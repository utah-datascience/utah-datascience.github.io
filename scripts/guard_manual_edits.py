#!/usr/bin/env python3
"""Fail if a talk record inside the calendar's sync window was edited by hand.

Google Calendar owns any talk starting within WINDOW_DAYS of today (see
import_calendar_talks.py); a manual edit to one of those records in this repo
is either silently overwritten by the next sync (an edit) or resurrected (a
deletion), so this exists to catch it before it merges or publishes rather
than let it quietly vanish.

Usage:
    python3 scripts/guard_manual_edits.py <base-ref> <head-ref>

Compares _data/talks/*.toml between the two refs (needs a checkout with
enough history for both to resolve -- fetch-depth: 0). Exits 0 if nothing to
guard against, 1 with GitHub Actions ::error annotations and a step-summary
table if a violation was found.

The escape hatch (an `allow-manual-entry` label or PR title marker) is
checked by the caller, not here -- see .github/workflows/talks.yml and
.github/workflows/pages.yml, which skip invoking this script at all when it
applies.
"""

from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from import_calendar_talks import TZ, WINDOW_DAYS_DEFAULT  # noqa: E402

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"  # git's well-known empty tree
ACTION_NAMES = {"A": "added", "M": "edited", "D": "deleted", "R": "renamed"}


def resolve_ref(ref: str) -> str:
    # A push event's "before" is all zeros on a branch's first push.
    return EMPTY_TREE if set(ref) <= {"0"} else ref


def changed_talk_paths(base: str, head: str) -> list[tuple[str, str]]:
    out = subprocess.run(
        ["git", "diff", "--name-status", f"{base}..{head}", "--", "_data/talks/*.toml"],
        capture_output=True, text=True, check=True,
    ).stdout
    changes = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status, path = parts[0][0], parts[-1]
        if os.path.basename(path).startswith("_"):
            continue  # _TEMPLATE.toml and friends
        changes.append((status, path))
    return changes


def read_date(ref: str, path: str) -> str | None:
    try:
        raw = subprocess.run(
            ["git", "show", f"{ref}:{path}"], capture_output=True, text=True, check=True
        ).stdout
    except subprocess.CalledProcessError:
        return None
    try:
        return str(tomllib.loads(raw).get("talk", {}).get("date", ""))
    except tomllib.TOMLDecodeError:
        return None


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: guard_manual_edits.py <base-ref> <head-ref>", file=sys.stderr)
        return 2
    base, head = resolve_ref(sys.argv[1]), sys.argv[2]

    window_days = int(os.environ.get("GUARD_WINDOW_DAYS", WINDOW_DAYS_DEFAULT))
    today = dt.datetime.now(TZ).date()
    window_end = today + dt.timedelta(days=window_days)

    violations = []
    for status, path in changed_talk_paths(base, head):
        date_str = read_date(base if status == "D" else head, path)
        if not date_str:
            continue
        try:
            date = dt.date.fromisoformat(date_str)
        except ValueError:
            continue
        if today <= date <= window_end:
            violations.append((path, date_str, ACTION_NAMES.get(status, status)))

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")

    if not violations:
        print("ok: no in-window talk record was edited directly in the repo")
        return 0

    intro = (
        f"Google Calendar owns any talk starting within {window_days} days "
        f"({today.isoformat()} .. {window_end.isoformat()}). The record(s) below "
        "were changed directly in this repo instead of on the calendar event, "
        "and would otherwise be silently overwritten (or, for a deletion, "
        "resurrected) by the next scheduled sync."
    )
    fix = (
        "Fix: make the change on the calendar event instead -- the daily sync "
        "will push it and republish the site. If this genuinely needs to be a "
        "manual repo edit, add the `allow-manual-entry` label to this pull "
        "request (or include `[allow-manual-entry]` in its title) and re-run."
    )

    for path, date_str, action in violations:
        message = f"{path} is dated {date_str}, inside the sync window ({action} directly in the repo)"
        print(f"::error file={path}::{message}")

    print(f"\n{intro}\n\n{fix}", file=sys.stderr)

    if summary_path:
        lines = [
            "### Manual edit to a calendar-owned talk record", "",
            intro, "", fix, "",
        ]
        lines += [f"- `{path}` ({date_str}, {action})" for path, date_str, action in violations]
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
