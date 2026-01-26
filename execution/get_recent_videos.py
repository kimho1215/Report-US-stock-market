import os
import sys
import datetime
import json
import argparse

# Force UTF-8 encoding for stdout/stderr
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Define scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

def log(msg, debug=False):
    if debug:
        print(f"[DEBUG] {msg}")

def get_service(debug=False):
    log("Initializing YouTube Service...", debug)
    creds = None
    if os.path.exists('token.json'):
        log("Found token.json, loading credentials...", debug)
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception as e:
            log(f"Error loading token.json: {e}", debug)
            creds = None
    
    if not creds or not creds.valid:
        log("Credentials invalid or expired.", debug)
        if creds and creds.expired and creds.refresh_token:
            log("Refleshing expired token...", debug)
            creds.refresh(Request())
        else:
            log("Starting OAuth flow...", debug)
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        log("Saving new credentials to token.json...", debug)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    log("Building YouTube service object...", debug)
    return build('youtube', 'v3', credentials=creds)

def main():
    parser = argparse.ArgumentParser(description='Fetch recent YouTube videos.')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    debug = args.debug

    log("Script started.", debug)
    service = get_service(debug)

    now = datetime.datetime.now(datetime.timezone.utc)
    one_day_ago = now - datetime.timedelta(hours=24)
    published_after = one_day_ago.isoformat().replace("+00:00", "Z")

    # List of channels/keywords to search for
    search_queries = ["삼프로TV", "언더스탠딩", "와이스트릿"]
    
    videos = []
    seen_ids = set()

    for query in search_queries:
        log(f"Searching for '{query}' videos published after {published_after}...", debug)
        print(f"Searching for '{query}' videos...")

        try:
            request = service.search().list(
                part="snippet",
                q=query, 
                type="video",
                publishedAfter=published_after,
                maxResults=20, # Reduced per query to balance quota
                order="date"
            )
            log(f"Executing search request for {query}...", debug)
            response = request.execute()
            log(f"Search request for {query} completed.", debug)
            
            items = response.get('items', [])
            log(f"Found {len(items)} items for '{query}'.", debug)

            for item in items:
                video_id = item['id']['videoId']
                if video_id not in seen_ids:
                    video_data = {
                        'id': video_id,
                        'title': item['snippet']['title'],
                        'publishedAt': item['snippet']['publishedAt'],
                        'channelTitle': item['snippet']['channelTitle']
                    }
                    videos.append(video_data)
                    seen_ids.add(video_id)
                    log(f"Processed video: {video_data['title']} ({video_data['id']})", debug)
                    print(f"Found: {video_data['title']} ({video_data['id']})")
        except Exception as e:
            print(f"Error during search for '{query}': {e}")
            continue

    log("Ensuring .tmp directory exists...", debug)
    os.makedirs('.tmp', exist_ok=True)
    
    log(f"Writing {len(videos)} total videos to .tmp/videos.json...", debug)
    with open('.tmp/videos.json', 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

    print(f"Saved total {len(videos)} videos to .tmp/videos.json")
    log("Script finished successfully.", debug)

if __name__ == "__main__":
    main()
