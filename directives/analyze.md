# Directive: Analyze 3pro TV for Stock Recommendations

## Goal
Identify investment recommendations for US/Korea stocks from "3pro TV" YouTube videos uploaded in the last 24 hours, and compile them into a Google Slides presentation sent via email.

## Workflow Status
- **Trigger**: Schedule (e.g., daily at 8 AM) or Manual run.
- **Inputs**: None.

## Steps

### 1. Find Recent Videos
- **Tool**: `execution/get_recent_videos.py`
- **Output**: `.tmp/videos.json`
- **Logic**:
    - Search YouTube for channel "3pro TV".
    - Filter for videos published in the last 24 hours.
    - Save video ID, Title, and PublishedTime.

### 2. Analyze Content
- **Tool**: `execution/extract_recommendations.py`
- **Input**: `.tmp/videos.json`
- **Output**: `.tmp/analysis_results.json`
- **Logic**:
    - For each video, fetch Transcript.
    - If no transcript, skip.
    - Use LLM to Process transcript:
        - Identify segments proposing specific stocks.
        - Extract: Speaker, Time, Market (US/KR), Reasoning, Stock Name.
        - Filter out general market commentary; focus on *actionable* advice or strong opinions.
    - Structure data into JSON.

### 3. Generate Presentation
- **Tool**: `execution/create_slides.py`
- **Input**: `.tmp/analysis_results.json`
- **Output**: `.tmp/slide_link.json` containing `{"url": "..."}`
- **Logic**:
    - Create a new Google Slide deck "3pro TV Stock Analysis [Date]".
    - For each recommendation item in JSON:
        - Create 1 Slide.
        - Title: [Stock Name] - [Market]
        - Body:
            - **Who**: [Speaker]
            - **Why**: [Reasoning]
            - **When**: [Time context] from video

### 4. Notify User
- **Tool**: `execution/send_email.py`
- **Input**: `.tmp/slide_link.json`
- **Logic**:
    - Send email to the user with the link to the slides.

## Edge Cases
- No videos in 24h: Exit gracefully.
- No recommendations found: Send email stating "No recommendations found".
- API Quota exceeded: Log error and fail.
