import os
import sys
import base64
import json
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Force UTF-8 encoding for stdout/stderr
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

def get_service():
    creds = None
    if os.path.exists('token_email.json'):
        try:
            creds = Credentials.from_authorized_user_file('token_email.json', SCOPES)
        except:
            creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token_email.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def main():
    if not os.path.exists('.tmp/slide_link.json'):
        print("No slide link found.")
        return

    with open('.tmp/slide_link.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        slide_url = data.get('url')
        slide_title = data.get('title')

    if not slide_url:
        print("No URL in slide_link.json")
        return

    recipient = os.environ.get('RECIPIENT_EMAIL')
    if not recipient:
        print("RECIPIENT_EMAIL not set in environment.")
        recipient = input("Enter recipient email: ")
        if not recipient:
            return

    service = get_service()

    message = MIMEText(f"Here is your stock analysis from 3pro TV: {slide_url}")
    message['to'] = recipient
    message['subject'] = f"Stock Analysis: {slide_title}"
    create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    try:
        message = (service.users().messages().send(userId="me", body=create_message).execute())
        print(f"Email sent. Message Id: {message['id']}")
    except Exception as e:
        print(f"An error occurred sending email: {e}")

if __name__ == "__main__":
    main()
