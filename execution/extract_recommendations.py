import os
import sys
import json
import argparse
import time
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Force UTF-8 encoding for stdout/stderr
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

def log(msg, debug=False):
    if debug:
        print(f"[DEBUG] {msg}")

# Setup Gemini with new SDK
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def get_transcript(video_id, debug=False):
    try:
        log(f"Fetching transcript for video ID: {video_id}", debug)
        try:
            # New instance-based API for version 1.2.x
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            try:
                t = transcript_list.find_transcript(['ko', 'en'])
            except:
                t = next(iter(transcript_list))
            data = t.fetch()
            text = " ".join([i.text for i in data])
            log(f"Transcript fetched successfully ({len(text)} chars)", debug)
            return text
        except Exception as e:
            log(f"Transcript retrieval failed: {e}", debug)
            return None
    except Exception as e:
        log(f"Error in get_transcript: {e}", debug)
        return None

def analyze_transcript(text, video_title, debug=False):
    log(f"Analyzing content with Gemini for: {video_title}", debug)
    prompt = f"""
    Analyze the following YouTube video content titled "{video_title}".
    Identify any specific investment recommendations for US or Korean stocks.
    
    Structure your answer strictly as a JSON object with a key "recommendations" which is a list of objects. 
    Each object in the list must have:
    - "stock_name": Name of the stock
    - "market": "US" or "KR"
    - "speaker": Who is recommending. IMPORTANT: If the person is Korean, use their Korean name in Hangeul (e.g., "김장열" instead of "Kim Jang-yeol"). If not identifiable, use "Analyst".
    - "action": "Buy" or "Sell" or "Hold"
    - "reasoning": Why they recommend it (brief summary, keep it concise)
    - "time_context": approximate time in video or "General"
    
    If there are no clear recommendations, return {{"recommendations": []}}.
    
    Content:
    {text[:300000]} 
    """ 

    max_retries = 3
    for attempt in range(max_retries):
        try:
            log(f"Sending request to Gemini (gemini-flash-latest) - Attempt {attempt+1}...", debug)
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            log("Received response from Gemini.", debug)
            
            result_json = json.loads(response.text)
            return result_json.get("recommendations", [])
            
        except Exception as e:
            if "429" in str(e):
                wait_time = 20 * (attempt + 1)
                log(f"Rate limited (429). Waiting {wait_time}s and retrying...", debug)
                time.sleep(wait_time)
            else:
                log(f"Error analyzing with Gemini: {e}", debug)
                print(f"Error analyzing with Gemini: {e}")
                break
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
    
    # Wait a bit before starting to avoid rate limit bursts
    time.sleep(5)

    # Process only top 20 videos to be safe with quota
    for video in videos[:20]:
        print(f"Processing {video['title']}...")
        transcript = get_transcript(video['id'], debug)
        
        analysis_input = ""
        input_type = ""
        
        if transcript:
            analysis_input = f"Transcript: {transcript}"
            input_type = "Transcript"
        else:
            print("  - Transcript not available. Using Tags and Description.")
            tags_str = ", ".join(video.get('tags', []))
            analysis_input = f"Title: {video.get('title', '')}\nTags: {tags_str}\nDescription: {video.get('description', '')}"
            input_type = "Tags/Description"

        recs = analyze_transcript(analysis_input, video['title'], debug)
        if recs:
            print(f"  - Found {len(recs)} recommendations using {input_type}.")
            for r in recs:
                r['video_title'] = video['title']
                r['video_id'] = video['id']
                r['source_type'] = input_type
                all_recommendations.append(r)
        else:
            print(f"  - No recommendations found in {input_type}.")
        
        # Consistent delay to avoid 429
        time.sleep(15)

    # Output results
    log("Writing results to .tmp/analysis_results.json...", debug)
    os.makedirs('.tmp', exist_ok=True)
    with open('.tmp/analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_recommendations, f, ensure_ascii=False, indent=2)
    
    print(f"Total recommendations saved: {len(all_recommendations)}")
    log("Script finished.", debug)

if __name__ == "__main__":
    main()
