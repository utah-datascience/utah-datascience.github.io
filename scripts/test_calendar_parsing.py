#!/usr/bin/env python3
"""Dependency-free tests for the calendar-sync parsing and merge logic.

Plain asserts over inline fixtures -- no pytest, so this runs anywhere Python
3.11+ does, including a bare CI step. Run with:

    python3 scripts/test_calendar_parsing.py

A failure raises AssertionError with a message naming the case; the runner
prints a one-line summary and exits non-zero if anything failed.
"""

from __future__ import annotations

import datetime as dt
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import import_calendar_talks as m  # noqa: E402


def make_event(**fields) -> dict:
    """Build an `event` dict in the shape parse_events() produces."""
    return {key: ("", value) for key, value in fields.items()}


# --------------------------------------------------------------------------- #
# parse_markdown_sections
# --------------------------------------------------------------------------- #
def test_clean_markdown_entry():
    text = (
        "## Title\n"
        "Scalable Manifold Learning\n\n"
        "## Speaker\n"
        "Kevin Moon\n\n"
        "## Affiliation\n"
        "Mathematics and Statistics, Utah State University\n\n"
        "## Website\n"
        "https://sites.google.com/view/kevin-moon\n\n"
        "## Bio\n"
        "Kevin is an assistant professor at USU.\n\n"
        "## Abstract\n"
        "The manifold assumption is used throughout ML.\n\n"
        "## Tags\n"
        "machine learning, visualization\n"
    )
    fields, speakers, unknown = m.parse_markdown_sections(text)
    assert fields["title"] == "Scalable Manifold Learning", fields
    assert fields["abstract"] == "The manifold assumption is used throughout ML.", fields
    assert fields["tags"] == ["machine learning", "visualization"], fields
    assert len(speakers) == 1, speakers
    assert speakers[0]["name"] == "Kevin Moon"
    assert speakers[0]["affiliation"] == "Mathematics and Statistics, Utah State University"
    assert speakers[0]["website"] == "https://sites.google.com/view/kevin-moon"
    assert speakers[0]["bio"] == "Kevin is an assistant professor at USU."
    assert unknown == []


def test_sloppy_headers():
    # Case, extra whitespace, a trailing colon, and "###" instead of "##".
    text = "##   TITLE   :\nA Sloppy Title\n\n###bio\nShort bio.\n"
    fields, speakers, unknown = m.parse_markdown_sections(text)
    assert fields["title"] == "A Sloppy Title", fields
    assert speakers == [{"bio": "Short bio."}], speakers
    assert unknown == []


def test_two_speaker_blocks():
    text = (
        "## Speaker\nKyle Dawson\n\n"
        "## Affiliation\nPhysics & Astronomy, University of Utah\n\n"
        "## Website\nhttps://faculty.utah.edu/u0634757\n\n"
        "## Speaker\nTyler Hagen\n\n"
        "## Affiliation\nPhysics & Astronomy, University of Utah\n"
    )
    _, speakers, _ = m.parse_markdown_sections(text)
    assert len(speakers) == 2, speakers
    assert speakers[0]["name"] == "Kyle Dawson"
    assert speakers[0]["website"] == "https://faculty.utah.edu/u0634757"
    assert speakers[1]["name"] == "Tyler Hagen"
    assert "website" not in speakers[1], "the first speaker's website must not leak to the second"


def test_tags_split_on_comma():
    _, _, _ = m.parse_markdown_sections("")  # sanity: empty text doesn't crash
    fields, _, _ = m.parse_markdown_sections("## Tags\nfairness & ethics,  statistics ,ml\n")
    assert fields["tags"] == ["fairness & ethics", "statistics", "ml"], fields


def test_unknown_header_reported():
    _, speakers, unknown = m.parse_markdown_sections(
        "## Speaker\nJohn Smith\n\n## Affiliaton\nTypo University\n"
    )
    assert unknown == ["Affiliaton"], unknown
    assert speakers[0]["name"] == "John Smith"


def test_legacy_text_is_not_structured():
    # No "##" headers at all -- must come back empty so the caller falls
    # through to the free-form heuristics, not silently produce zero speakers.
    fields, speakers, unknown = m.parse_markdown_sections(
        "Speaker: Jane Doe\nAbstract: something interesting"
    )
    assert fields == {} and speakers == [] and unknown == []


