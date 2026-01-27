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
    if os.path.exists('token_youtube.json'):
        try:
            creds = Credentials.from_authorized_user_file('token_youtube.json', SCOPES)
        except Exception:
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token_youtube.json', 'w') as token:
            token.write(creds.to_json())

    return build('youtube', 'v3', credentials=creds)

def main():
    parser = argparse.ArgumentParser(description='Fetch recent YouTube videos.')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    debug = args.debug

    service = get_service(debug)

    now = datetime.datetime.now(datetime.timezone.utc)
    published_after = (now - datetime.timedelta(hours=36)).isoformat().replace("+00:00", "Z")
    published_before = (now - datetime.timedelta(hours=12)).isoformat().replace("+00:00", "Z")

    search_queries = ["삼프로TV", "언더스탠딩", "와이스트릿"]
    
    found_video_ids = []
    seen_ids = set()

    for query in search_queries:
        print(f"Searching for '{query}' videos...")
        try:
            request = service.search().list(
                part="snippet",
                q=query, 
                type="video",
                publishedAfter=published_after,
                publishedBefore=published_before,
                maxResults=10,
                order="date"
            )
            response = request.execute()
            
            allowed_keywords = ["삼프로", "언더스탠딩", "와이스트릿"]
            blacklist_keywords = ["하나님 나라", "Hacks Hub", "Smart English"]

            for item in response.get('items', []):
                video_id = item['id']['videoId']
                channel_title = item['snippet']['channelTitle']
                
                is_target = any(k in channel_title for k in allowed_keywords)
                is_blacklisted = any(k in channel_title for k in blacklist_keywords)
                
                if video_id not in seen_ids and is_target and not is_blacklisted:
                    found_video_ids.append(video_id)
                    seen_ids.add(video_id)
        except Exception as e:
            print(f"Error searching for {query}: {e}")

    # Fetch detailed info for all found videos
    videos = []
    if found_video_ids:
        print(f"Fetching details for {len(found_video_ids)} videos...")
        # Process in batches of 50 (API limit)
        for i in range(0, len(found_video_ids), 50):
            batch_ids = found_video_ids[i:i+50]
            try:
                request = service.videos().list(
                    part="snippet,contentDetails,topicDetails",
                    id=",".join(batch_ids)
                )
                response = request.execute()
                for item in response.get('items', []):
                    snippet = item.get('snippet', {})
                    videos.append({
                        'id': item['id'],
                        'title': snippet.get('title'),
                        'description': snippet.get('description'),
                        'tags': snippet.get('tags', []),
                        'publishedAt': snippet.get('publishedAt'),
                        'channelTitle': snippet.get('channelTitle'),
                        'category': snippet.get('categoryId')
                    })
            except Exception as e:
                print(f"Error fetching details: {e}")

    os.makedirs('.tmp', exist_ok=True)
    with open('.tmp/videos.json', 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

    print(f"Saved total {len(videos)} videos with full details to .tmp/videos.json")

if __name__ == "__main__":
    main()
