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


HEADER_VARIANTS = {
    "#title (h1, no space)": "#title\nA\n#speaker\nJane Doe",
    "# TITLE (trailing spaces)": "# TITLE  \nA\n# SPEAKER \nJane Doe",
    "trailing colon": "##   Title   :\nA\n## Speaker:\nJane Doe",
    "indented": "  ## title\nA\n  ## speaker\nJane Doe",
    "mixed case": "## TiTlE\nA\n## SpEaKeR\nJane Doe",
    "tab after #": "##\tTitle\nA\n##\tSpeaker\nJane Doe",
    "CRLF": "## Title\r\nA\r\n## Speaker\r\nJane Doe\r\n",
    "value on the header line": "## Title: A\n## Speaker: Jane Doe",
    "html <br>": "## Title<br>A<br><br>## Speaker<br>Jane Doe",
    "html <div> per line": "<div>## Title</div><div>A</div><div>## Speaker</div><div>Jane Doe</div>",
    "html <p> per line": "<p>## Title</p><p>A</p><p>## Speaker</p><p>Jane Doe</p>",
    "html bold header": "<b>## Title</b><br>A<br><b>## Speaker</b><br>Jane Doe",
    "&nbsp; after #": "##&nbsp;Title<br>A<br>##&nbsp;Speaker<br>Jane Doe",
}


def test_header_variants():
    # Every way a person plausibly types a header in Google Calendar, run
    # through the same html_to_text step the real feed goes through.
    for name, raw in HEADER_VARIANTS.items():
        fields, speakers, _ = m.parse_markdown_sections(m.html_to_text(raw))
        assert fields.get("title") == "A", f"{name}: title={fields.get('title')!r}"
        assert speakers and speakers[0].get("name") == "Jane Doe", f"{name}: speakers={speakers}"


def test_hash_lines_inside_a_body_are_kept():
    # Only a *known* field header ends a section, so prose that happens to
    # start with "#" stays in the abstract instead of silently truncating it.
    text = (
        "## Speaker\nJane Doe\n"
        "## Abstract\nFirst paragraph.\n#MachineLearning is everywhere.\nLast line.\n"
        "## Website: https://example.edu/a:b\n"
    )
    fields, speakers, unknown = m.parse_markdown_sections(text)
    assert fields["abstract"] == "First paragraph.\n#MachineLearning is everywhere.\nLast line.", fields
    assert speakers[0]["website"] == "https://example.edu/a:b"  # only the first ":" splits
    assert unknown == [], unknown  # a single "#" glued to a word is prose, not a typo


def test_structured_entry_is_authoritative_in_merge():
    # Requirement: for a talk the calendar owns, the calendar wins -- even when
    # the organizer *removes* something, the site should stop showing it.
    existing_raw = {
        "talk": {"title": "T", "abstract": "Old abstract", "slides": "https://s/old.pdf",
                 "tags": ["statistics"], "paper": "https://arxiv.org/abs/x"},
        "speakers": [{"name": "Jane Doe", "bio": "Old bio", "photo": "/p.jpg"}],
    }
    incoming = {
        "title": "T", "series": "S", "location": "WEB L112", "zoom": "", "slides": "",
        "recording": "", "abstract": "", "tags": [], "needs_review": False,
        "speakers": [{"name": "Jane Doe", "affiliation": "", "website": "", "email": "", "bio": ""}],
    }
    merged = m.merge_record(incoming, existing_raw)
    assert merged["abstract"] == "", "structured entry with no abstract clears the old one"
    assert merged["speakers"][0]["bio"] == "", "structured entry with no bio clears the old one"
    assert merged["speakers"][0]["photo"] == "/p.jpg", "photos are never supplied by the calendar"
    assert merged["slides"] == "https://s/old.pdf", "slides are added in the repo"
    assert merged["tags"] == ["statistics"], "tags are filled in by tag_talks.py"
    assert merged["paper"] == "https://arxiv.org/abs/x"


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


def test_unreadable_entry_is_published_with_a_date_title():
    # Nothing here names a speaker -- only the series and a Zoom link. It is
    # still a talk slot on the calendar, so it gets a page rather than being
    # silently dropped.
    event = {
        "DTSTART": (";TZID=America/Denver", "20240823T133000"),
        "SUMMARY": ("", "Data Science Lecture Series"),
        "DESCRIPTION": ("", "Zoom link: https://utah.zoom.us/j/91737198805"),
        "UID": ("", "logistics-only-uid"),
    }
    talk = m.event_to_talk(event)
    assert talk is not None
    assert talk["title"] == "Talk of Friday, August 23rd", talk["title"]
    assert talk["speakers"] == []
    assert talk["needs_review"] is True
    assert talk["zoom"] == "https://utah.zoom.us/j/91737198805"
    assert talk["abstract"] == "", "no speaker to anchor on, so no guessed abstract"
    assert m.record_key(talk) == "2024-08-23-talk"


def test_fallback_keeps_labelled_fields():
    for summary in ("TBA", "", "UCDS+AI Seminar"):
        event = {
            "DTSTART": (";TZID=America/Denver", "20261009T133000"),
            "SUMMARY": ("", summary),
            "DESCRIPTION": ("", "## Title\nA Real Title\n\n## Abstract\nA real abstract."),
            "UID": ("", "tba-uid"),
        }
        talk = m.event_to_talk(event)
        assert talk is not None, summary
        assert talk["title"] == "A Real Title", (summary, talk["title"])
        assert talk["abstract"] == "A real abstract."


def test_non_talks_are_still_skipped():
    for summary in ("No seminar", "No Data Science Seminar", "Spring Break", "Holiday",
                    "Hold for faculty meeting", "Reserved", "UCDS Social",
                    "Sandia Information Session (pizza)", "UCDS Seminar : canceled"):
        event = {
            "DTSTART": (";TZID=America/Denver", "20261009T133000"),
            "SUMMARY": ("", summary),
            "UID": ("", "x"),
        }
        assert m.event_to_talk(event) is None, summary


def test_seminar_prefix_is_not_the_speaker():
    speaker, _ = m.split_speaker_and_title("Seminar: Anna Little (Utah)")
    assert m.split_name_affiliation(speaker) == ("Anna Little", "Utah"), speaker


def test_fallback_title_ordinals():
    import datetime as _dt
    cases = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 11: "11th", 12: "12th",
             13: "13th", 21: "21st", 22: "22nd", 23: "23rd", 31: "31st"}
    for day, expected in cases.items():
        assert m.ordinal(day) == expected, (day, m.ordinal(day))
    assert m.fallback_title(_dt.date(2024, 8, 23)) == "Talk of Friday, August 23rd"


def test_fallback_does_not_downgrade_a_known_talk():
    # A record that already knows its speaker keeps its title if a later edit
    # to the calendar entry makes it unreadable.
    existing_raw = {"talk": {"title": "Real Title"}, "speakers": [{"name": "Jane Doe"}]}
    incoming = {"title": "Talk of Friday, October 9th", "series": "S", "location": "", "zoom": "",
                "slides": "", "recording": "", "abstract": "", "tags": [], "speakers": [],
                "needs_review": True}
    merged = m.merge_record(incoming, existing_raw)
    assert merged["title"] == "Real Title"
    assert merged["speakers"] == [{"name": "Jane Doe"}]


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
