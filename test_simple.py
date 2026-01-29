from youtube_transcript_api import YouTubeTranscriptApi

try:
    print("Testing get_transcript...")
    # Using a common video ID
    transcript = YouTubeTranscriptApi.get_transcript("hyAp2186UfM", languages=['ko', 'en'])
    print(f"Success! Length: {len(transcript)}")
except Exception as e:
    print(f"Error: {e}")
