#!/usr/bin/env python3
"""Announce upcoming talks on Bluesky, from the records in `_data/talks/*.toml`.

Two posts per talk, both automatic:

    announce   N days before the talk (`announce_days_before` in
               _data/social.toml), with a LinkedIn hand-off issue
    reminder   the morning of the talk, from `reminder_hour` on

Everything a post says comes from the talk record (title, speakers, time,
location, Zoom, the talk's own page), so it never disagrees with the website.
The speaker's own name links to their `website`, and their `bluesky` handle
(optional, per speaker) is tagged along with the handles in `[bluesky].mentions`.

What has been posted is recorded in `_data/social_posted.json`, outside the
talk TOML files because the calendar sync rewrites those. With --push-state
the "pending" marker is committed and pushed BEFORE posting, so a run that dies
after posting can never post the same talk twice; it fails loudly instead.

Usage:
    python3 scripts/post_bluesky.py --dry-run               # preview what is due now
    python3 scripts/post_bluesky.py --dry-run --now 2026-10-16T10:00-06:00
    python3 scripts/post_bluesky.py --dry-run --slug 2026-10-23-jane-doe --kind reminder
    python3 scripts/post_bluesky.py --push-state            # what the workflow runs

Needs BLUESKY_HANDLE and BLUESKY_APP_PASSWORD (an app password, never the
account password) in the environment unless --dry-run. Standard library only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
import tomllib
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import generate_talks as gt  # noqa: E402

ROOT = gt.ROOT
TZ = gt.TZ
CONFIG_PATH = os.path.join(ROOT, "_data", "social.toml")
STATE_PATH = os.path.join(ROOT, "_data", "social_posted.json")
STATE_REL = "_data/social_posted.json"

PDS = "https://bsky.social"
PUBLIC_API = "https://public.api.bsky.app"
POST_LIMIT = 300  # graphemes
SAFETY_MARGIN = 5  # our grapheme count is an approximation; stay clear of the edge
NEEDS_REVIEW_GRACE = dt.timedelta(days=2)

DEFAULT_CONFIG = {
    "bluesky": {
        "mentions": [],
        "hashtags": ["DataScience"],
        "announce_days_before": 7,
        "reminder_hour": 9,
    },
    "linkedin": {"notify": []},
}

LINK = "app.bsky.richtext.facet#link"
MENTION = "app.bsky.richtext.facet#mention"
TAG = "app.bsky.richtext.facet#tag"

Seg = tuple[str, "dict | None"]


class PostError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Config, talks, state
# --------------------------------------------------------------------------- #
def load_config(path: str = CONFIG_PATH) -> dict:
    cfg = {section: dict(values) for section, values in DEFAULT_CONFIG.items()}
    if os.path.exists(path):
        with open(path, "rb") as handle:
            loaded = tomllib.load(handle)
        for section, values in loaded.items():
            cfg.setdefault(section, {}).update(values)
    cfg["bluesky"]["mentions"] = [h for h in map(normalize_handle, cfg["bluesky"]["mentions"]) if h]
    return cfg


def normalize_handle(value: str) -> str:
    """'@a.bsky.social', 'https://bsky.app/profile/a.bsky.social', or a bare
    handle -> 'a.bsky.social' ('' if it does not look like a handle)."""
    value = (value or "").strip()
    match = re.search(r"bsky\.app/profile/([^/?#\s]+)", value)
    if match:
        value = match.group(1)
    value = value.lstrip("@").strip().lower()
    return value if re.fullmatch(r"([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z]([a-z0-9-]*[a-z0-9])?", value) else ""


def load_talks(data_dir: str = gt.DATA_DIR) -> list[dict]:
    talks = []
    for path in sorted(glob.glob(os.path.join(data_dir, "*.toml"))):
        if os.path.basename(path).startswith("_"):
            continue
        talk = gt.load_talk(path)
        with open(path, "rb") as handle:
            raw = tomllib.load(handle)
        talk["canceled"] = bool(raw.get("talk", {}).get("canceled", False))
        talk["needs_review"] = bool(raw.get("meta", {}).get("needs_review", False))
        talks.append(talk)
    talks.sort(key=lambda t: t["starts_at"])
    return talks


def load_state(path: str = STATE_PATH) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def save_state(state: dict, path: str = STATE_PATH) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


# --------------------------------------------------------------------------- #
# What is due
# --------------------------------------------------------------------------- #
def due_posts(talks: list[dict], state: dict, cfg: dict, now: dt.datetime) -> list[tuple[dict, str]]:
    """(talk, kind) pairs that should be posted at `now`. At most one per talk:
    on the day of the talk the reminder replaces a still-unsent announcement."""
    announce_lead = dt.timedelta(days=int(cfg["bluesky"]["announce_days_before"]))
    reminder_hour = int(cfg["bluesky"]["reminder_hour"])
    local_now = now.astimezone(TZ)
    due = []
    for talk in talks:
        start = talk["starts_at"]
        if talk["canceled"] or now >= start:
            continue
        # a record the calendar could not fully read: give a human time to fix
        # it, but do not stay silent right before the talk
        if talk["needs_review"] and start - now > NEEDS_REVIEW_GRACE:
            continue
        done = state.get(talk["slug"], {})
        if local_now.date() == start.date():
            # the day itself is the reminder's alone, even if the announcement
            # never went out, so the two never land back to back
            if local_now.hour >= reminder_hour and "reminder" not in done:
                due.append((talk, "reminder"))
        elif now >= start - announce_lead and "announce" not in done:
            due.append((talk, "announce"))
    return due


# --------------------------------------------------------------------------- #
# Text: segments -> (text, facets)
# --------------------------------------------------------------------------- #
def grapheme_len(text: str) -> int:
    """Approximate grapheme-cluster count (what Bluesky's 300 limit counts):
    combining marks, variation selectors, skin tones and ZWJ sequences extend
    the previous character; regional indicators pair up into one flag."""
    count = 0
    after_joiner = False
    open_flag = False
    for ch in text:
        code = ord(ch)
        if after_joiner:
            after_joiner = False
            continue
        if ch == "‍":
            after_joiner = True
            continue
        if unicodedata.category(ch) in ("Mn", "Me", "Mc") or 0x1F3FB <= code <= 0x1F3FF:
            continue
        if 0x1F1E6 <= code <= 0x1F1FF:
            if open_flag:
                open_flag = False
                continue
            open_flag = True
        else:
            open_flag = False
        count += 1
    return count


def build(lines: list[list[Seg]]) -> tuple[str, list[dict]]:
    """Join lines of (text, feature) segments; facet offsets are UTF-8 bytes."""
    text = ""
    facets = []
    for number, line in enumerate(lines):
        if number:
            text += "\n"
        for piece, feature in line:
            start = len(text.encode("utf-8"))
            text += piece
            if feature:
                facets.append(
                    {
                        "index": {"byteStart": start, "byteEnd": len(text.encode("utf-8"))},
                        "features": [feature],
                    }
                )
    return text, facets


def time_range(talk: dict) -> str:
    start, end = talk["starts_at"], talk["ends_at"]
    if not end:
        return f"{start:%-I:%M %p} MT"
    if start.strftime("%p") == end.strftime("%p"):
        return f"{start:%-I:%M}–{end:%-I:%M %p} MT"
    return f"{start:%-I:%M %p}–{end:%-I:%M %p} MT"


def talk_url(talk: dict) -> str:
    return f"{gt.site_url()}/talks/{talk['slug']}/"


def speaker_handles(talk: dict) -> list[str]:
    return [h for h in (normalize_handle(s.get("bluesky", "")) for s in talk["speakers"]) if h]


def speaker_line(talk: dict, with_affiliation: bool) -> list[Seg] | None:
    speakers = talk["speakers"]
    if not speakers:
        return None
    line: list[Seg] = [("🎤 ", None)]
    for number, speaker in enumerate(speakers):
        if number:
            line.append((" & ", None))
        site = (speaker.get("website") or "").strip()
        line.append((speaker["name"], {"$type": LINK, "uri": site} if site.startswith("http") else None))
    affiliation = (speakers[0].get("affiliation") or "").strip()
    if with_affiliation and affiliation:
        line.append((f" ({affiliation})", None))
    return line


def base_lines(talk: dict, kind: str, level: int, title: str, hashtags: list[str], cc: list[tuple[str, str]]) -> list[list[Seg]]:
    """Level 0 is the full post; each higher level drops something: 1 the
    hashtags, 2 the affiliation, 3 the Zoom note, (4 shortens the title)."""
    start = talk["starts_at"]
    if kind == "reminder":
        head = f"⏰ Today, {start:%-I:%M %p} MT: “{title}”"
    else:
        head = f"📣 Next talk: “{title}”"
    lines: list[list[Seg]] = [[(head, None)]]
    spk = speaker_line(talk, with_affiliation=level < 2)
    if spk:
        lines.append(spk)
    if kind == "announce":
        lines.append([(f"🗓 {start:%a, %b %-d} · {time_range(talk)}", None)])
    where = (talk["front"].get("location") or "").strip()
    if talk["front"].get("zoom") and level < 3:
        where = f"{where} · Zoom" if where else "Zoom"
    if where:
        lines.append([(f"📍 {where}", None)])
    url = talk_url(talk)
    lines.append([(re.sub(r"^https?://", "", url), {"$type": LINK, "uri": url})])
    if hashtags and level < 1:
        tags: list[Seg] = []
        for tag in hashtags:
            tags += [(f"#{tag}", {"$type": TAG, "tag": tag}), (" ", None)]
        lines.append(tags[:-1])
    if cc:
        lines.append(cc_line(cc))
    return lines


def cc_line(cc: list[tuple[str, str]]) -> list[Seg]:
    line: list[Seg] = [("cc ", None)]
    for number, (handle, did) in enumerate(cc):
        if number:
            line.append((" ", None))
        line.append((f"@{handle}", {"$type": MENTION, "did": did}))
    return line


def fits(lines: list[list[Seg]]) -> bool:
    text, _ = build(lines)
    return grapheme_len(text) <= POST_LIMIT - SAFETY_MARGIN


def compose(talk: dict, kind: str, cfg: dict, dids: dict[str, str]) -> list[dict]:
    """The posts to publish for one talk: the main post, plus an optional reply
    holding any mentions that did not fit. Each is {"text", "facets", "embed"?}.
    `dids` maps handle -> DID for every handle that resolved; others are skipped."""
    hashtags = list(cfg["bluesky"]["hashtags"])
    wanted = speaker_handles(talk) + [h for h in cfg["bluesky"]["mentions"] if h not in speaker_handles(talk)]
    resolved = [(h, dids[h]) for h in wanted if h in dids]
    first = [(h, d) for h, d in resolved if h in speaker_handles(talk)]  # the speaker always makes the main post
    rest = [(h, d) for h, d in resolved if h not in speaker_handles(talk)]

    title = " ".join(talk["front"]["title"].split())
    chosen = None
    for level in range(4):
        lines = base_lines(talk, kind, level, title, hashtags, first)
        if fits(lines):
            chosen = (level, title)
            break
    if chosen is None:
        level = 3
        shortened = title
        while len(shortened) > 20:
            shortened = shortened[: len(shortened) - 8].rstrip() + "…"
            if fits(base_lines(talk, kind, level, shortened, hashtags, first)):
                chosen = (level, shortened)
                break
    if chosen is None:
        raise PostError(f"{talk['slug']}: cannot fit the post in {POST_LIMIT} graphemes")
    level, title = chosen

    cc = list(first)
    overflow = []
    for pair in rest:
        if fits(base_lines(talk, kind, level, title, hashtags, cc + [pair])):
            cc.append(pair)
        else:
            overflow.append(pair)
    text, facets = build(base_lines(talk, kind, level, title, hashtags, cc))
    summary = ", ".join(s["name"] for s in talk["speakers"])
    description = f"{summary} · {talk['starts_at']:%a, %b %-d}, {time_range(talk)}".strip(" ·")
    posts = [
        {
            "text": text,
            "facets": facets,
            "embed": {
                "$type": "app.bsky.embed.external",
                "external": {"uri": talk_url(talk), "title": talk["front"]["title"][:300], "description": description[:1000]},
            },
        }
    ]
    if overflow:
        chunk: list[tuple[str, str]] = []
        for pair in overflow:
            candidate = build([[("With ", None)] + cc_line(chunk + [pair])[1:]])[0]
            if grapheme_len(candidate) > POST_LIMIT - SAFETY_MARGIN:
                break
            chunk.append(pair)
        if len(chunk) < len(overflow):
            print(f"warning: {len(overflow) - len(chunk)} mention(s) did not fit even in the reply and were dropped")
        if chunk:
            rtext, rfacets = build([[("With ", None)] + cc_line(chunk)[1:]])
            posts.append({"text": rtext, "facets": rfacets})
    return posts


def linkedin_text(talk: dict) -> str:
    start = talk["starts_at"]
    names = " & ".join(s["name"] for s in talk["speakers"]) or "our next speaker"
    affiliation = (talk["speakers"][0].get("affiliation") or "").strip() if talk["speakers"] else ""
    lines = [f"📣 Join us on {start:%A, %B %-d} at {time_range(talk)} for the next talk in the {talk['front'].get('series') or 'Data Science & AI Lecture Series'} at the University of Utah:", ""]
    lines.append(f"“{talk['front']['title']}”")
    lines.append(f"{names}{f' ({affiliation})' if affiliation else ''}")
    lines.append("")
    abstract = " ".join(talk["body"].split())
    if abstract:
        lines += [abstract if len(abstract) <= 500 else abstract[:497].rsplit(" ", 1)[0] + "…", ""]
    where = (talk["front"].get("location") or "").strip()
    if where:
        lines.append(f"📍 {where}" + (" (Zoom available)" if talk["front"].get("zoom") else ""))
    lines.append(f"🔗 {talk_url(talk)}")
    site = next((s.get("website") for s in talk["speakers"] if s.get("website")), "")
    if site:
        lines.append(f"👤 {site}")
    lines += ["", "#DataScience #UniversityOfUtah"]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Bluesky + GitHub
# --------------------------------------------------------------------------- #
def http_json(method: str, url: str, payload: dict | None = None, token: str | None = None, retries: int = 0) -> dict:
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(retries + 1):
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", "replace")[:300]
            if error.code >= 500 and attempt < retries:
                continue
            raise PostError(f"{method} {urllib.parse.urlsplit(url).path}: HTTP {error.code} {body}") from error
        except urllib.error.URLError as error:
            if attempt < retries:
                continue
            raise PostError(f"{method} {urllib.parse.urlsplit(url).path}: {error.reason}") from error
    raise PostError("unreachable")


def resolve_handle(handle: str) -> str:
    query = urllib.parse.urlencode({"handle": handle})
    return http_json("GET", f"{PUBLIC_API}/xrpc/com.atproto.identity.resolveHandle?{query}", retries=1)["did"]


def resolve_all(handles: list[str], resolver=resolve_handle) -> dict[str, str]:
    dids = {}
    for handle in dict.fromkeys(handles):
        try:
            dids[handle] = resolver(handle)
        except (PostError, KeyError) as error:
            print(f"warning: skipping @{handle}, could not resolve it ({error})")
    return dids


class Session:
    def __init__(self, handle: str, password: str):
        reply = http_json("POST", f"{PDS}/xrpc/com.atproto.server.createSession", {"identifier": handle, "password": password}, retries=1)
        self.did, self.token = reply["did"], reply["accessJwt"]

    def post(self, post: dict, reply_to: dict | None = None) -> dict:
        record = {
            "$type": "app.bsky.feed.post",
            "text": post["text"],
            "facets": post["facets"],
            "langs": ["en"],
            "createdAt": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        }
        if post.get("embed"):
            record["embed"] = post["embed"]
        if reply_to:
            record["reply"] = reply_to
        # no retry: a repeated createRecord after a timeout could post twice
        return http_json(
            "POST",
            f"{PDS}/xrpc/com.atproto.repo.createRecord",
            {"repo": self.did, "collection": "app.bsky.feed.post", "record": record},
            token=self.token,
        )


def git(*args: str) -> None:
    subprocess.run(["git", *args], cwd=ROOT, check=True)


def commit_state(message: str) -> None:
    """Commit the state file and push it to master, rebasing over any
    concurrent push (the calendar sync commits there too)."""
    git("add", STATE_REL)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
        return
    git("commit", "-m", f"{message} [skip ci]")
    for attempt in range(1, 4):
        if subprocess.run(["git", "push", "origin", "HEAD:master"], cwd=ROOT).returncode == 0:
            return
        print(f"Push rejected (attempt {attempt}); rebasing onto the latest master.")
        git("pull", "--rebase", "origin", "master")
    raise PostError("could not push the post record to master")


def open_linkedin_issue(talk: dict, cfg: dict) -> str:
    notify = [u.lstrip("@") for u in cfg["linkedin"]["notify"]]
    pings = " ".join(f"@{u}" for u in notify)
    body = (
        f"{pings}\n\n" if pings else ""
    ) + (
        "The Bluesky announcement for this talk is out. Please post the text below on the group's LinkedIn page "
        "(or your own), then close this issue.\n\n"
        f"```text\n{linkedin_text(talk)}\n```\n"
    )
    title = f"LinkedIn post: {talk['front']['title']} ({talk['starts_at']:%b %-d})"
    subprocess.run(["gh", "label", "create", "social", "--color", "0A66C2", "--description", "Social media posts", "--force"], cwd=ROOT, capture_output=True)
    result = subprocess.run(["gh", "issue", "create", "--title", title, "--body", body, "--label", "social"], cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise PostError(f"could not open the LinkedIn issue: {result.stderr.strip()[:300]}")
    return result.stdout.strip()


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def preview(talk: dict, kind: str, posts: list[dict]) -> None:
    print(f"\n=== {kind.upper()}: {talk['slug']} ({talk['starts_at']:%Y-%m-%d %H:%M %Z}) ===")
    for number, post in enumerate(posts):
        label = "post" if number == 0 else "reply"
        print(f"--- {label} ({grapheme_len(post['text'])}/{POST_LIMIT} graphemes, {len(post['facets'])} facets)")
        print(post["text"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="print what would be posted; post and write nothing")
    parser.add_argument("--now", help="pretend it is this ISO time (default: now)")
    parser.add_argument("--slug", help="post about this talk regardless of timing")
    parser.add_argument("--kind", choices=("announce", "reminder"), default="announce", help="with --slug (default: announce)")
    parser.add_argument("--force", action="store_true", help="with --slug, post even if already recorded as posted")
    parser.add_argument("--push-state", action="store_true", help="commit and push the post record to master (the workflow uses this)")
    parser.add_argument("--no-linkedin", action="store_true", help="do not open the LinkedIn issue")
    args = parser.parse_args()

    now = dt.datetime.fromisoformat(args.now) if args.now else dt.datetime.now(TZ)
    if now.tzinfo is None:
        now = now.replace(tzinfo=TZ)
    cfg = load_config()
    talks = load_talks()
    state = load_state()

    stale = [f"{slug}/{kind}" for slug, kinds in state.items() for kind, entry in kinds.items() if entry.get("status") == "pending"]
    if stale:
        print(f"::error::Possibly posted but never recorded: {', '.join(stale)}. Check the Bluesky account, then fix {STATE_REL}.")
        return 1

    if args.slug:
        found = [t for t in talks if t["slug"] == args.slug]
        if not found:
            print(f"::error::No talk with slug {args.slug!r}")
            return 1
        if state.get(args.slug, {}).get(args.kind) and not args.force:
            print(f"{args.slug} already has a {args.kind} post recorded; use --force to post again.")
            return 0
        due = [(found[0], args.kind)]
    else:
        due = due_posts(talks, state, cfg, now)
    if not due:
        print(f"Nothing to post at {now:%Y-%m-%d %H:%M %Z}.")
        return 0

    handles = list(cfg["bluesky"]["mentions"])
    for talk, _ in due:
        handles += speaker_handles(talk)
    dids = resolve_all(handles)

    session = None
    if not args.dry_run:
        handle, password = os.environ.get("BLUESKY_HANDLE"), os.environ.get("BLUESKY_APP_PASSWORD")
        if not handle or not password:
            print("::error::BLUESKY_HANDLE and BLUESKY_APP_PASSWORD must be set.")
            return 1
        session = Session(handle, password)

    failed = False
    for talk, kind in due:
        try:
            posts = compose(talk, kind, cfg, dids)
        except PostError as error:
            print(f"::error::{error}")
            failed = True
            continue
        preview(talk, kind, posts)
        if args.dry_run:
            continue

        entry = state.setdefault(talk["slug"], {})
        entry[kind] = {"status": "pending", "at": now.isoformat(timespec="seconds")}
        save_state(state)
        if args.push_state:
            commit_state(f"Posting Bluesky {kind} for {talk['slug']}")  # raises, and nothing is posted, if this fails
        root = session.post(posts[0])
        parent = {"uri": root["uri"], "cid": root["cid"]}
        for extra in posts[1:]:
            parent = (lambda r: {"uri": r["uri"], "cid": r["cid"]})(session.post(extra, {"root": {"uri": root["uri"], "cid": root["cid"]}, "parent": parent}))
        entry[kind] = {"status": "posted", "uri": root["uri"], "at": now.isoformat(timespec="seconds")}
        save_state(state)
        print(f"Posted: {root['uri']}")
        if kind == "announce" and not args.no_linkedin:
            try:
                entry[kind]["linkedin_issue"] = open_linkedin_issue(talk, cfg)
                print(f"Opened {entry[kind]['linkedin_issue']}")
            except PostError as error:
                print(f"::warning::{error}")
            save_state(state)
        if args.push_state:
            commit_state(f"Record Bluesky {kind} for {talk['slug']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
