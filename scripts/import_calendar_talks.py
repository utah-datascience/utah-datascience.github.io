#!/usr/bin/env python3
"""Sync talk records in `_data/talks/` from the seminar's Google Calendar.

Google Calendar is the source of truth for any talk happening soon; this
script is what keeps `_data/talks/*.toml` in step with it. Two modes:

    python3 scripts/import_calendar_talks.py --sync
        The daily sync. Talks starting within --window-days (default 90) are
        created, updated, or (if removed from the calendar) deleted to match
        it. Talks outside the window are left alone -- past talks and
        anything far out are owned by the repo, not the calendar. See
        `parse_markdown_sections` for the structured description format this
        expects, and the README for a pasteable template.

    python3 scripts/import_calendar_talks.py
        One-off seeding, for backfilling history: writes a new TOML file for
        every calendar entry that does not already have one, using best-effort
        heuristics for calendar entries that predate the structured format.
        Never updates or deletes an existing file unless --overwrite is given.

Usage:
    python3 scripts/import_calendar_talks.py --sync                    # daily sync
    python3 scripts/import_calendar_talks.py --sync --dry-run          # preview it
    python3 scripts/import_calendar_talks.py --sync --window-days 30
    python3 scripts/import_calendar_talks.py                           # one-off seeding
    python3 scripts/import_calendar_talks.py --overwrite               # also rewrite existing files
    python3 scripts/import_calendar_talks.py --ics cal.ics             # use a local .ics file
    python3 scripts/import_calendar_talks.py --since 2025-01-01
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import html
import os
import re
import sys
import tomllib
import unicodedata
import urllib.request
from zoneinfo import ZoneInfo

CALENDAR_ID = "ekol7ulqm14nv155angut2rlfo@group.calendar.google.com"
ICS_URL = (
    "https://calendar.google.com/calendar/ical/"
    + CALENDAR_ID.replace("@", "%40")
    + "/public/basic.ics"
)
TZ = ZoneInfo("America/Denver")
WINDOW_DAYS_DEFAULT = 90

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "_data", "talks")

# Talk-level fields the calendar never supplies -- carried over from whatever
# is already on disk, verbatim, every sync.
PRESERVE_ONLY_FIELDS = ("paper", "slug")

# Boilerplate that shows up in the calendar summaries and is not part of a title.
SERIES_NOISE = [
    "Utah Center for Data Science Seminar",
    "Data Science & AI Lecture Series",
    "Data Science and AI Lecture Series",
    "Data Science Lecture Series",
    "UCDS+AI Lecture Series",
    "UCDS Lecture Series",
    "UCDS+AI Seminar",
    "UCDS + AI Seminar",
    "Data Science and AI Seminar",
    "Data Science & AI Seminar",
    "Data Science Seminar",
    "Data Seminar",
    "UCDS Seminar",
]

# summaries sometimes name the series (or an event) where a speaker should be
NOT_A_PERSON_RE = re.compile(
    r"(?i)^(?:the\s+)?(?:utah\s+center\s+for\s+)?data\s+science\b|"
    r"lecture\s+series|\bseminars?\b|information\s+session|\borientation\b|"
    r"^speakers?$|\b(?:data\s+science|ai)\s*(?:\+\s*ai\s*)?day\b|"
    r"^(?:spring|summer|fall|winter)\s*'?\d*$",
)

CANCELED_RE = re.compile(r"\[?\b(cancell?ed|postponed)\b\]?", re.I)
SKIP_SUMMARY_RE = re.compile(
    r"^\s*(no (seminar|talk|lecture)|tba|tbd|holiday|spring break|fall break|"
    r"reserved|placeholder|hold\b|organizational|planning meeting|"
    r"(ucds\+?a?i? ?)?(seminar |lecture series )?(kick ?off|welcome|social|lunch|"
    r"open (house|discussion)))",
    re.I,
)


# --------------------------------------------------------------------------- #
# ICS parsing
# --------------------------------------------------------------------------- #
def unfold(text: str) -> str:
    return re.sub(r"\r?\n[ \t]", "", text.replace("\r\n", "\n"))


def unescape_ics(value: str) -> str:
    return (
        value.replace("\\n", "\n")
        .replace("\\N", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
    )


def parse_events(ics_text: str) -> list[dict]:
    events = []
    for block in re.findall(r"BEGIN:VEVENT\n(.*?)\nEND:VEVENT", unfold(ics_text), re.S):
        event = {}
        for line in block.split("\n"):
            m = re.match(r"^([A-Z-]+)((?:;[^:]*)?):(.*)$", line)
            if not m:
                continue
            key, params, value = m.group(1), m.group(2), m.group(3)
            event.setdefault(key, (params, unescape_ics(value)))
        events.append(event)
    return events


def get(event: dict, key: str) -> str:
    return event.get(key, ("", ""))[1]


def event_uid(event: dict) -> str:
    """This calendar reuses one UID across every occurrence of a recurring
    slot, distinguishing them with RECURRENCE-ID -- so that pair, not the bare
    UID, is what uniquely identifies a specific talk."""
    uid = get(event, "UID")
    rid = get(event, "RECURRENCE-ID")
    return f"{uid}::{rid}" if rid else uid


def parse_dt(event: dict, key: str) -> dt.datetime | None:
    if key not in event:
        return None
    params, value = event[key]
    if value.endswith("Z"):
        stamp = dt.datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(
            tzinfo=dt.timezone.utc
        )
        return stamp.astimezone(TZ)
    tzid = re.search(r"TZID=([^;:]+)", params)
    tz = ZoneInfo(tzid.group(1)) if tzid else TZ
    if "T" in value:
        return dt.datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=tz)
    return dt.datetime.strptime(value, "%Y%m%d").replace(tzinfo=tz)


# --------------------------------------------------------------------------- #
# Field extraction
# --------------------------------------------------------------------------- #
def html_to_text(raw: str) -> str:
    text = re.sub(r"(?i)<br\s*/?>", "\n", raw)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = re.sub(r'(?i)<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"\2 (\1)", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\xa0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Google Meet boilerplate appended by Calendar
    text = re.split(r"\n-::~:~::.*", text)[0]
    text = re.split(r"\nJoin with Google Meet:", text)[0]
    text = re.split(r"\nLearn more about Meet at:", text)[0]
    return text.strip()


def find_links(text: str) -> list[str]:
    links = re.findall(r"https?://[^\s<>\"')\]]+", text)
    return [link.rstrip(".,;)") for link in links]


def classify_links(links: list[str]) -> dict:
    out = {"zoom": "", "recording": "", "slides": "", "website": ""}
    for link in links:
        low = link.lower()
        if ("zoom.us" in low or "meet.google" in low) and not out["zoom"]:
            out["zoom"] = link
        elif ("youtube.com" in low or "youtu.be" in low) and not out["recording"]:
            out["recording"] = link
        elif re.search(r"(slides|\.pdf$|\.pptx?$|speakerdeck|slideshare)", low) and not out["slides"]:
            out["slides"] = link
        elif not re.search(r"(zoom\.us|meet\.google|youtube|youtu\.be|calendar\.google|"
                           r"support\.google|mailman|utah\.zoom|map\.utah\.edu|"
                           r"maps\.google|goo\.gl/maps|/map)", low) and not out["website"]:
            out["website"] = link
    return out


# --------------------------------------------------------------------------- #
# Structured (Markdown-header) description format
# --------------------------------------------------------------------------- #
# The organizer-facing format this sync expects in the calendar description:
# level 1-6 Markdown headers name a field, and everything up to the next
# header is that field's value. A header must have nothing else on its line,
# but is otherwise forgiving of case and whitespace -- "## Title", "##title",
# and "###   Title   :" all work. See README for the pasteable template.
MD_HEADER_RE = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]*(?P<label>[^\n]+?)[ \t]*:?[ \t]*$", re.M)

# label (normalized: lowercased, whitespace-collapsed) -> canonical field name
TALK_LABEL_ALIASES = {
    "title": "title",
    "talk title": "title",
    "abstract": "abstract",
    "summary": "abstract",
    "tags": "tags",
    "topics": "tags",
    "keywords": "tags",
    "location": "location",
    "room": "location",
    "venue": "location",
    "zoom": "zoom",
    "meeting link": "zoom",
    "meeting": "zoom",
    "slides": "slides",
    "recording": "recording",
    "video": "recording",
    "series": "series",
}
SPEAKER_LABEL_ALIASES = {
    "affiliation": "affiliation",
    "institution": "affiliation",
    "department": "affiliation",
    "website": "website",
    "url": "website",
    "homepage": "website",
    "link": "website",
    "bio": "bio",
    "biography": "bio",
    "about the speaker": "bio",
    "speaker bio": "bio",
    "email": "email",
    "role": "role",
    "position": "role",
}


def normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", label).strip().lower()


def parse_markdown_sections(text: str) -> tuple[dict, list[dict], list[str]]:
    """Split a structured calendar description into talk fields and speakers.

    Returns (talk_fields, speakers, unknown_labels). An empty `speakers` means
    the text was not written in this format at all -- the caller should fall
    back to the free-form heuristics used for older calendar entries.
    """
    matches = list(MD_HEADER_RE.finditer(text))
    talk_fields: dict = {}
    speakers: list[dict] = []
    lead_speaker_fields: dict = {}
    unknown: list[str] = []
    current: dict | None = None

    for i, match in enumerate(matches):
        label = normalize_label(match.group("label"))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if not body:
            continue
        if label in ("speaker", "presenter"):
            current = {"name": body.split("\n")[0].strip()}
            speakers.append(current)
            continue
        canon = SPEAKER_LABEL_ALIASES.get(label)
        if canon:
            (current if current is not None else lead_speaker_fields)[canon] = body
            continue
        canon = TALK_LABEL_ALIASES.get(label)
        if canon == "tags":
            talk_fields[canon] = [t.strip() for t in body.split(",") if t.strip()]
        elif canon:
            talk_fields[canon] = body
        else:
            unknown.append(match.group("label").strip())

    if not speakers and lead_speaker_fields:
        # Fields typed before any "## Speaker" header, and there never was
        # one -- a single speaker, named from the calendar summary instead.
        speakers = [dict(lead_speaker_fields)]
    elif lead_speaker_fields and speakers:
        # Fields typed before the first "## Speaker" header attach to it.
        merged = dict(lead_speaker_fields)
        merged.update(speakers[0])
        speakers[0] = merged

    return talk_fields, speakers, unknown


def infer_series(summary: str, start: dt.datetime) -> str:
    return (
        "Data Science & AI Lecture Series"
        if re.search(r"(?i)ucds\+ai|lecture series", summary) or start.year >= 2025
        else "Data Science Seminar"
    )


def format_last_modified(value: str) -> str:
    """LAST-MODIFIED as GitHub-Actions-run-agnostic ISO 8601, for the [meta]
    block -- this is what a later sync compares to skip an unchanged event."""
    if not value:
        return ""
    try:
        stamp = dt.datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return value
    return stamp.isoformat().replace("+00:00", "Z")


BOILERPLATE_LINE_RE = re.compile(
    r"^(?:the\s+)?(?:utah\s+center\s+for\s+)?data\s+science(?:\s*(?:&|and)\s*ai)?"
    r"\s*(?:seminar|lecture series)?\s*$|"
    r"^(?:ucds|ucds\+ai)\b.*$|"
    r"^join zoom meeting$|^meeting id\b|^passcode\b|^one tap mobile$|"
    r"^zoom\s*(link|info)\b|^talks? will be held\b|.*streamed via the following.*|"
    r"^\(?https?://\S+.*$|.*\bzoom\b[^\n]*https?://.*|"
    r"^dial by your location$|^\+?\d[\d\s().,*#+-]{6,}$|^find your local number|"
    r"^join by (?:sip|h\.?323)$|^\d{3} \d{4} \d{4}$|^[\s.*#-]+$|"
    r"^time:\s.*(?:mountain time|am|pm)\b.*$|"
    r"^in person\b.*$|^zoom\b\s*:?\s*$|^https?://\S+$|^[\s.*#-]*$",
    re.I,
)


def strip_boilerplate(text: str) -> str:
    # blank lines are kept: they are what separates title / speaker / abstract blocks
    kept = [
        line
        for line in text.split("\n")
        if not line.strip() or not BOILERPLATE_LINE_RE.match(line.strip())
    ]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def looks_like_title(text: str) -> bool:
    if not 8 < len(text) <= 250:
        return False
    if looks_like_person(text.split("\n")[0]):
        return False
    return not re.match(r"(?i)^(abstract|bio|speaker|zoom|title)\b\s*:?$", text)


def split_sections(text: str) -> dict:
    """Pull Title / Abstract / Bio blocks out of a free-form description."""
    labels = {
        "title": r"(?:talk\s+)?title",
        "abstract": r"abstract|summary",
        "bio": r"bio(?:graphy|sketch)?|about the speaker|speaker bio",
        "speaker": r"speaker|presenter",
    }
    pattern = re.compile(
        r"^\s*(?P<label>" + "|".join(labels.values()) + r")\s*:\s*",
        re.I | re.M,
    )
    matches = list(pattern.finditer(text))
    sections: dict[str, str] = {}
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        label = match.group("label").lower()
        for name, expr in labels.items():
            if re.fullmatch(expr, label, re.I):
                sections.setdefault(name, body)
                break
    return sections


def clean_summary(summary: str) -> str:
    text = CANCELED_RE.sub("", summary)
    for noise in SERIES_NOISE:
        text = re.sub(re.escape(noise), "|", text, flags=re.I)
    text = re.sub(r"\s*[-–—]{2,}\s*", "|", text)
    text = re.sub(r"\s+[-–—]\s+", "|", text)
    # "Data Science Lecture Series. Speaker: Mihai Budiu, Feldera"
    text = re.sub(r"(?i)(?:^|\|)\s*\.?\s*(?:speakers?|presenters?)\s*:\s*", "|", text)
    text = re.sub(r"\s+@\s+", "|", text)
    parts = [p.strip(" .-–—:|@\t") for p in text.split("|")]
    return "|".join(p for p in parts if p)


def split_speaker_and_title(summary: str) -> tuple[str, str]:
    """Best-effort split of a calendar summary into (speaker, title)."""
    parts = [p for p in clean_summary(summary).split("|") if p]
    if not parts:
        return "", ""
    if len(parts) == 1:
        head = parts[0]
        m = re.match(r"^(?P<speaker>[^:]{3,60}?)\s*:\s*(?P<title>.+)$", head)
        if m and looks_like_person(m.group("speaker")):
            return clean_name(m.group("speaker")), clean_title(m.group("title"))
        return (clean_name(head), "") if looks_like_person(head) else ("", clean_title(head))
    # first part that looks like a person is the speaker; longest remainder the title
    speaker = ""
    rest = []
    for part in parts:
        if not speaker and looks_like_person(part):
            speaker = part
        else:
            rest.append(part)
    title = max(rest, key=len) if rest else ""
    if not speaker:
        speaker, title = parts[0], max(parts[1:], key=len) if len(parts) > 1 else ""
    if ":" in speaker and not title:
        speaker, title = speaker.split(":", 1)
    return clean_name(speaker), clean_title(title)


CONNECTOR_WORDS = {"and", "de", "del", "der", "van", "von", "la", "bin", "y"}


def looks_like_person(text: str) -> bool:
    core = re.sub(r"\(.*?\)", "", text).strip()
    if not core or len(core) > 60:
        return False
    if re.search(r"[:;]|\d", core):  # "Data Visualization 101" is a title, not a name
        return False
    words = core.split()
    if not 1 < len(words) <= 6:
        return False
    return all(
        w[0].isupper() or not w[0].isalpha() or w.lower() in CONNECTOR_WORDS for w in words
    )


def split_name_affiliation(text: str) -> tuple[str, str]:
    text = text.strip()
    text = re.sub(r"\(?\s*https?://\S+\)?", " ", text).strip()
    # "Jie (Claire) Zhang" -- a nickname rather than an affiliation
    text = re.sub(r"^([^(]+)\(([^)]*)\)\s+(?=\S)", r"\1 ", text).strip()
    if "(" in text and ")" not in text:  # unbalanced, e.g. "Jie Zhang (U Washington"
        name, affil = text.split("(", 1)
        return clean_name(name), clean_affiliation(affil)
    m = re.match(r"^(?P<name>[^(]+)\((?P<affil>[^)]*)\)", text)
    if m:
        return clean_name(m.group("name")), clean_affiliation(m.group("affil"))
    if "," in text and len(text.split(",")) == 2:
        name, affil = text.split(",")
        return clean_name(name), clean_affiliation(affil)
    return clean_name(text), ""


def clean_name(text: str) -> str:
    text = re.sub(r"\(?\s*https?://\S+\)?", " ", text)  # links pulled out of the HTML
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ,;:.-()[]|")


def clean_affiliation(text: str) -> str:
    affil = re.sub(r"\s+", " ", text.split("\n")[0]).strip(" ,;:-()[]|")
    # anything this long is a mis-parse (usually an abstract that ran together)
    return "" if len(affil) > 120 else affil



def clean_title(text: str) -> str:
    # "Title: TBA" followed by "Topic: <something>" is a common calendar shape
    lines = [
        re.sub(r"(?i)^(?:talk\s+)?(?:title|topic)\s*:\s*", "", line).strip()
        for line in text.split("\n")
    ]
    lines = [line for line in lines if line and not re.fullmatch(r"(?i)tba|tbd", line)]
    if not lines:
        return ""
    text = "\n".join(lines)
    title = lines[0] if len(lines[0]) > 15 else text.replace("\n", " ")
    title = re.split(r"(?i)(?:abstract|bio(?:graphy)?)\s*:", title)[0]
    title = re.sub(r"\s+", " ", title).strip(" .,;:-\u2013\u2014()[]")
    if re.fullmatch(r"(?i)tba|tbd|", title) or len(title) < 6:
        return ""
    if not re.search(r"[A-Za-z]{3,}", title):
        return ""
    return title[:250].strip()


def clean_block(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def matches_name(line: str, name: str) -> bool:
    line_words = set(re.findall(r"[A-Za-z]{3,}", line.lower()))
    name_words = set(re.findall(r"[A-Za-z]{3,}", name.lower()))
    return bool(name_words) and len(name_words & line_words) >= min(2, len(name_words))


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return re.sub(r"-{2,}", "-", text)


# --------------------------------------------------------------------------- #
# TOML writing
# --------------------------------------------------------------------------- #
def toml_str(value: str) -> str:
    if "\n" in value:
        body = value.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
        return '"""\n' + body + '\n"""'
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_toml(talk: dict) -> str:
    needs_review = bool(talk.get("needs_review", True))
    banner = (
        "# Imported from the seminar Google Calendar -- please review and complete."
        if needs_review
        else "# Synced from the seminar Google Calendar -- edits here are overwritten"
             "\n# while this talk is inside the sync window. See README.md#talks."
    )
    lines = [
        banner,
        "",
        "[talk]",
        f'title = {toml_str(talk["title"])}',
        f'date = {talk["date"]}',
        f'start_time = "{talk["start_time"]}"',
        f'end_time = "{talk["end_time"]}"',
        f'series = {toml_str(talk["series"])}',
        f'location = {toml_str(talk["location"])}',
        f'zoom = {toml_str(talk["zoom"])}',
        f'slides = {toml_str(talk["slides"])}',
        f'recording = {toml_str(talk["recording"])}',
        f'paper = {toml_str(talk.get("paper", ""))}',
        "tags = [" + ", ".join(toml_str(tag) for tag in talk.get("tags") or []) + "]",
        f'canceled = {"true" if talk["canceled"] else "false"}',
    ]
    if talk.get("slug"):
        lines.append(f'slug = {toml_str(talk["slug"])}')
    lines += [
        f'abstract = {toml_str(talk["abstract"])}',
        "",
    ]
    for speaker in talk["speakers"]:
        lines += [
            "[[speakers]]",
            f'name = {toml_str(speaker["name"])}',
            f'affiliation = {toml_str(speaker.get("affiliation", ""))}',
            f'role = {toml_str(speaker.get("role", ""))}',
            f'website = {toml_str(speaker.get("website", ""))}',
            f'photo = {toml_str(speaker.get("photo", ""))}',
            f'email = {toml_str(speaker.get("email", ""))}',
            f'bio = {toml_str(speaker.get("bio", ""))}',
            "",
        ]
    lines += [
        "[meta]",
        'source = "google-calendar"',
        f'calendar_uid = {toml_str(talk["uid"])}',
    ]
    last_modified = format_last_modified(talk.get("last_modified", ""))
    if last_modified:
        lines.append(f'calendar_last_modified = {toml_str(last_modified)}')
    lines.append(f'synced_on = {dt.date.today().isoformat()}')
    lines.append(f'needs_review = {"true" if needs_review else "false"}')
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Loading and merging existing records
# --------------------------------------------------------------------------- #
def load_records(data_dir: str) -> dict[str, dict]:
    """{calendar_uid: {"path", "talk", "speakers"}} for every existing record
    that has a calendar_uid. Records without one (hand-written, or from before
    this sync existed) are invisible to it -- and so left untouched."""
    records: dict[str, dict] = {}
    for path in sorted(glob.glob(os.path.join(data_dir, "*.toml"))):
        if os.path.basename(path).startswith("_"):
            continue
        with open(path, "rb") as handle:
            try:
                raw = tomllib.load(handle)
            except tomllib.TOMLDecodeError as error:
                print(
                    f"warning: {os.path.relpath(path, ROOT)} is not valid TOML ({error}) "
                    "-- the sync cannot see this record and will not touch it, which can "
                    "leave a stale duplicate behind if the calendar has since renamed it",
                    file=sys.stderr,
                )
                continue
        uid = raw.get("meta", {}).get("calendar_uid")
        if uid:
            records[uid] = {"path": path, "raw": raw}
    return records


def prefer(incoming, existing):
    """The merge rule, uniformly: whatever the calendar supplies this sync
    wins; whatever it says nothing about survives from the existing record."""
    if isinstance(incoming, str):
        return incoming if incoming.strip() else existing
    if isinstance(incoming, list):
        return incoming if incoming else existing
    return incoming if incoming is not None else existing


def normalize_person_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip().lower()


def merge_speakers(incoming: list[dict], existing: list[dict]) -> list[dict]:
    if not incoming:
        # No speaker parsed at all almost certainly means something failed to
        # parse, not that every speaker was intentionally removed.
        return existing
    existing_by_name = {normalize_person_name(s.get("name", "")): s for s in existing}
    merged = []
    for speaker in incoming:
        prior = existing_by_name.get(normalize_person_name(speaker.get("name", "")), {})
        merged.append(
            {
                "name": speaker.get("name", "") or prior.get("name", ""),
                "affiliation": prefer(speaker.get("affiliation", ""), prior.get("affiliation", "")),
                "role": prefer(speaker.get("role", ""), prior.get("role", "")),
                "website": prefer(speaker.get("website", ""), prior.get("website", "")),
                "photo": prior.get("photo", ""),  # never supplied by the calendar
                "email": prefer(speaker.get("email", ""), prior.get("email", "")),
                "bio": prefer(speaker.get("bio", ""), prior.get("bio", "")),
            }
        )
    return merged


def merge_record(incoming: dict, existing_raw: dict | None) -> dict:
    """Combine a freshly parsed calendar event with whatever is already on
    disk for this talk (None the first time a talk is seen). Fields the
    calendar supplies (non-empty) win; fields it says nothing about are kept
    from the existing record. date/start_time/end_time/canceled always come
    straight from the calendar -- they are unambiguous and always present."""
    existing_talk = (existing_raw or {}).get("talk", {})
    existing_speakers = (existing_raw or {}).get("speakers", []) or []

    merged = dict(incoming)
    for field in ("title", "series", "location", "zoom", "slides", "recording", "abstract"):
        merged[field] = prefer(incoming.get(field, ""), existing_talk.get(field, ""))
    merged["tags"] = prefer(incoming.get("tags", []), existing_talk.get("tags", []))
    for field in PRESERVE_ONLY_FIELDS:
        if existing_talk.get(field):
            merged[field] = existing_talk[field]
    merged["speakers"] = merge_speakers(incoming.get("speakers", []), existing_speakers)
    return merged


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def event_to_talk(event: dict) -> dict | None:
    start = parse_dt(event, "DTSTART")
    if start is None:
        return None
    end = parse_dt(event, "DTEND") or (start + dt.timedelta(hours=1))
    summary = get(event, "SUMMARY").strip()
    if not summary or any(
        SKIP_SUMMARY_RE.match(part) for part in [summary] + clean_summary(summary).split("|")
    ):
        return None

    description = html_to_text(get(event, "DESCRIPTION"))
    location_raw = get(event, "LOCATION").strip()
    links = classify_links(find_links(description + "\n" + location_raw))

    location = re.sub(r"https?://\S+", "", location_raw)
    location = re.sub(r"(?i)\b(and|&|\|)?\s*zoom\s*:?\s*(tba)?\s*$", "", location)
    if location.count("(") != location.count(")"):  # e.g. "FASB 295 (see link)" -> "FASB 295 ("
        location = location.split("(")[0]
    location = re.sub(r"(?i)\s*\b(and|&|or)\s*$", "", location).strip(" &|,-")

    summary_speaker_name, summary_title = split_speaker_and_title(summary)
    summary_name, summary_affiliation = split_name_affiliation(summary_speaker_name)

    md_fields, md_speakers, unknown_headers = parse_markdown_sections(description)

    if md_speakers:
        # Structured description: trust it completely rather than mixing in
        # the free-form heuristics below, which assume a layout this format
        # does not have.
        speakers = []
        for entry in md_speakers:
            name = entry.get("name", "").strip() or summary_name
            if not name or NOT_A_PERSON_RE.search(name):
                continue
            speakers.append(
                {
                    "name": name,
                    "affiliation": entry.get("affiliation", ""),
                    "role": entry.get("role", ""),
                    "website": entry.get("website", ""),
                    "email": entry.get("email", ""),
                    "bio": entry.get("bio", ""),
                }
            )
        if not speakers:
            return None

        title = clean_title(md_fields.get("title", "")) or clean_title(summary_title) or "TBA"
        abstract = clean_block(md_fields.get("abstract", ""))
        tags = md_fields.get("tags", [])
        location = md_fields.get("location", "") or location
        zoom = md_fields.get("zoom", "") or links["zoom"]
        slides = md_fields.get("slides", "") or links["slides"]
        recording = md_fields.get("recording", "") or links["recording"]
        series = md_fields.get("series", "") or infer_series(summary, start)
        needs_review = False
    else:
        # Free-form description (an entry from before this format, or one
        # that never adopted it) -- fall back to positional heuristics.
        body = strip_boilerplate(description)
        sections = split_sections(body)
        speaker_name, title = summary_speaker_name, summary_title

        # Labelled fields in the description win over whatever the summary said.
        if sections.get("speaker"):
            candidate = sections["speaker"].split("\n")[0].strip()
            if candidate and not re.match(r"(?i)^tba|^tbd", candidate):
                speaker_name = candidate
        if sections.get("title"):
            candidate = clean_title(sections["title"])
            if candidate:
                title = candidate

        blocks = paragraphs(body)
        used: set[int] = set()
        for i, block in enumerate(blocks):
            if any(re.match(rf"(?i)^{expr}\s*:", block) for expr in
                   (r"abstract", r"summary", r"bio", r"speaker", r"presenter", r"(?:talk )?title")):
                used.add(i)

        # Fall back to the unlabelled layout used by the older calendar entries:
        #   <title> / <speaker + affiliation + link> / <abstract paragraphs>
        if not title or title == "TBA":
            for i, block in enumerate(blocks):
                if i not in used and looks_like_title(block):
                    candidate = clean_title(block)
                    if candidate:
                        title = candidate
                        used.add(i)
                        break

        affiliation = ""
        name, affiliation = split_name_affiliation(speaker_name)
        if not affiliation:
            for i, block in enumerate(blocks):
                if i in used:
                    continue
                lines = [l.strip() for l in block.split("\n") if l.strip()]
                if lines and matches_name(lines[0], name):
                    _, affiliation = split_name_affiliation(lines[0])
                    if not affiliation and len(lines) > 1:
                        affiliation = clean_affiliation(
                            ", ".join(
                                l for l in lines[1:3] if not l.lower().startswith("http")
                            )
                        )
                    used.add(i)
                    break

        abstract = sections.get("abstract", "")
        if not abstract:
            remainder = [b for i, b in enumerate(blocks) if i not in used and len(b) > 200]
            abstract = "\n\n".join(remainder).strip()
        abstract = clean_block(abstract)
        bio = clean_block(sections.get("bio", ""))

        if not name or re.match(r"(?i)^(speaker\s*)?(tba|tbd)\b", name):
            return None
        if NOT_A_PERSON_RE.search(name):  # "Data Science Lecture Series", "Sandia Information Session", ...
            return None

        speakers = []
        for part in re.split(r"\s+(?:&|and)\s+|\s*,\s*(?=[A-Z][a-z]+\s+[A-Z])", name):
            part = part.strip(" ,;:-")
            if part:
                speakers.append(
                    {
                        "name": part,
                        "affiliation": affiliation,
                        "website": links["website"],
                        "bio": bio,
                    }
                )
        if not speakers:
            return None
        if len(speakers) > 1:  # a shared bio/website belongs to nobody in particular
            for speaker in speakers[1:]:
                speaker["website"] = ""

        tags = []
        zoom = links["zoom"]
        slides = links["slides"]
        recording = links["recording"]
        series = infer_series(summary, start)
        needs_review = True

    canceled = bool(CANCELED_RE.search(summary)) or get(event, "STATUS").upper() == "CANCELLED"

    return {
        "title": title or "TBA",
        "date": start.date().isoformat(),
        "start_time": start.strftime("%H:%M"),
        "end_time": end.strftime("%H:%M"),
        "series": series,
        "location": location,
        "zoom": zoom,
        "slides": slides,
        "recording": recording,
        "canceled": canceled,
        "abstract": abstract,
        "tags": tags,
        "speakers": speakers,
        "uid": event_uid(event),
        "needs_review": needs_review,
        "unknown_headers": unknown_headers,
        "last_modified": get(event, "LAST-MODIFIED"),
    }


def fetch_ics(path: str | None) -> str:
    if path:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    with urllib.request.urlopen(ICS_URL) as response:
        return response.read().decode("utf-8")


def in_window(date_str: str, window_start: dt.date, window_end: dt.date) -> bool:
    try:
        date = dt.date.fromisoformat(date_str)
    except ValueError:
        return False
    return window_start <= date <= window_end


def sync_talks(
    events: list[dict],
    *,
    window_days: int,
    dry_run: bool,
    force: bool,
    allow_bulk_delete: bool,
) -> int:
    """The daily sync: create, update, or delete records for talks starting
    within `window_days` of today, and leave everything else -- past talks,
    and anything further out that already has a record -- alone."""
    if not events:
        print(
            "error: the calendar feed contained zero events; refusing to sync "
            "(this usually means the fetch failed or was truncated)",
            file=sys.stderr,
        )
        return 1

    today = dt.datetime.now(TZ).date()
    window_start = today
    window_end = today + dt.timedelta(days=window_days)

    talks_by_uid: dict[str, dict] = {}
    for event in events:
        talk = event_to_talk(event)
        if talk is None:
            continue
        talks_by_uid[talk["uid"]] = talk

    existing = load_records(DATA_DIR)

    to_write: list[tuple[str, dict, str | None]] = []  # (key, merged_talk, old_path)
    created, updated, renamed, unknown_report = [], [], [], []

    for uid, talk in talks_by_uid.items():
        if talk["date"] < window_start.isoformat():
            continue  # a past-dated event is never created or updated here
        record = existing.get(uid)
        if record is None:
            merged = merge_record(talk, None)
        else:
            record_date = str(record["raw"].get("talk", {}).get("date", ""))
            record_in_window = bool(record_date) and in_window(record_date, window_start, window_end)
            if not record_in_window and not force:
                continue  # repo-owned: past its sync window, leave it alone
            prior_lm = record["raw"].get("meta", {}).get("calendar_last_modified", "")
            new_lm = format_last_modified(talk.get("last_modified", ""))
            if prior_lm == new_lm and not force:
                continue  # unchanged since the last sync
            merged = merge_record(talk, record["raw"])

        slug = slugify("-".join(s["name"] for s in merged["speakers"]))[:60]
        key = f'{merged["date"]}-{slug}'
        old_path = record["path"] if record else None
        to_write.append((key, merged, old_path))
        (created if record is None else updated).append(key)
        if talk.get("unknown_headers"):
            unknown_report.append((key, talk["unknown_headers"]))

    to_delete: list[tuple[str, str]] = []  # (key-ish label, path)
    for uid, record in existing.items():
        if uid in talks_by_uid:
            continue
        record_date = str(record["raw"].get("talk", {}).get("date", ""))
        if not record_date or not in_window(record_date, window_start, window_end):
            continue  # out of window (or dateless): the sync does not touch it
        label = os.path.splitext(os.path.basename(record["path"]))[0]
        to_delete.append((label, record["path"]))

    if to_delete and len(to_delete) > 3 and not allow_bulk_delete:
        print(
            f"error: this run would delete {len(to_delete)} record(s) in one go, which usually "
            "means the calendar fetch was truncated or failed rather than that this many talks "
            "were genuinely removed. Pass --allow-bulk-delete to proceed anyway.",
            file=sys.stderr,
        )
        for label, _ in to_delete:
            print(f"  would delete: {label}.toml", file=sys.stderr)
        return 1

    if not dry_run:
        os.makedirs(DATA_DIR, exist_ok=True)
        for key, merged, old_path in to_write:
            new_path = os.path.join(DATA_DIR, f"{key}.toml")
            with open(new_path, "w", encoding="utf-8") as handle:
                handle.write(render_toml(merged))
            if old_path and os.path.abspath(old_path) != os.path.abspath(new_path):
                os.remove(old_path)
        for _, path in to_delete:
            os.remove(path)

    for key, merged, old_path in to_write:
        if old_path:
            old_key = os.path.splitext(os.path.basename(old_path))[0]
            if old_key != key:
                renamed.append((old_key, key))

    print(f"window: {window_start.isoformat()} .. {window_end.isoformat()} ({window_days} days)")
    print(f"created: {len(created)}")
    for key in created:
        print(f"  + {key}.toml")
    print(f"updated: {len(updated)}")
    for key in updated:
        print(f"  ~ {key}.toml")
    for old_key, new_key in renamed:
        print(f"  renamed {old_key}.toml -> {new_key}.toml")
    print(f"deleted: {len(to_delete)}")
    for label, _ in to_delete:
        print(f"  - {label}.toml")
    if unknown_report:
        print("unrecognized headers (typo? see TALK_LABEL_ALIASES / SPEAKER_LABEL_ALIASES):")
        for key, headers in unknown_report:
            print(f"  {key}.toml: {', '.join(headers)}")
    if dry_run:
        print("\n(dry run: no files were written)")
    return 0


def backfill_talks(events: list[dict], *, since: str, until: str | None, overwrite: bool) -> int:
    """One-off seeding: write a TOML file for every calendar entry that does
    not already have one. Never updates or deletes an existing file unless
    --overwrite is given."""
    os.makedirs(DATA_DIR, exist_ok=True)
    written, skipped, seen = 0, 0, set()
    talks = []
    for event in events:
        talk = event_to_talk(event)
        if talk is None:
            skipped += 1
            continue
        if talk["date"] < since or (until and talk["date"] > until):
            continue
        talks.append(talk)

    talks.sort(key=lambda t: (t["date"], t["start_time"]))
    for talk in talks:
        slug = slugify("-".join(s["name"] for s in talk["speakers"]))[:60]
        key = f'{talk["date"]}-{slug}'
        if key in seen:
            continue
        seen.add(key)
        path = os.path.join(DATA_DIR, f"{key}.toml")
        if os.path.exists(path) and not overwrite:
            continue
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(render_toml(talk))
        written += 1

    print(f"imported {written} talk(s) into {os.path.relpath(DATA_DIR, ROOT)}")
    print(f"({skipped} calendar entries skipped: no speaker, placeholder, or malformed)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ics", help="path to a local .ics file (default: fetch the calendar)")
    parser.add_argument("--sync", action="store_true", help="run the window-aware daily sync")
    parser.add_argument(
        "--window-days", type=int, default=WINDOW_DAYS_DEFAULT,
        help=f"sync mode: how many days ahead the calendar owns (default {WINDOW_DAYS_DEFAULT})",
    )
    parser.add_argument("--dry-run", action="store_true", help="sync mode: report only, write nothing")
    parser.add_argument(
        "--force", action="store_true",
        help="sync mode: update/delete records outside the window too, and ignore LAST-MODIFIED",
    )
    parser.add_argument(
        "--allow-bulk-delete", action="store_true",
        help="sync mode: allow deleting more than 3 records in one run",
    )
    parser.add_argument("--since", default="2020-01-01", help="backfill mode: ignore talks before this date")
    parser.add_argument("--until", help="backfill mode: ignore talks after this date")
    parser.add_argument("--overwrite", action="store_true", help="backfill mode: rewrite existing TOML files")
    args = parser.parse_args()

    ics_text = fetch_ics(args.ics)
    events = parse_events(ics_text)

    if args.sync:
        return sync_talks(
            events,
            window_days=args.window_days,
            dry_run=args.dry_run,
            force=args.force,
            allow_bulk_delete=args.allow_bulk_delete,
        )
    return backfill_talks(events, since=args.since, until=args.until, overwrite=args.overwrite)


if __name__ == "__main__":
    sys.exit(main())
