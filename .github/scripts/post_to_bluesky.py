#!/usr/bin/env python3
"""
Script to fetch the next Utah Data Science Center event from Google Calendar
and post it to Bluesky.
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime, timezone
from dateutil import parser
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BlueSkyPoster:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = None
        self.base_url = "https://bsky.social"
        
    def authenticate(self):
        """Authenticate with Bluesky and get session token"""
        try:
            auth_url = f"{self.base_url}/xrpc/com.atproto.server.createSession"
            auth_data = {
                "identifier": self.username,
                "password": self.password
            }
            
            response = requests.post(auth_url, json=auth_data)
            response.raise_for_status()
            
            self.session = response.json()
            logger.info("Successfully authenticated with Bluesky")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to authenticate with Bluesky: {e}")
            return False
    
    def post_message(self, message):
        """Post a message to Bluesky"""
        if not self.session:
            logger.error("Not authenticated. Call authenticate() first.")
            return False
            
        try:
            post_url = f"{self.base_url}/xrpc/com.atproto.repo.createRecord"
            headers = {
                "Authorization": f"Bearer {self.session['accessJwt']}",
                "Content-Type": "application/json"
            }
            
            # Create the post record
            now = datetime.now(timezone.utc).isoformat()
            post_data = {
                "repo": self.session["did"],
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": message,
                    "createdAt": now
                }
            }
            
            response = requests.post(post_url, headers=headers, json=post_data)
            response.raise_for_status()
            
            logger.info("Successfully posted to Bluesky")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post to Bluesky: {e}")
            return False

class GoogleCalendarFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.calendar_id = "ekol7ulqm14nv155angut2rlfo@group.calendar.google.com"
        
    def get_next_event(self):
        """Fetch the next upcoming event from the Google Calendar"""
        try:
            # Current time in ISO format
            time_min = datetime.now(timezone.utc).isoformat()
            
            url = "https://www.googleapis.com/calendar/v3/calendars/{}/events".format(self.calendar_id)
            params = {
                "key": self.api_key,
                "timeMin": time_min,
                "maxResults": 1,
                "singleEvents": True,
                "orderBy": "startTime"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            events = data.get("items", [])
            
            if not events:
                logger.warning("No upcoming events found")
                return None
                
            event = events[0]
            logger.info(f"Found next event: {event.get('summary', 'Unknown')}")
            return event
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch calendar events: {e}")
            return None

def format_event_message(event):
    """Format the event data into a Bluesky post message"""
    if not event:
        return "Join us for our next Utah Data Science Center event! Check our website for details: https://datascience.utah.edu/seminar"
    
    # Extract event details
    title = event.get("summary", "Utah Data Science Event")
    description = event.get("description", "")
    location = event.get("location", "")
    html_link = event.get("htmlLink", "")
    
    # Parse start time
    start_time = None
    if "start" in event:
        if "dateTime" in event["start"]:
            start_time = parser.parse(event["start"]["dateTime"])
        elif "date" in event["start"]:
            start_time = parser.parse(event["start"]["date"])
    
    # Format the message
    message_parts = ["🔬 Join us for our next Utah Data Science Center event!"]
    
    message_parts.append(f"\n📅 {title}")
    
    if start_time:
        formatted_time = start_time.strftime("%A, %B %d at %I:%M %p")
        message_parts.append(f"\n⏰ {formatted_time}")
    
    if location and location.strip():
        message_parts.append(f"\n📍 {location}")
    
    # Add a brief description if available (truncated for length)
    if description and description.strip():
        # Remove markdown and HTML tags for a cleaner description
        clean_desc = description.replace("*", "").replace("**", "").replace("#", "")
        # Take first sentence or first 100 characters
        if len(clean_desc) > 100:
            clean_desc = clean_desc[:100] + "..."
        message_parts.append(f"\n\n{clean_desc}")
    
    message_parts.append(f"\n\n🔗 More info: https://datascience.utah.edu/seminar")
    
    if html_link:
        message_parts.append(f"\n📅 Calendar: {html_link}")
    
    message_parts.append("\n\n#DataScience #Utah #AI #MachineLearning")
    
    return "".join(message_parts)

def main():
    """Main function to orchestrate the calendar fetch and Bluesky post"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Post Utah Data Science Center events to Bluesky")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Generate and display the message without posting to Bluesky")
    args = parser.parse_args()
    
    # Get environment variables
    bluesky_username = os.getenv("BLUESKY_USERNAME")
    bluesky_password = os.getenv("BLUESKY_PASSWORD")
    google_api_key = os.getenv("GOOGLE_CALENDAR_API_KEY")
    
    # In dry-run mode, we don't need Bluesky credentials
    if not args.dry_run and (not bluesky_username or not bluesky_password):
        logger.warning("Bluesky credentials not provided. Skipping post.")
        logger.info("This is expected until the Bluesky credentials are added to GitHub secrets.")
        logger.info("To add credentials, set BLUESKY_USERNAME and BLUESKY_PASSWORD in GitHub repository secrets.")
        return
    
    # Use the hardcoded API key if not provided as secret (fallback to existing key)
    if not google_api_key:
        google_api_key = "AIzaSyBq6TTVUkWGCs0vmGh1XlIuGn0w5dCtbsA"
        logger.info("Using fallback Google Calendar API key")
    
    # Fetch the next event
    calendar_fetcher = GoogleCalendarFetcher(google_api_key)
    next_event = calendar_fetcher.get_next_event()
    
    # Format the message
    message = format_event_message(next_event)
    
    if args.dry_run:
        logger.info("DRY RUN MODE - Message would be posted to Bluesky:")
        print("\n" + "="*60)
        print("BLUESKY POST PREVIEW")
        print("="*60)
        print(message)
        print("="*60)
        logger.info("Dry run completed successfully")
        return
    
    logger.info(f"Formatted message: {message}")
    
    # Post to Bluesky
    poster = BlueSkyPoster(bluesky_username, bluesky_password)
    
    if poster.authenticate():
        success = poster.post_message(message)
        if success:
            logger.info("Successfully completed Bluesky post workflow")
        else:
            logger.error("Failed to post message to Bluesky")
            sys.exit(1)
    else:
        logger.error("Failed to authenticate with Bluesky")
        sys.exit(1)

if __name__ == "__main__":
    main()