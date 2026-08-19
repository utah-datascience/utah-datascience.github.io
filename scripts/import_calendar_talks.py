#!/usr/bin/env python3
"""Import talk records from the seminar's public Google Calendar feed.

This is a *seeding / convenience* tool: it turns calendar entries into TOML
records under `_data/talks/`, which are then the source of truth for the site.
Calendar descriptions are free-form, so the parsing here is best effort; every
imported record should be reviewed (and the fields it could not fill in, such
as slides or recording links, filled in by hand).

Usage:
    python3 scripts/import_calendar_talks.py                 # fetch + import new talks
    python3 scripts/import_calendar_talks.py --overwrite      # also rewrite existing files
    python3 scripts/import_calendar_talks.py --ics cal.ics    # use a local .ics file
    python3 scripts/import_calendar_talks.py --since 2025-01-01
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import os
import re
import sys
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "_data", "talks")

# Boilerplate that shows up in the calendar summaries and is not part of a title.
SERIES_NOISE = [
    "UCDS+AI Lecture Series",
    "UCDS+AI Seminar",
    "UCDS + AI Seminar",
    "Data Science and AI Seminar",
    "Data Science & AI Seminar",
    "Data Science Seminar",
    "Data Seminar",
    "UCDS Seminar",
]

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


BOILERPLATE_LINE_RE = re.compile(
    r"^(?:the\s+)?(?:utah\s+center\s+for\s+)?data\s+science(?:\s*(?:&|and)\s*ai)?"
    r"\s*(?:seminar|lecture series)?\s*$|"
    r"^(?:ucds|ucds\+ai)\b.*$|"
    r"^join zoom meeting$|^meeting id\b|^passcode\b|^one tap mobile$|"
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
    text = re.sub(r"\s+@\s+", "|", text)
    parts = [p.strip(" -–—:|@\t") for p in text.split("|")]
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


def looks_like_person(text: str) -> bool:
    core = re.sub(r"\(.*?\)", "", text).strip()
    if not core or len(core) > 60:
        return False
    words = core.split()
    if not 1 < len(words) <= 5:
        return False
    if re.search(r"[:;]", core):
        return False
    return all(w[0].isupper() or not w[0].isalpha() for w in words)


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
    lines = [
        "# Imported from the seminar Google Calendar -- please review and complete.",
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
        f'canceled = {"true" if talk["canceled"] else "false"}',
        f'abstract = {toml_str(talk["abstract"])}',
        "",
    ]
    for speaker in talk["speakers"]:
        lines += [
            "[[speakers]]",
            f'name = {toml_str(speaker["name"])}',
            f'affiliation = {toml_str(speaker["affiliation"])}',
            f'website = {toml_str(speaker["website"])}',
            'photo = ""',
            f'bio = {toml_str(speaker["bio"])}',
            "",
        ]
    lines += [
        "[meta]",
        'source = "google-calendar"',
        f'calendar_uid = {toml_str(talk["uid"])}',
        f'imported_on = {dt.date.today().isoformat()}',
        "needs_review = true",
        "",
    ]
    return "\n".join(lines)


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

    body = strip_boilerplate(description)
    sections = split_sections(body)
    speaker_name, title = split_speaker_and_title(summary)

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

    series = (
        "Data Science & AI Lecture Series"
        if re.search(r"(?i)ucds\+ai|lecture series", summary) or start.year >= 2025
        else "Data Science Seminar"
    )

    return {
        "title": title or "TBA",
        "date": start.date().isoformat(),
        "start_time": start.strftime("%H:%M"),
        "end_time": end.strftime("%H:%M"),
        "series": series,
        "location": location,
        "zoom": links["zoom"],
        "slides": links["slides"],
        "recording": links["recording"],
        "canceled": bool(CANCELED_RE.search(summary)),
        "abstract": abstract,
        "speakers": speakers,
        "uid": get(event, "UID"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ics", help="path to a local .ics file (default: fetch the calendar)")
    parser.add_argument("--since", default="2020-01-01", help="ignore talks before this date")
    parser.add_argument("--until", help="ignore talks after this date")
    parser.add_argument("--overwrite", action="store_true", help="rewrite existing TOML files")
    args = parser.parse_args()

    if args.ics:
        with open(args.ics, encoding="utf-8") as handle:
            ics_text = handle.read()
    else:
        with urllib.request.urlopen(ICS_URL) as response:
            ics_text = response.read().decode("utf-8")

    os.makedirs(DATA_DIR, exist_ok=True)
    written, skipped, seen = 0, 0, set()
    talks = []
    for event in parse_events(ics_text):
        talk = event_to_talk(event)
        if talk is None:
            skipped += 1
            continue
        if talk["date"] < args.since or (args.until and talk["date"] > args.until):
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
        if os.path.exists(path) and not args.overwrite:
            continue
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(render_toml(talk))
        written += 1

    print(f"imported {written} talk(s) into {os.path.relpath(DATA_DIR, ROOT)}")
    print(f"({skipped} calendar entries skipped: no speaker, placeholder, or malformed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
