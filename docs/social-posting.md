# Bluesky announcements

`.github/workflows/bluesky-post.yml` runs hourly and posts about upcoming talks
on Bluesky, using `scripts/post_bluesky.py`. It reads the talk records in
`_data/talks/` (the same ones the website is built from), so a post can never
disagree with the site.

For each talk (never a canceled one) it posts twice:

| Post | When | Contains |
| --- | --- | --- |
| Announcement | 7 days before (`announce_days_before`) | title, speaker(s), date and time, room and Zoom, the talk's page, hashtags, tags |
| Reminder | the morning of the talk, from 9 AM Mountain (`reminder_hour`) | the same, with "Today, 1:30 PM" in place of the date |

The speaker's name links to their `website`. The main post is limited to 300
characters, so if it is crowded it first drops the hashtags, then the
affiliation, then the Zoom note, then shortens the title. Mentions that still
don't fit go in a reply.

On the day of a talk only the reminder is posted, even if the announcement
never went out. A record the calendar sync flagged `needs_review = true` is
held back until two days before the talk, so there is time to fix a garbled
title; after that it is posted as is.

With each announcement the workflow also opens a **"LinkedIn post: ..." issue**
(label `social`) holding ready-to-paste text and @mentioning the people in
`[linkedin].notify`; GitHub emails them. Close the issue once it is posted.

## Who gets tagged

Edit `_data/social.toml`:

```toml
[bluesky]
mentions = ["someone.bsky.social"]   # tagged on every post
hashtags = ["DataScience"]

[linkedin]
notify = ["github-username"]         # @mentioned in the LinkedIn issue
```

The speaker is tagged too if their Bluesky handle is known. Put it in the
calendar event description, like the other speaker fields:

```markdown
## Speaker
Speaker Name

## Bluesky
@speaker.bsky.social
```

(or `bluesky = "..."` in the `[[speakers]]` block of a talk record outside the
sync window). Handles that don't resolve are skipped with a warning, never an
error.

## Setup (once)

1. Create an **app password** for the posting account (Bluesky -> Settings ->
   Privacy and security -> App passwords). Never use the account password.
2. Add repository secrets `BLUESKY_HANDLE` (e.g. `utahdatascience.bsky.social`)
   and `BLUESKY_APP_PASSWORD`.
3. Run the workflow manually from the Actions tab with **dry_run** on and read
   the log; it prints each post, its length, and its link/mention/tag facets.

## Trying it locally

```sh
make bluesky-dry-run                                        # what is due now
python3 scripts/post_bluesky.py --dry-run --now 2026-10-17T10:00:00-06:00
python3 scripts/post_bluesky.py --dry-run --slug 2026-10-23-jane-doe --kind reminder
make test-bluesky
```

Local dry runs post nothing and write nothing (they do look up mentioned
handles on Bluesky's public API).

## What was posted

`_data/social_posted.json` records each post. The workflow marks a post
`pending` and **pushes that to master before posting**; if a run dies between
posting and recording, later runs fail with an error naming the post instead of
posting it again. Check the Bluesky account, then set that entry to
`"status": "posted"` (or delete it to have it posted again).

To re-post something deliberately, run the workflow manually with a `slug` and
`kind` and dry_run off after deleting its entry from the file.
