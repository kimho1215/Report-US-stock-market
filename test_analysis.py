import os
import sys
import json
from execution.extract_recommendations import analyze_transcript, get_transcript
from dotenv import load_dotenv

load_dotenv()

video = {
    "id": "foqCjCwvpNo",
    "title": "3배로 오릅니다! 코스피 5000은 못 믿었어도 코스닥 3000은 풀악셀 [야식잡썰 EP.254] / 이대호 기자",
    "tags": ["삼성전자", "SK하이닉스", "알테오젠", "마이크론", "반도체", "바이오", "로봇"],
    "description": "3배로 오릅니다! 코스피 5000은 못 믿었어도 코스닥 3000은 풀악셀 [야식잡썰 EP.254]\n00:00 코스닥 3000은 풀악셀\n09:16 반등의 시간\n13:59 3배 오릅니다!"
}

print(f"Testing {video['title']}...")
tags_str = ", ".join(video.get('tags', []))
analysis_input = f"Title: {video['title']}\nTags: {tags_str}\nDescription: {video['description']}"

recs = analyze_transcript(analysis_input, video['title'], debug=True)
print(f"Found {len(recs)} recommendations:")
for r in recs:
    print(f" - {r['stock_name']} ({r['market']}): {r['action']} - {r['reasoning']}")
