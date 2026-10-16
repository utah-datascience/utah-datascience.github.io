#!/usr/bin/env python3
"""Dependency-free tests for scripts/post_bluesky.py (no network, no git).

Plain asserts over inline fixtures, like test_calendar_parsing.py:

    python3 scripts/test_post_bluesky.py
"""

from __future__ import annotations

import datetime as dt
import sys
import traceback
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
import post_bluesky as pb  # noqa: E402

TZ = ZoneInfo("America/Denver")
CFG = {
    "bluesky": {"mentions": [], "hashtags": ["DataScience"], "announce_days_before": 7, "reminder_hour": 9},
    "linkedin": {"notify": []},
}


def make_talk(slug="2026-10-23-jane-doe", day=dt.date(2026, 10, 23), title="Scalable Manifold Learning",
              speakers=None, canceled=False, needs_review=False, location="WEB 2250", zoom="https://z/1"):
    start = dt.datetime.combine(day, dt.time(13, 30), tzinfo=TZ)
    return {
        "slug": slug,
        "starts_at": start,
        "ends_at": start + dt.timedelta(hours=1),
        "canceled": canceled,
        "needs_review": needs_review,
        "body": "An abstract about manifolds.",
        "front": {"title": title, "location": location, "zoom": zoom, "series": "Data Science & AI Lecture Series"},
        "speakers": speakers if speakers is not None else [
            {"name": "Jane Doe", "affiliation": "Mathematics, USU", "website": "https://example.edu/~jane"}
        ],
    }


def at(y, mo, d, h=12, mi=0):
    return dt.datetime(y, mo, d, h, mi, tzinfo=TZ)


def kinds(talks, state, now):
    return [(t["slug"], kind) for t, kind in pb.due_posts(talks, state, CFG, now)]


# --------------------------------------------------------------------------- #
# What is due
# --------------------------------------------------------------------------- #
def test_nothing_before_the_announce_window():
    assert kinds([make_talk()], {}, at(2026, 10, 16, 13, 0)) == []


def test_announce_opens_seven_days_ahead():
    assert kinds([make_talk()], {}, at(2026, 10, 16, 13, 30)) == [("2026-10-23-jane-doe", "announce")]


def test_announce_is_not_repeated():
    state = {"2026-10-23-jane-doe": {"announce": {"status": "posted"}}}
    assert kinds([make_talk()], state, at(2026, 10, 20)) == []


def test_late_talk_still_gets_announced_once():
    # added to the calendar only two days out: the window already opened
    assert kinds([make_talk()], {}, at(2026, 10, 21)) == [("2026-10-23-jane-doe", "announce")]


def test_reminder_waits_for_the_morning_of():
    state = {"2026-10-23-jane-doe": {"announce": {"status": "posted"}}}
    assert kinds([make_talk()], state, at(2026, 10, 22, 23, 0)) == []
    assert kinds([make_talk()], state, at(2026, 10, 23, 8, 59)) == []
    assert kinds([make_talk()], state, at(2026, 10, 23, 9, 0)) == [("2026-10-23-jane-doe", "reminder")]


def test_reminder_replaces_an_unsent_announcement():
    assert kinds([make_talk()], {}, at(2026, 10, 23, 10)) == [("2026-10-23-jane-doe", "reminder")]


def test_nothing_once_the_talk_started():
    assert kinds([make_talk()], {}, at(2026, 10, 23, 13, 30)) == []


def test_canceled_talks_are_skipped():
    assert kinds([make_talk(canceled=True)], {}, at(2026, 10, 21)) == []


def test_unreviewed_record_waits_then_posts_anyway():
    talk = make_talk(needs_review=True)
    assert kinds([talk], {}, at(2026, 10, 18)) == [], "more than 2 days out: give a human time to fix it"
    assert kinds([talk], {}, at(2026, 10, 21, 14, 0)) == [("2026-10-23-jane-doe", "announce")]


def test_reminder_hour_follows_mountain_time_across_the_dst_switch():
    # 2026-11-01 is when clocks go back; a talk on Friday Nov 6 is on MST.
    talk = make_talk(slug="2026-11-06-x", day=dt.date(2026, 11, 6))
    utc = dt.timezone.utc
    assert kinds([talk], {}, dt.datetime(2026, 11, 6, 15, 59, tzinfo=utc)) == [], "08:59 MST"
    assert kinds([talk], {}, dt.datetime(2026, 11, 6, 16, 0, tzinfo=utc)) == [("2026-11-06-x", "reminder")], "09:00 MST"


# --------------------------------------------------------------------------- #
# Text, facets, length
# --------------------------------------------------------------------------- #
def facet_texts(post):
    raw = post["text"].encode("utf-8")
    return [(f["features"][0]["$type"].split("#")[1], raw[f["index"]["byteStart"]:f["index"]["byteEnd"]].decode("utf-8"))
            for f in post["facets"]]


def test_announcement_content_and_facets():
    post = pb.compose(make_talk(), "announce", CFG, {})[0]
    assert "“Scalable Manifold Learning”" in post["text"]
    assert "Fri, Oct 23 · 1:30–2:30 PM MT" in post["text"], post["text"]
    assert "WEB 2250 · Zoom" in post["text"]
    found = facet_texts(post)
    assert ("link", "Jane Doe") in found, "the speaker's name links to their website"
    assert ("link", "datascience.utah.edu/talks/2026-10-23-jane-doe/") in found, found
    assert ("tag", "#DataScience") in found
    assert post["embed"]["external"]["uri"].endswith("/talks/2026-10-23-jane-doe/")


