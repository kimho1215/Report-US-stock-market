from youtube_transcript_api import YouTubeTranscriptApi

video_id = "foqCjCwvpNo"
try:
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    print(f"Available transcripts for {video_id}:")
    for t in transcript_list:
        print(f" - {t.language_code} (auto-generated: {t.is_generated})")
    
    # Try picking the first one
    t = transcript_list.find_transcript(['ko', 'en'])
    print(f"Success! Fetched {t.language_code}")
except Exception as e:
    print(f"Failed: {e}")
