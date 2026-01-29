from youtube_transcript_api import YouTubeTranscriptApi

video_id = "hyAp2186UfM"
try:
    print(f"Testing new API for {video_id}...")
    # Based on search result: YouTubeTranscriptApi().list(video_id) or similar
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)
    
    print("Available transcripts:")
    for t in transcript_list:
        print(f" - {t.language_code} (auto-generated: {t.is_generated})")
        
    # Example fetch
    transcript = transcript_list.find_transcript(['ko', 'en'])
    data = transcript.fetch()
    print(f"Success! Length: {len(data)} items")
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()