# --------------------------------------------------------------------------- #
# event_to_talk: structured vs. legacy fallback, end to end
# --------------------------------------------------------------------------- #
def test_event_to_talk_structured():
    event = make_event(
        **{
            "DTSTART;TZID=America/Denver": "20261115T133000",
            "DTEND;TZID=America/Denver": "20261115T143000",
        }
    )
    # make_event's simple key=value form can't carry ICS parameters, so build
    # this one by hand to match what parse_events() actually produces.
    event = {
        "DTSTART": (";TZID=America/Denver", "20261115T133000"),
        "DTEND": (";TZID=America/Denver", "20261115T143000"),
        "SUMMARY": ("", "UCDS+AI Lecture Series -- Test Speaker"),
        "DESCRIPTION": (
            "",
            "## Title\nScalable Manifold Learning\n\n"
            "## Speaker\nKevin Moon\n\n"
            "## Affiliation\nMath and Stats, USU\n\n"
            "## Abstract\nThe manifold assumption.\n\n"
            "## Tags\nmachine learning\n",
        ),
        "LOCATION": ("", "WEB L112"),
        "UID": ("", "structured-test-uid"),
        "STATUS": ("", "CONFIRMED"),
        "LAST-MODIFIED": ("", "20260901T120000Z"),
    }
    talk = m.event_to_talk(event)
    assert talk is not None
    assert talk["needs_review"] is False
    assert talk["title"] == "Scalable Manifold Learning"
    assert talk["tags"] == ["machine learning"]
    assert talk["speakers"][0]["name"] == "Kevin Moon"
    assert talk["speakers"][0]["affiliation"] == "Math and Stats, USU"
    assert talk["uid"] == "structured-test-uid"  # no RECURRENCE-ID on this one


def test_event_to_talk_legacy_labelled():
    event = {
        "DTSTART": (";TZID=America/Denver", "20220101T133000"),
        "DTEND": (";TZID=America/Denver", "20220101T143000"),
        "SUMMARY": ("", "UCDS Seminar : Jane Doe"),
        "DESCRIPTION": (
            "",
            "Data Science Seminar\n\nTitle:\nAn Old-Style Entry\n\n"
            "Jane Doe\nUniversity of Somewhere\n\n"
            "Abstract:\nThis entry predates the structured format entirely, "
            "and is long enough to look like a real abstract paragraph rather "
            "than a stray fragment of boilerplate text picked up by mistake.",
        ),
        "LOCATION": ("", "MEB 3147"),
        "UID": ("", "legacy-test-uid"),
        "STATUS": ("", "CONFIRMED"),
        "LAST-MODIFIED": ("", "20220101T000000Z"),
    }
    talk = m.event_to_talk(event)
    assert talk is not None
    assert talk["needs_review"] is True
    assert talk["title"] == "An Old-Style Entry", talk["title"]
    assert talk["speakers"][0]["name"] == "Jane Doe"
    assert talk["tags"] == []


def test_event_to_talk_skips_logistics_only():
    event = {
        "DTSTART": (";TZID=America/Denver", "20230101T133000"),
        "SUMMARY": ("", "Data Science Lecture Series"),
        "DESCRIPTION": ("", "Zoom link: https://utah.zoom.us/j/91737198805"),
        "UID": ("", "logistics-only-uid"),
    }
    assert m.event_to_talk(event) is None


def test_event_uid_uses_recurrence_id():
    base = {
        "DTSTART": (";TZID=America/Denver", "20220101T133000"),
        "SUMMARY": ("", "Data Science Seminar : Jane Doe"),
        "DESCRIPTION": ("", "Abstract:\nSomething long enough to count as a real paragraph here."),
        "UID": ("", "shared-series-uid"),
    }
    without_rid = dict(base)
    with_rid = dict(base, **{"RECURRENCE-ID": (";TZID=America/Denver", "20220101T133000")})
    assert m.event_uid(without_rid) == "shared-series-uid"
    assert m.event_uid(with_rid) == "shared-series-uid::20220101T133000"
    assert m.event_uid(without_rid) != m.event_uid(with_rid)


