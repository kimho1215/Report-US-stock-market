from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(video_id):
    try:
        print(f"Fetching transcript for video ID: {video_id}")
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        # Try to find Korean or English
        try:
            t = transcript_list.find_transcript(['ko', 'en'])
            print(f"Found transcript in language: {t.language}")
        except:
            t = next(iter(transcript_list))
            print(f"Fallback to first available transcript: {t.language}")
        data = t.fetch()
        text = " ".join([i['text'] for i in data])
        print(f"Length: {len(text)}")
        return text
    except Exception as e:
        print(f"Error: {e}")
        return None

# Test with first video from videos.json
get_transcript("hyAp2186UfM")
