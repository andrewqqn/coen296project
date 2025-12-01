"""
Test real Gmail sending
"""
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gmail_service():
    """Test Gmail service initialization"""
    print("\n" + "="*70)
    print("Testing Gmail Service Initialization")
    print("="*70)
    
    try:
        # Check token file
        token_path = '../app/email_agent/gmail_token.json'
        print(f"\n1. Checking token file: {token_path}")
        if os.path.exists(token_path):
            print(f"   ✅ Token file exists")
        else:
            print(f"   ❌ Token file not found")
            return False
        
        # Try to import Gmail modules
        print(f"\n2. Importing Gmail modules...")
        from app.email_agent.gmail.gmail_service_creator import GmailServiceCreator
        from app.email_agent.gmail.gmail_client import GmailClient
        from app.email_agent.services.email_service import EmailService
        print(f"   ✅ Imports successful")
        
        # Create Gmail service
        print(f"\n3. Creating Gmail service...")
        service = GmailServiceCreator.create_gmail_service(
            credentials_file='gmail_oauth_credentials.json',
            token_file=token_path
        )
        print(f"   ✅ Gmail service created")
        
        # Create clients
        print(f"\n4. Creating Gmail client...")
        gmail_client = GmailClient(service)
        email_service = EmailService(gmail_client)
        print(f"   ✅ Email service created")
        
        # Get authenticated user
        print(f"\n5. Getting authenticated user...")
        user_email = gmail_client.get_authenticated_user_email()
        print(f"   ✅ Authenticated as: {user_email}")
        
        # Send test email
        print(f"\n6. Sending test email...")
        result = email_service.send_email(
            to="nguyen.andrew.quang@gmail.com",
            subject="Test from ExpenseSense",
            body="This is a test email to verify Gmail integration is working!"
        )
        print(f"   ✅ Email sent!")
        print(f"   Message ID: {result.get('id')}")
        print(f"   Thread ID: {result.get('threadId')}")
        
        print(f"\n" + "="*70)
        print("✅ Gmail service is working! Check your inbox.")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_gmail_service()
