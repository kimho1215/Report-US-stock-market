# US Stock Market Report - Automation Script
# This script executes the following steps in order.

Write-Host "Step 1: Fetching recent YouTube videos..." -ForegroundColor Cyan
python execution/get_recent_videos.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error in Step 1. Exiting." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Step 2: Extracting recommendations using Gemini AI..." -ForegroundColor Cyan
python execution/extract_recommendations.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error in Step 2. Exiting." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Step 3: Creating/Updating Google Slides..." -ForegroundColor Cyan
python execution/create_slides.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error in Step 3. Exiting." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Step 4: Sending email report..." -ForegroundColor Cyan
python execution/send_email.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error in Step 4. Exiting." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "All steps completed successfully!" -ForegroundColor Green
