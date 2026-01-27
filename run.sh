#!/bin/bash

# US Stock Market Report - Automation Script
# This script executes the following steps:
# 1. Fetch recent videos from target YouTube channels
# 2. Extract stock recommendations using Gemini AI
# 3. Create/Update Google Slides with the analysis
# 4. Send the slide link via email

echo "Step 1: Fetching recent YouTube videos..."
python execution/get_recent_videos.py
if [ $? -ne 0 ]; then
    echo "Error in Step 1. Exiting."
    exit 1
fi

echo "Step 2: Extracting recommendations using Gemini AI..."
python execution/extract_recommendations.py
if [ $? -ne 0 ]; then
    echo "Error in Step 2. Exiting."
    exit 1
fi

echo "Step 3: Creating/Updating Google Slides..."
python execution/create_slides.py
if [ $? -ne 0 ]; then
    echo "Error in Step 3. Exiting."
    exit 1
fi

echo "Step 4: Sending email report..."
python execution/send_email.py
if [ $? -ne 0 ]; then
    echo "Error in Step 4. Exiting."
    exit 1
fi

echo "All steps completed successfully!"