def test_facet_offsets_are_utf8_bytes_not_characters():
    # emoji and accents earlier in the text shift byte offsets away from character offsets
    talk = make_talk(title="Données 📊 et modèles", speakers=[{"name": "José Núñez", "website": "https://e.edu"}])
    post = pb.compose(talk, "announce", CFG, {})[0]
    assert ("link", "José Núñez") in facet_texts(post), facet_texts(post)


def test_mentions_use_resolved_handles_only():
    talk = make_talk()
    talk["speakers"][0]["bluesky"] = "https://bsky.app/profile/Jane.bsky.social"
    cfg = {**CFG, "bluesky": {**CFG["bluesky"], "mentions": ["lab.bsky.social", "ghost.bsky.social"]}}
    dids = {"jane.bsky.social": "did:plc:jane", "lab.bsky.social": "did:plc:lab"}  # ghost did not resolve
    post = pb.compose(talk, "announce", cfg, dids)[0]
    mentions = [f["features"][0]["did"] for f in post["facets"] if f["features"][0]["$type"] == pb.MENTION]
    assert mentions == ["did:plc:jane", "did:plc:lab"], mentions
    assert ("mention", "@jane.bsky.social") in facet_texts(post)


def test_posts_never_exceed_the_limit_and_overflow_mentions_go_in_a_reply():
    long_title = "A Very Long Title About " + "Everything In Data Science " * 8
    handles = [f"person{i}.example.bsky.social" for i in range(12)]
    cfg = {**CFG, "bluesky": {**CFG["bluesky"], "mentions": handles}}
    dids = {h: f"did:plc:{i}" for i, h in enumerate(handles)}
    posts = pb.compose(make_talk(title=long_title), "announce", cfg, dids)
    for post in posts:
        assert pb.grapheme_len(post["text"]) <= pb.POST_LIMIT, pb.grapheme_len(post["text"])
    assert len(posts) == 2 and posts[1]["text"].startswith("With @person"), [p["text"] for p in posts]
    mentioned = sum(1 for p in posts for f in p["facets"] if f["features"][0]["$type"] == pb.MENTION)
    assert mentioned >= 2


def test_speaker_stays_in_the_main_post_even_when_crowded():
    talk = make_talk(title="T " * 100)
    talk["speakers"][0]["bluesky"] = "jane.bsky.social"
    handles = [f"p{i}.example.bsky.social" for i in range(10)]
    cfg = {**CFG, "bluesky": {**CFG["bluesky"], "mentions": handles}}
    dids = {h: "did:plc:x" for h in handles + ["jane.bsky.social"]}
    posts = pb.compose(talk, "announce", cfg, dids)
    assert "@jane.bsky.social" in posts[0]["text"]


def test_grapheme_count():
    assert pb.grapheme_len("abc") == 3
    assert pb.grapheme_len("é") == 1 and pb.grapheme_len("é") == 1
    assert pb.grapheme_len("👩‍💻") == 1, "ZWJ sequence is one grapheme"
    assert pb.grapheme_len("🇺🇸") == 1, "a flag is one grapheme"
    assert pb.grapheme_len("👍🏽") == 1, "skin-tone modifier"


def test_normalize_handle():
    assert pb.normalize_handle("@Jane.Bsky.Social") == "jane.bsky.social"
    assert pb.normalize_handle("https://bsky.app/profile/jane.example.edu/") == "jane.example.edu"
    assert pb.normalize_handle("not a handle") == ""
    assert pb.normalize_handle("") == ""


def test_unresolvable_handles_are_skipped_not_fatal():
    def resolver(handle):
        if handle == "bad.bsky.social":
            raise pb.PostError("HTTP 400")
        return "did:plc:ok"
    assert pb.resolve_all(["ok.bsky.social", "bad.bsky.social", "ok.bsky.social"], resolver) == {"ok.bsky.social": "did:plc:ok"}


def test_reminder_text():
    post = pb.compose(make_talk(), "reminder", CFG, {})[0]
    assert post["text"].startswith("⏰ Today, 1:30 PM MT"), post["text"]
    assert "🗓" not in post["text"]


def test_linkedin_text_has_the_essentials():
    text = pb.linkedin_text(make_talk())
    for needle in ("Scalable Manifold Learning", "Jane Doe", "WEB 2250", "/talks/2026-10-23-jane-doe/", "https://example.edu/~jane"):
        assert needle in text, needle


TESTS = [obj for name, obj in sorted(globals().items()) if name.startswith("test_")]


def main() -> int:
    failures = []
    for test in TESTS:
        try:
            test()
        except AssertionError as error:
            failures.append(test.__name__)
            print(f"FAIL {test.__name__}: {error}")
        except Exception:  # noqa: BLE001
            failures.append(test.__name__)
            print(f"ERROR {test.__name__}:")
            traceback.print_exc()
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(TESTS) - len(failures)}/{len(TESTS)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
