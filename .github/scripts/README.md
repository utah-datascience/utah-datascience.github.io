# Bluesky Posting Workflow

This directory contains the GitHub Actions workflow and script for automatically posting Utah Data Science Center events to Bluesky.

## How it works

1. **Schedule**: The workflow runs twice a week:
   - Mondays at 9:00 AM MST
   - Wednesdays at 8:00 AM MST

2. **Data Source**: The script fetches the next upcoming event from the Utah Data Science Center Google Calendar (calendar ID: `ekol7ulqm14nv155angut2rlfo@group.calendar.google.com`)

3. **Posting**: It formats the event information into a social media-friendly message and posts it to Bluesky using the AT Protocol

## Setup Instructions

### Required GitHub Secrets

To enable Bluesky posting, add the following secrets to your GitHub repository:

1. Go to your repository Settings → Secrets and variables → Actions
2. Add these repository secrets:
   - `BLUESKY_USERNAME`: Your Bluesky handle (e.g., `username.bsky.social`)
   - `BLUESKY_PASSWORD`: Your Bluesky app password (not your regular password!)

### Creating a Bluesky App Password

1. Log in to Bluesky
2. Go to Settings → App Passwords
3. Create a new app password for "GitHub Actions Bot" 
4. Use this app password (not your regular password) as `BLUESKY_PASSWORD`

### Optional Secrets

- `GOOGLE_CALENDAR_API_KEY`: If you want to use a different Google Calendar API key (the script has a fallback to the existing key)

## Manual Testing

You can manually trigger the workflow by:
1. Going to the Actions tab in your repository
2. Selecting "Post to Bluesky"
3. Clicking "Run workflow"

## Files

- `bluesky-post.yml`: GitHub Actions workflow definition
- `post_to_bluesky.py`: Python script that handles calendar fetching and Bluesky posting
- `README.md`: This documentation file

## Message Format

The bot posts messages in this format:

```
🔬 Join us for our next Utah Data Science Center event!
📅 [Event Title]
⏰ [Day, Month Date at Time]
📍 [Location]

[Brief description...]

🔗 More info: https://datascience.utah.edu/seminar
📅 Calendar: [Google Calendar Link]

#DataScience #Utah #AI #MachineLearning
```

If no upcoming events are found, it posts a generic message directing people to the website.