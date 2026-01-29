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
    if os.path.exists('token_slides.json'):
        log("Found token_slides.json, loading credentials...", debug)
        try:
            creds = Credentials.from_authorized_user_file('token_slides.json', SCOPES)
        except:
            creds = None
    if not creds or not creds.valid:
        log("Credentials invalid or expired.", debug)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token_slides.json', 'w') as token:
            token.write(creds.to_json())
    return build('slides', 'v1', credentials=creds)

def main():
    parser = argparse.ArgumentParser(description='Create Google Slides.')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    debug = args.debug

    log("Script started.", debug)

    # 1. Load analysis results
    recommendations = []
    if os.path.exists('.tmp/analysis_results.json'):
        with open('.tmp/analysis_results.json', 'r', encoding='utf-8') as f:
            recommendations = json.load(f)

    # 2. Setup Slides Service
    service = get_service(debug)

    # 3. Handle Presentation ID (Existing or New)
    presentation_id = None
    if os.path.exists('.tmp/slide_link.json'):
        try:
            with open('.tmp/slide_link.json', 'r', encoding='utf-8') as f:
                presentation_id = json.load(f).get('id')
            # Verify it exists on Drive
            service.presentations().get(presentationId=presentation_id).execute()
            log(f"Using existing presentation: {presentation_id}", debug)
        except:
            presentation_id = None

    if not presentation_id:
        title = "3pro TV Stock Analysis Report"
        presentation = service.presentations().create(body={'title': title}).execute()
        presentation_id = presentation.get('presentationId')
        log(f"Created new presentation: {presentation_id}", debug)

    # 4. Prepare Metadata
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    channels = ["삼프로TV", "언더스탠딩", "와이스트릿"]
    summary_title = f"Report: {date_str} {time_str}"

    # 5. Batch Update Requests (Insert at Top with Styling)
    requests = []
    
    # RGB Values (normalized 0-1)
    RGB_BG = {'red': 0.11, 'green': 0.11, 'blue': 0.11} # #1C1C1C
    RGB_TITLE = {'red': 1.0, 'green': 1.0, 'blue': 1.0} # White
    RGB_ACCENT = {'red': 0.29, 'green': 0.61, 'blue': 1.0} # #4B9BFF
    RGB_TEXT = {'red': 0.8, 'green': 0.8, 'blue': 0.8} # Light Gray

    # Helper for Solid Fill (Background)
    def solid_fill(rgb): return {'solidFill': {'color': {'rgbColor': rgb}}}
    
    # Helper for Opaque Color (Text)
    def text_style(rgb, bold=False, size=None):
        style = {'foregroundColor': {'opaqueColor': {'rgbColor': rgb}}, 'bold': bold}
        if size: style['fontSize'] = {'magnitude': size, 'unit': 'PT'}
        return style

    # A. Create Summary Slide
    summary_id = f'summary_{date_str.replace("-","")}_{now.strftime("%H%M%S")}'
    requests.append({
        'createSlide': {
            'objectId': summary_id,
            'insertionIndex': 0,
            'slideLayoutReference': {'predefinedLayout': 'TITLE_AND_BODY'}
        }
    })
    # Set Summary Background
    requests.append({
        'updatePageProperties': {
            'objectId': summary_id,
            'pageProperties': {'pageBackgroundFill': solid_fill(RGB_BG)},
            'fields': 'pageBackgroundFill'
        }
    })
    
    # B. Add Recommendation Slides (or No Result slide)
    new_slide_ids = []
    if not recommendations:
        no_data_id = f'no_data_{now.strftime("%H%M%S")}'
        requests.append({
            'createSlide': {
                'objectId': no_data_id,
                'insertionIndex': 1,
                'slideLayoutReference': {'predefinedLayout': 'TITLE_AND_BODY'}
            }
        })
        requests.append({
            'updatePageProperties': {
                'objectId': no_data_id,
                'pageProperties': {'pageBackgroundFill': solid_fill(RGB_BG)},
                'fields': 'pageBackgroundFill'
            }
        })
        new_slide_ids.append(no_data_id)
    else:
        # Group recommendations by video_id
        grouped_recs = {}
        for rec in recommendations:
            v_id = rec.get('video_id', 'unknown')
            if v_id not in grouped_recs:
                grouped_recs[v_id] = {
                    'video_title': rec.get('video_title', 'Unknown Video'),
                    'items': []
                }
            grouped_recs[v_id]['items'].append(rec)

        # Create slides per video, splitting into multiple pages if many items
        ITEMS_PER_PAGE = 5
        for i, (v_id, data) in enumerate(reversed(list(grouped_recs.items()))):
            items = data['items']
            # Split items into chunks
            chunks = [items[j:j + ITEMS_PER_PAGE] for j in range(0, len(items), ITEMS_PER_PAGE)]
            
            # Reverse the chunks so that when we insert at index 1, the first chunk ends up at the top
            for chunk_idx, chunk in reversed(list(enumerate(chunks))):
                suffix = f" ({chunk_idx + 1}/{len(chunks)})" if len(chunks) > 1 else ""
                slide_id = f'v_rec_{i}_{chunk_idx}_{now.strftime("%H%M%S")}'
                requests.append({
                    'createSlide': {
                        'objectId': slide_id,
                        'insertionIndex': 1,
                        'slideLayoutReference': {'predefinedLayout': 'TITLE_AND_BODY'}
                    }
                })
                requests.append({
                    'updatePageProperties': {
                        'objectId': slide_id,
                        'pageProperties': {'pageBackgroundFill': solid_fill(RGB_BG)},
                        'fields': 'pageBackgroundFill'
                    }
                })
                new_slide_ids.append((slide_id, {
                    'video_title': data['video_title'] + suffix,
                    'items': chunk
                }))

    # Execute Slide Creation
    log("Creating new slides with premium theme...", debug)
    response = service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': requests}).execute()
    
    # 6. Populate Content & Style Text
    text_requests = []
    pres = service.presentations().get(presentationId=presentation_id).execute()
    slides = pres.get('slides', [])
    
    def get_placeholders(slide_obj):
        t_id, b_id = None, None
        for element in slide_obj.get('pageElements', []):
            if 'shape' in element and 'placeholder' in element['shape']:
                p_type = element['shape']['placeholder']['type']
                if p_type == 'TITLE': t_id = element['objectId']
                elif p_type == 'BODY': b_id = element['objectId']
        return t_id, b_id

    # Populate Summary
    summary_slide = next(s for s in slides if s['objectId'] == summary_id)
    t_id, b_id = get_placeholders(summary_slide)
    if t_id: 
        text_requests.append({'insertText': {'objectId': t_id, 'text': summary_title}})
        text_requests.append({'updateTextStyle': {'objectId': t_id, 'style': text_style(RGB_ACCENT, True, 36), 'fields': 'foregroundColor,bold,fontSize'}})
    if b_id: 
        # Add extra newlines at the start to push content down and avoid overlap with title
        status_text = f"\n\nChannels: {', '.join(channels)}\nStatus: {'Success - Recommendations found' if recommendations else 'No data found'}"
        text_requests.append({'insertText': {'objectId': b_id, 'text': status_text}})
        text_requests.append({'updateTextStyle': {'objectId': b_id, 'style': text_style(RGB_TEXT, False, 18), 'fields': 'foregroundColor,fontSize'}})

    # Populate Recommendations or No Data
    if not recommendations:
        no_data_slide = next(s for s in slides if s['objectId'] == new_slide_ids[0])
        t_id, b_id = get_placeholders(no_data_slide)
        if t_id: 
            text_requests.append({'insertText': {'objectId': t_id, 'text': "Today's Result"}})
            text_requests.append({'updateTextStyle': {'objectId': t_id, 'style': text_style(RGB_TITLE, True), 'fields': 'foregroundColor,bold'}})
        if b_id: 
            text_requests.append({'insertText': {'objectId': b_id, 'text': "조건에 맞는 추천 종목이 없습니다."}})
            text_requests.append({'updateTextStyle': {'objectId': b_id, 'style': text_style(RGB_TEXT), 'fields': 'foregroundColor'}})
    else:
        # Action Icons
        icons = {"Buy": "🚀", "Sell": "📉", "Hold": "⚖️", "Wait": "⏳", "Watch": "👀"}

        for slide_id, data in new_slide_ids:
            target_slide = next(s for s in slides if s['objectId'] == slide_id)
            t_id, b_id = get_placeholders(target_slide)
            
            if t_id:
                clean_title = data['video_title']
                if len(clean_title) > 70: clean_title = clean_title[:67] + "..."
                text_requests.append({'insertText': {'objectId': t_id, 'text': clean_title}})
                text_requests.append({'updateTextStyle': {'objectId': t_id, 'style': text_style(RGB_ACCENT, True, 16), 'fields': 'foregroundColor,bold,fontSize'}})
            
            if b_id:
                body_content = ""
                for item in data['items']:
                    action = item.get('action', 'N/A')
                    icon = icons.get(action, "📌")
                    market = f"[{item.get('market', '')}]" if item.get('market') else ""
                    stock = item.get('stock_name', 'N/A')
                    body_content += f"{icon} {stock} {market} ({action})\n"
                    
                    reason = item.get('reasoning', '')
                    if len(reason) > 110: reason = reason[:107] + "..."
                    body_content += f"      └ {reason} [{item.get('speaker', 'Analyst')}]\n"
                
                text_requests.append({'insertText': {'objectId': b_id, 'text': body_content}})
                text_requests.append({'updateTextStyle': {'objectId': b_id, 'style': text_style(RGB_TEXT, False, 10), 'fields': 'foregroundColor,fontSize'}})

    if text_requests:
        service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': text_requests}).execute()

    # 7. Retention Policy: Keep only last 30 daily reports
    log("Checking retention policy (30 days)...", debug)
    pres = service.presentations().get(presentationId=presentation_id).execute()
    current_slides = pres.get('slides', [])
    
    summary_indices = []
    for i, s in enumerate(current_slides):
        # We identify summary slides by their objectId prefix
        if s['objectId'].startswith('summary_'):
            summary_indices.append(i)
    
    if len(summary_indices) > 30:
        delete_from_index = summary_indices[30]
        log(f"Retention: Deleting slides from index {delete_from_index} onwards.", debug)
        delete_requests = []
        for s in current_slides[delete_from_index:]:
            delete_requests.append({'deleteObject': {'objectId': s['objectId']}})
        if delete_requests:
            service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': delete_requests}).execute()

    # 8. Save/Update link
    presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
    print(f"Slides updated: {presentation_url}")
    with open('.tmp/slide_link.json', 'w', encoding='utf-8') as f:
        json.dump({"url": presentation_url, "id": presentation_id, "title": "3pro TV Stock Analysis Report"}, f)

if __name__ == "__main__":
    main()
