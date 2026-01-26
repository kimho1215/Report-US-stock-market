import os
import sys
import json
import datetime
import argparse

# Force UTF-8 encoding for stdout/stderr
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/presentations', 'https://www.googleapis.com/auth/drive']

def log(msg, debug=False):
    if debug:
        print(f"[DEBUG] {msg}")

def get_service(debug=False):
    log("Initializing Slides Service...", debug)
    creds = None
    if os.path.exists('token.json'):
        log("Found token.json, loading credentials...", debug)
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except:
            creds = None
    if not creds or not creds.valid:
        log("Credentials invalid or expired.", debug)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('slides', 'v1', credentials=creds)

def main():
    parser = argparse.ArgumentParser(description='Create Google Slides.')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    debug = args.debug

    log("Script started.", debug)

    if not os.path.exists('.tmp/analysis_results.json'):
        print("No analysis results found.")
        return

    log("Reading .tmp/analysis_results.json...", debug)
    with open('.tmp/analysis_results.json', 'r', encoding='utf-8') as f:
        recommendations = json.load(f)

    if not recommendations:
        print("No recommendations to present.")
        return

    service = get_service(debug)

    # Create presentation
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    title = f"3pro TV Stock Analysis - {date_str}"
    body = {'title': title}
    log(f"Creating presentation: {title}", debug)
    presentation = service.presentations().create(body=body).execute()
    presentation_id = presentation.get('presentationId')
    print(f"Created presentation with ID: {presentation_id}")

    # Add slides
    log(f"Adding {len(recommendations)} slides...", debug)
    
    for i, rec in enumerate(recommendations):
        log(f"Creating slide {i+1} for {rec['stock_name']}...", debug)
        # Create slide
        res = service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': [{'createSlide': {'slideLayoutReference': {'predefinedLayout': 'TITLE_AND_BODY'}}}]}
        ).execute()
        
        slide_id = res['replies'][0]['createSlide']['objectId']
        log(f"Slide created with ID: {slide_id}", debug)
        
        # Get placeholders (Title and Body)
        slide = service.presentations().pages().get(presentationId=presentation_id, pageObjectId=slide_id).execute()
        title_id = None
        body_id = None
        
        for element in slide.get('pageElements', []):
            if 'shape' in element and 'placeholder' in element['shape']:
                type_ = element['shape']['placeholder']['type']
                if type_ == 'TITLE':
                    title_id = element['objectId']
                elif type_ == 'BODY':
                    body_id = element['objectId']
        
        # Requests to populate text
        text_requests = []
        if title_id:
            text_requests.append({
                'insertText': {
                    'objectId': title_id,
                    'text': f"{rec['stock_name']} ({rec['market']})"
                }
            })
        if body_id:
            content = f"Action: {rec.get('action', 'N/A')}\n" \
                      f"Who: {rec.get('speaker', 'Unknown')}\n" \
                      f"Why: {rec.get('reasoning', '')}\n" \
                      f"Context: {rec.get('time_context', '')}\n" \
                      f"Source: {rec.get('video_title', '')}"
            text_requests.append({
                'insertText': {
                    'objectId': body_id,
                    'text': content
                }
            })
            
        if text_requests:
            log("Inserting text content...", debug)
            service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': text_requests}).execute()

    # Save link
    presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
    print(f"Slides created: {presentation_url}")
    
    with open('.tmp/slide_link.json', 'w', encoding='utf-8') as f:
        json.dump({"url": presentation_url, "id": presentation_id, "title": title}, f)
    
    log("Script finished.", debug)

if __name__ == "__main__":
    main()
