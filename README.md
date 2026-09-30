# Utah Data Science Center

[![Deploy site](https://github.com/utah-datascience/utah-datascience.github.io/actions/workflows/pages.yml/badge.svg)](https://github.com/utah-datascience/utah-datascience.github.io/actions/workflows/pages.yml)
[![Talk pages](https://github.com/utah-datascience/utah-datascience.github.io/actions/workflows/talks.yml/badge.svg)](https://github.com/utah-datascience/utah-datascience.github.io/actions/workflows/talks.yml)
[![Sync talks from Google Calendar](https://github.com/utah-datascience/utah-datascience.github.io/actions/workflows/sync-talks.yml/badge.svg)](https://github.com/utah-datascience/utah-datascience.github.io/actions/workflows/sync-talks.yml)

Original theme: https://jamstack-argon-design.appseed.us/index.html

## Local run
* For the first time, install [jekyll](https://jekyllrb.com/docs/installation/), if windows, you may need further run `bundle add webrick`.
  Then run follow in the project root.
  ```shell
  bundle install
  ```
* If failed because of gem version incompatible, try
  ```shell
  bundle update
  ```
This will update `Gemfile.lock`.
* To serve the website locally, run
  ```shell
  bundle exec jekyll serve
  ```

You can also use `make setup`, `make serve`, `make build`, etc. Run `make help` to see all available targets.

## Content Edit
### Images in markdown
To center the image and avoid big images overflow, you can specify the class `img-fluid` for the image by appending `{:class="img-fluid"}`, like
```markdown
![alt text](/path/to/image.jpg){:class="img-fluid"}
```
`img-fluid` class has been defined as `display: block; margin: auto; max-width: 90%; height: auto`.
### Image as a figure
We have a figure template for adding a figure to any page. Example code is:
```html
{% include figure.html
src="/assets/img/theme/team-1-800x800.jpg"
max-width="500px"
caption="The caption of the figure." %}
```

## Notes for specific pages.
### Members
Add/delete/edit .md files in `_members` directory to add/delete/edit members. 

`Director, Associate Director of Research, ...` are called *roles*, order and available values for role are hard coded in `members.md` file.

Members in the same role are sorted by the file name. Please name them in the format like `Lastname-Firstname-Middlename.md`. Here is an example file content:

```YAML
---
name: Jeff M. Phillips
role: Director
title: |
    Associate Professor, School of Computing, University of Utah
link: http://www.cs.utah.edu/~jeffp/
pic: assets/img/member_photos/jeff.png
---
He specializes in designing algorithms for data science.
```

The available variables are:

| Variable | Description |
| -------- | ------------- |
| name     | The name of the member to be shown.    |
| role     | Under which role to diplay the member. Available values are hard coded in `members.md` file.|
| title    | Title of the member to be display under the name. Using block style indicator `|` to keep newlines between multiline. |
| link     | The link for the photo and name. |
| pic      | The photo of the member. It can be an exist link to an image, or a path to the image. |

> **_NOTE:_**  The subfolders (affiliated, core, and leadership) under `_members` have no effects. They exist only for organizing these files. To show member under a role, set the role variable in its .md file with a right value.

### Talks

Every talk in the Data Science & AI Lecture Series has its own page on the site
(for example `/talks/2026-09-04-george-vega-yon/`). Those pages are **generated**
from a TOML record per talk in `_data/talks/` -- but who is allowed to edit that
record depends on when the talk happens:

* **Talks starting soon** (within the *sync window*, 90 days by default):
  **Google Calendar is the source of truth.** Edit the calendar event; a daily
  sync turns it into a pull request. Editing the TOML file directly is blocked
  by CI -- see [The sync window](#the-sync-window) below.
* **Past talks, and anything further out than the window:** the repo is the
  source of truth. Edit the TOML file directly, the ordinary way.

Nothing here ever writes back to Google Calendar in the other direction.

#### Adding or editing an upcoming talk

Write (or edit) the calendar event's description using level 1-6 Markdown
headers (any number of `#`) to label each field. Headers are forgiving of case,
spacing, and a trailing colon -- `#title`, `# TITLE `, `## Title`, and
`###   Title   :` all work the same -- and the value can go on the next line or
on the same one (`## Title: Something`). Everything up to the next recognized
header is that field's value; a line starting with `#` that is *not* a
recognized field (a hashtag in an abstract, say) stays part of the text. A
header that looks like a misspelled field (`## Affiliaton`) is kept as text too,
and flagged in the sync PR's report so it can be fixed on the calendar. Paste
this in and fill it out:

```markdown
## Title
Title of the talk

## Speaker
Speaker Name

## Affiliation
Department, University

## Website
https://example.edu/~speaker

## Bio
A short bio, in Markdown.

## Abstract
The abstract, in Markdown. Can span several paragraphs.

## Tags
machine learning, visualization
```

For a talk with more than one speaker, repeat the `## Speaker` block -- each
one starts a new speaker, and `## Affiliation` / `## Website` / `## Bio` (and
`## Role`, `## Email`) attach to whichever `## Speaker` came most recently
above them:

```markdown
## Speaker
Kyle Dawson

## Affiliation
Physics & Astronomy, University of Utah

## Speaker
Tyler Hagen

## Affiliation
Physics & Astronomy, University of Utah
```

Recognized headers (aliases in parentheses; see `TALK_LABEL_ALIASES` and
`SPEAKER_LABEL_ALIASES` at the top of `scripts/import_calendar_talks.py` for
the exact, current list):

| Talk | Speaker |
| --- | --- |
| Title | Affiliation (institution, department) |
| Abstract (summary) | Website (url, homepage, link) |
| Tags (topics, keywords) | Bio (biography, about the speaker) |
| Location (room, venue) | Email |
| Zoom (meeting, meeting link) | Role (position) |
| Slides | |
| Recording (video) | |
| Series | |

Location, Zoom, Slides, and Recording only need a header if you want to
override what the sync would otherwise pick up from the event's own Location
field or a link in the description -- most entries can skip them. Tags is a
comma-separated list; stick to the vocabulary in `scripts/tag_talks.py`
(`machine learning`, `visualization`, `health & medicine`, and about twenty
more) so the `/talks/` filters stay useful, or add a term to the vocabulary
first. Slides and recording links are almost always added later, once the talk
has already happened and its record has left the sync window -- see below.

An entry that never adopts this format still gets imported, using best-effort
heuristics on whatever plain text is there; the resulting record is flagged
`needs_review = true` and should be checked by hand once it lands.

Once the daily sync (or a maintainer running it manually) picks up the change,
it lands as a pull request from a branch named `entry-update`. **Review and
merge that PR** -- that's what publishes it.

#### The sync window

`scripts/import_calendar_talks.py --sync` is what keeps `_data/talks/` in step
with the calendar. Given `today` and a `--window-days` (default 90, matching
`WINDOW_DAYS_DEFAULT` in that script):

| A talk starting... | is... |
| --- | --- |
| before today | untouched -- repo-owned, past talks are history |
| within the window | created, updated, or deleted to match the calendar |
| after the window | created if missing; never updated once it exists |

A talk removed from the calendar while still inside the window has its record
**deleted** (not merely marked canceled) -- a subscribed calendar re-syncs
against the whole feed, so the event disappears there too. A talk the calendar
still lists but marks cancelled keeps its record, with `canceled = true`; that
is what the page badge and `talks.ics`'s `STATUS:CANCELLED` are for. As a
safety rail against a truncated or failed calendar fetch, the sync refuses to
run at all if the feed came back with zero events, and refuses to delete more
than three records in one run without `--allow-bulk-delete`.

**For an entry in the structured format, the calendar wins outright**: remove
the abstract or a bio from the event, and the next sync removes it from the
site too. The exceptions are things the calendar is not where they come from --
slides and recording links (added in the repo once they exist, unless the
calendar supplies one), tags (filled in by `scripts/tag_talks.py` unless the
event has a `## Tags` section), speaker photos, and the `paper` and custom
`slug` fields (see `_TEMPLATE.toml`); those survive a resync untouched. For a
free-form entry the heuristics routinely miss fields, so there a missing field
never clears an existing value.

Because Google Calendar owns any in-window record, **editing one of those TOML
files directly in this repo is blocked**: `.github/workflows/talks.yml` runs
`scripts/guard_manual_edits.py` on every pull request and fails it if a changed
record's date falls inside the window (the authoritative copy of this check,
which is what actually blocks the site from republishing, runs again from
`.github/workflows/pages.yml` on push to master). Edit the calendar event
instead, and let the sync open its usual PR. For the rare edit that genuinely
has to happen here -- add the `allow-manual-entry` label to the pull request,
or put `[allow-manual-entry]` in its title.

Running the sync yourself:

```shell
make sync-talks-dry-run       # preview what would change
make sync-talks                # or: python3 scripts/import_calendar_talks.py --sync
python3 scripts/import_calendar_talks.py --sync --window-days 30
```

It normally runs on its own: `.github/workflows/sync-talks.yml` triggers daily
and opens or updates the pull request from `entry-update` -- reused across
runs, so a week of small calendar edits accumulates into one PR rather than a
pile of them.

#### Editing a past talk, or adding one from scratch

For anything outside the window -- fixing a typo in an old abstract, adding a
recording link once one exists, or backfilling a talk that predates all of
this -- edit (or create) the TOML file the ordinary way and open a PR. Copy
`_data/talks/_TEMPLATE.toml` to `_data/talks/YYYY-MM-DD-speaker-name.toml` for
a brand new record; the file name becomes the page URL, so keep the
`date-speaker` shape. Then:

1. Run `make talks` (equivalently `python3 scripts/generate_talks.py`). This
   writes `_talks/YYYY-MM-DD-speaker-name.md`, and regenerates `talks.ics` and
   `talks.json`.
2. Commit the TOML file together with everything `make talks` changed, and
   open a pull request. CI (`.github/workflows/talks.yml`) re-runs the
   generator and fails if they are out of sync.

The generated pages are wired into the site automatically:

* `seminar.md` shows the next talk and the next few upcoming talks.
* `/talks/` (`talks.md`) lists everything, upcoming first, then past talks by year.

A minimal record looks like this:

```toml
[talk]
title = "Data Science of Tracking Measles in Utah"
date = 2026-09-04
start_time = "13:30"
end_time = "14:30"
location = "WEB 2250"
zoom = "https://utah.zoom.us/j/85983626630"
abstract = """
What the talk is about, in markdown.
"""

[[speakers]]
name = "George Vega Yon"
affiliation = "Division of Epidemiology, University of Utah"
website = "https://ggvy.cl"
bio = """
A short bio, in markdown.
"""
```

Only `[talk] title`, `[talk] date`, and one `[[speakers]] name` are required;
everything else is optional and simply omitted from the page when empty. Add a
`[[speakers]]` block per speaker for joint talks, and set `canceled = true`
rather than deleting a record for a talk that did not happen.

Why TOML plus a generator? GitHub Pages builds Jekyll in safe mode, so custom
plugins (which could read TOML at build time) are not available: the pages have
to be generated ahead of time and committed.

#### Tags and searching

Each record carries a `tags` list drawn from a fixed vocabulary (about twenty
topics: `machine learning`, `visualization`, `health & medicine`, and so on --
the full list lives at the top of `scripts/tag_talks.py`). The `/talks/` page
uses them for its filters, so free-form tags would only fragment the results:
stick to the vocabulary, or add a term to the vocabulary first.

`scripts/tag_talks.py` fills in tags automatically by matching a talk's title,
abstract, and speaker bio against that vocabulary:

```shell
python3 scripts/tag_talks.py --dry-run   # show what it would pick
python3 scripts/tag_talks.py             # fill in records with no tags yet
python3 scripts/tag_talks.py --report    # tag counts across all talks
```

It never touches a record that already has tags, so anything you set by hand
wins. Tagging by hand is perfectly fine too -- just edit `tags` in the TOML.

`/talks/` searches and filters entirely in the browser, with no index to build
and no service to run: the page ships every talk as a list item carrying its
searchable text in a `data-search` attribute, and the JavaScript at the bottom
of `talks.md` hides the ones that do not match. Readers can search across every
field (title, speaker, affiliation, abstract, location, date), filter by tag,
speaker, or year, and land on a pre-filtered view via a link such as
`/talks/?tag=robotics` or `/talks/?speaker=Anna%20Fariha`. Without JavaScript
the full list still renders; only the filter controls are hidden.

#### The calendar feed (talks.ics)

`make talks` also writes `talks.ics`, an iCalendar feed of every talk record,
served at <https://datascience.utah.edu/talks.ics>. It is generated and
committed like the talk pages, and the same CI check keeps it from going stale,
so the feed on the live site always matches the records in `_data/talks/`.

**Share this URL**, and it works in every calendar app:

```
https://datascience.utah.edu/talks.ics
```

* **Google Calendar**: *Other calendars* -> *+* -> *From URL*, paste the URL
* **Outlook** (web / Microsoft 365): *Add calendar* -> *Subscribe from web*, paste the URL
* **Apple Calendar**: *File* -> *New Calendar Subscription*, paste the URL (or
  open `webcal://datascience.utah.edu/talks.ics`, which does it in one click)
* **Thunderbird and the rest**: any "subscribe to a remote calendar" option

Use the GitHub Pages URL above rather than a `raw.githubusercontent.com` link.
The raw file is served as `text/plain` (some clients refuse to subscribe), the
URL carries the branch name in it, and it is rate limited. The Pages URL is on
our own domain and is served as `text/calendar`.

How quickly subscribers see a change is up to their client, not us: Apple
Calendar lets the subscriber pick (five minutes to a day), Outlook re-reads
every few hours, and Google Calendar refreshes on its own schedule, which can
be up to a day and cannot be forced. The feed asks for hourly refreshes via
`REFRESH-INTERVAL`, which Apple and Outlook honour. In other words this is
right for a weekly seminar, but do not count on a subscriber seeing a room
change made an hour before the talk.

Each event carries the talk's title and speaker, the abstract, the location and
Zoom link, its tags as categories, and a link back to the talk page. Canceled
talks stay in the feed marked `STATUS:CANCELLED`, which is how a subscriber's
calendar learns that a talk is off.

One thing that does *not* work, in case it comes up: subscribing to this feed
in Google Calendar and then sharing that calendar onward. A calendar added
"from URL" is private to the account that added it -- Google offers no sharing
settings for it at all. The `.ics` URL is the thing to share; it is the same
link for everyone and needs no account.

If the goal is instead to keep the existing shared Google Calendar in step with
these records (so people who already have that calendar keep it), that takes
the Google Calendar API: a service account, the calendar shared with that
account's address, its key in a repository secret, and a workflow that upserts
each record as an event keyed by `iCalUID`. That is a bigger change and it
makes this repository the source of truth for the calendar -- edits made in
Google Calendar would be overwritten on the next sync.

#### The calendar view

The calendar on the seminar page (`_includes/full_calendar.html`) is
[FullCalendar](https://fullcalendar.io/), which the repository already vendors
under `assets/fullcalendar-4.3.1/`. It reads `talks.json` -- a FullCalendar
event feed written by the same generator as everything else -- so the calendar,
the talk pages, and the `.ics` feed can never disagree. It offers an 8-week
list, a year list, and a month grid; clicking an event opens that talk's page.

It used to read the Google Calendar through the Google Calendar API, with an
API key committed in the include. That key, the `google-calendar` plugin, and
`assets/js/fetchGoogleCalendar.js` are all gone: nothing on the site calls
Google any more.

#### Backfilling records (one-off, not the daily sync)

`scripts/import_calendar_talks.py`, run without `--sync`, is the original
seeding mode: it reads the calendar's full history and writes a TOML record
for every entry that does not already have one, using the same best-effort
heuristics as the `--sync` fallback path (see above). Useful for a one-time
backfill, never for keeping the window in sync (that is what `--sync` and
`sync-talks.yml` are for):

```shell
make import-talks             # or: python3 scripts/import_calendar_talks.py
```

Old calendar descriptions are free-form, so this is best effort -- imported
records are marked `needs_review = true` under `[meta]` and should be checked
(titles, affiliations, and abstracts especially) before they are considered
final. It never overwrites an existing file unless you pass `--overwrite`.

### progrmas
Add/delete/edit .md files in `_progrmas` folder to add/delete/edit members.

## Page header
* header:
  * title: Header Title, default: None
  * title-color: white|red, default: white
  * excerpt: >  
        Excerpt to show under title, default: None
  * excerpt-color: white|black, default: white
  * align: center|left, default: center
  * background-image: default: /assets/img/header-background/zion-shorter.jpg

## Layout
* home
  Designed for landing page, does not defined a content box.
* single
  Designed for content page, predefined a content box to include all content in a white backgound card.
  
## Scheduling Website Changes

You can schedule a website change to occur at 00:01 any day by doing the following:

1. Create a branch where you will make your changes.
2. On your branch, make your changes and test them.
3. Once you’re ready, you need to submit a Pull Request. At the very bottom of your Pull Request description, add `/schedule yyyy-mm-dd`. Your change will be merged to master at ~12:01 am on this date.

This scheduler is implemented using the Merge Schedule GitHub Action. More information on this can be found [here](https://github.com/marketplace/actions/merge-schedule).