import os
import sys
import json
import argparse
import google.generativeai as genai
import time
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

# Force UTF-8 encoding for stdout/stderr
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

def log(msg, debug=False):
    if debug:
        print(f"[DEBUG] {msg}")

# Setup Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_transcript(video_id, debug=False):
    try:
        log(f"Fetching transcript for video ID: {video_id}", debug)
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id, languages=['ko', 'en'])
        text = " ".join([t.text for t in transcript_list])
        log(f"Transcript fetched successfully ({len(text)} chars)", debug)
        return text
    except Exception as e:
        log(f"Could not get transcript for {video_id}: {e}", debug)
        return None

def analyze_transcript(text, video_title, debug=False):
    log(f"Analyzing transcript with Gemini for: {video_title}", debug)
    prompt = f"""
    Analyze the following YouTube video transcript titled "{video_title}".
    Identify any specific investment recommendations for US or Korean stocks.
    
    Structure your answer strictly as a JSON object with a key "recommendations" which is a list of objects. 
    Each object in the list must have:
    - "stock_name": Name of the stock
    - "market": "US" or "KR"
    - "speaker": Who is recommending (if identifiable, else "Analyst")
    - "action": "Buy" or "Sell" or "Hold"
    - "reasoning": Why they recommend it (brief summary)
    - "time_context": approximate time in video or "General"
    
    If there are no clear recommendations, return {{"recommendations": []}}.
    
    Transcript:
    {text[:30000]} 
    """ 

    try:
        log("Sending request to Gemini...", debug)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            ),
        )
        log("Received response from Gemini.", debug)
        
        result_json = json.loads(response.text)
        return result_json.get("recommendations", [])
        
    except Exception as e:
        log(f"Error analyzing with Gemini: {e}", debug)
        print(f"Error analyzing with Gemini: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Extract recommendations from transcripts.')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    debug = args.debug

    log("Script started.", debug)

    if not os.path.exists('.tmp/videos.json'):
        print("No videos found. Run get_recent_videos.py first.")
        return

    log("Reading .tmp/videos.json...", debug)
    with open('.tmp/videos.json', 'r', encoding='utf-8') as f:
        videos = json.load(f)

    all_recommendations = []
    log(f"Found {len(videos)} videos to process.", debug)

    for video in videos:
        print(f"Processing {video['title']}...")
        transcript = get_transcript(video['id'], debug)
        if transcript:
            recs = analyze_transcript(transcript, video['title'], debug)
            if recs:
                print(f"Found {len(recs)} recommendations.")
                log(f"Recommendations: {recs}", debug)
                for r in recs:
                    r['video_title'] = video['title']
                    r['video_id'] = video['id']
                    all_recommendations.append(r)
            else:
                log("No recommendations found in this video.", debug)
        else:
            print("Skipping (no transcript).")

    # Output results
    log("Writing results to .tmp/analysis_results.json...", debug)
    os.makedirs('.tmp', exist_ok=True)
    with open('.tmp/analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_recommendations, f, ensure_ascii=False, indent=2)
    
    print(f"Total recommendations saved: {len(all_recommendations)}")
    log("Script finished.", debug)

if __name__ == "__main__":
    main()
