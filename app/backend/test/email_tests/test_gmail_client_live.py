import os
import sys
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Fix imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.services.agents.email_agent.gmail.gmail_service_creator import GmailServiceCreator
from backend.services.agents.email_agent.gmail.gmail_client import GmailClient

"""
Configuration - UPDATE THESE PATHS FOR WHATEVER IS YOUR DIRECTORY WHERE 
YOU STORE THE CREDENTIALS AND YOUR EMAIL
"""
CREDENTIALS_FILE = "/coen296project/backend/services/agents/email_agent/gmail_oauth_credentials.json"
TOKEN_FILE = "/coen296/coen296project/backend/services/agents/email_agent/gmail_token.json"  # Will be created automatically
YOUR_EMAIL = "redteambcoenai@gmail.com"  # Your Gmail address

def create_test_email(to_email, subject="Test from GmailClient", body="Test body"):
    msg = MIMEMultipart()
    msg['to'] = to_email
    msg['from'] = YOUR_EMAIL
    msg['subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {'raw': raw}

def run_live_gmail_client_test():
    print("🔄 1. Creating Gmail service...")
    print(f"📁 Looking for credentials: {os.path.abspath(CREDENTIALS_FILE)}")
    
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Credentials file not found: {CREDENTIALS_FILE}")
        print("💡 Download from Google Cloud Console → APIs & Services → Credentials")
        return
    
    service = GmailServiceCreator.create_gmail_service(
        credentials_file=CREDENTIALS_FILE,
        token_file=TOKEN_FILE
    )
    
    print("✅ 2. Creating GmailClient...")
    client = GmailClient(service)
    
    user_email = client.get_authenticated_user_email()
    print(f"✅ 3. Your email: {user_email}")
    
    test_email = create_test_email(
        user_email,
        "✅ GmailClient Live Test SUCCESS",
        f"Sent at {os.popen('date').read().strip()}"
    )
    
    message = client.send_email(test_email)
    msg_id = message['id']
    print(f"✅ 4. Email sent! ID: {msg_id}")
    
    sent_msg = client.get_message(msg_id)
    if sent_msg:
        headers = sent_msg['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Unknown')
        print(f"✅ 5. Verified! Subject: {subject}")

if __name__ == "__main__":
    run_live_gmail_client_test()
