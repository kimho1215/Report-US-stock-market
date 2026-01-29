from youtube_transcript_api import YouTubeTranscriptApi

video_id = "hyAp2186UfM"
try:
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)
    t = transcript_list.find_transcript(['ko'])
    data = t.fetch()
    print(f"Data type: {type(data)}")
    print(f"First item type: {type(data[0])}")
    print(f"First item attributes: {dir(data[0])}")
    # Try to access text
    try:
        print(f"Text via subscript: {data[0]['text']}")
    except Exception as e:
        print(f"Subscript failed: {e}")
    try:
        print(f"Text via attribute: {data[0].text}")
    except Exception as e:
        print(f"Attribute failed: {e}")
except Exception as e:
    print(f"Error: {e}")