# --------------------------------------------------------------------------- #
# Window arithmetic
# --------------------------------------------------------------------------- #
def test_in_window():
    start = dt.date(2026, 9, 4)
    end = dt.date(2026, 12, 3)
    assert m.in_window("2026-09-04", start, end) is True   # inclusive start
    assert m.in_window("2026-12-03", start, end) is True   # inclusive end
    assert m.in_window("2026-09-03", start, end) is False  # just before
    assert m.in_window("2026-12-04", start, end) is False  # just after
    assert m.in_window("not-a-date", start, end) is False  # malformed: never in window


# --------------------------------------------------------------------------- #
# Merge rule: calendar wins when it supplies a field, existing survives when
# the calendar says nothing about it.
# --------------------------------------------------------------------------- #
def test_merge_preserves_repo_only_fields():
    existing_raw = {
        "talk": {
            "title": "Old title",
            "abstract": "Old abstract",
            "slides": "https://slides.example/old.pdf",
            "recording": "https://youtu.be/old",
            "paper": "https://arxiv.org/abs/old",
            "tags": ["machine learning"],
        },
        "speakers": [
            {"name": "Kevin Moon", "affiliation": "USU", "photo": "/assets/img/kmoon.jpg", "bio": "Old bio"}
        ],
    }
    incoming = {
        "title": "New title from the calendar",
        "series": "Data Science & AI Lecture Series",
        "location": "WEB L112",
        "zoom": "",
        "slides": "",
        "recording": "",
        "abstract": "New abstract from the calendar",
        "tags": [],
        "speakers": [{"name": "Kevin Moon", "affiliation": "", "website": "", "email": "", "bio": ""}],
    }
    merged = m.merge_record(incoming, existing_raw)
    assert merged["title"] == "New title from the calendar"  # calendar supplied it: wins
    assert merged["abstract"] == "New abstract from the calendar"
    assert merged["slides"] == "https://slides.example/old.pdf"  # calendar said nothing: kept
    assert merged["recording"] == "https://youtu.be/old"
    assert merged["paper"] == "https://arxiv.org/abs/old"  # never supplied by the calendar at all
    assert merged["tags"] == ["machine learning"]  # calendar sent no tags: kept
    assert merged["speakers"][0]["affiliation"] == "USU"  # calendar sent blank: kept
    assert merged["speakers"][0]["photo"] == "/assets/img/kmoon.jpg"  # never supplied: kept


def test_merge_speakers_empty_incoming_keeps_existing():
    # An empty speaker list from event_to_talk should never happen in
    # practice (event_to_talk returns None instead), but merge_speakers
    # guards against it directly: losing every speaker on a parse hiccup
    # would be a bad failure mode.
    existing = [{"name": "Jane Doe", "affiliation": "Somewhere"}]
    assert m.merge_speakers([], existing) == existing


def test_toml_round_trip_preserves_hand_added_fields():
    import tomllib

    talk = {
        "title": "T", "date": "2026-11-15", "start_time": "13:30", "end_time": "14:30",
        "series": "S", "location": "L", "zoom": "", "slides": "", "recording": "",
        "canceled": False, "abstract": "A", "tags": ["x"],
        "speakers": [{"name": "N", "affiliation": "", "role": "", "website": "", "email": "", "bio": ""}],
        "uid": "uid::", "needs_review": False, "unknown_headers": [], "last_modified": "",
    }
    rendered = m.render_toml(talk)
    parsed = tomllib.loads(rendered)
    assert parsed["talk"]["title"] == "T"
    assert parsed["meta"]["calendar_uid"] == "uid::"
    assert parsed["meta"]["needs_review"] is False


TESTS = [obj for name, obj in sorted(globals().items()) if name.startswith("test_")]


def main() -> int:
    failures = []
    for test in TESTS:
        try:
            test()
        except AssertionError as error:
            failures.append((test.__name__, str(error)))
            print(f"FAIL {test.__name__}: {error}")
        except Exception:  # noqa: BLE001
            failures.append((test.__name__, "unexpected exception"))
            print(f"ERROR {test.__name__}:")
            traceback.print_exc()
        else:
            print(f"ok   {test.__name__}")

    print(f"\n{len(TESTS) - len(failures)}/{len(TESTS)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
