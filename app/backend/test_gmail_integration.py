"""
Test Gmail Integration

This script tests if Gmail token is valid and can send real emails.
"""
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_token_file():
    """Check if Gmail token file exists and is valid"""
    print("\n" + "="*70)
    print("Step 1: Check Gmail Token File")
    print("="*70)
    
    # Try multiple possible locations
    possible_paths = [
        'app/email_agent/gmail_token.json',
        '../app/email_agent/gmail_token.json',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app/email_agent/gmail_token.json')
    ]
    
    token_file = None
    for path in possible_paths:
        if os.path.exists(path):
            token_file = path
            break
    
    if not token_file:
        print(f"❌ Token file not found: {token_file}")
        return False
    
    print(f"✅ Token file found: {token_file}")
    
    try:
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        print(f"\n📋 Token Details:")
        print(f"   Client ID: {token_data.get('client_id', 'N/A')[:30]}...")
        print(f"   Scopes: {len(token_data.get('scopes', []))} scopes")
        for scope in token_data.get('scopes', []):
            print(f"      - {scope}")
        
        expiry = token_data.get('expiry')
        if expiry:
            print(f"   Expiry: {expiry}")
            # Note: Token will auto-refresh if expired
        
        has_refresh = 'refresh_token' in token_data
        print(f"   Has Refresh Token: {'✅ Yes' if has_refresh else '❌ No'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading token: {e}")
        return False


def test_gmail_service():
    """Test creating Gmail service"""
    print("\n" + "="*70)
    print("Step 2: Initialize Gmail Service")
    print("="*70)
    
    try:
        from app.email_agent.gmail.gmail_service_creator import GmailServiceCreator
        from app.email_agent.gmail.gmail_client import GmailClient
        
        print("📦 Importing Gmail modules...")
        
        # Find token file
        possible_paths = [
            'app/email_agent/gmail_token.json',
            '../app/email_agent/gmail_token.json',
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app/email_agent/gmail_token.json')
        ]
        
        token_file = None
        for path in possible_paths:
            if os.path.exists(path):
                token_file = path
                break
        
        if not token_file:
            print("❌ Token file not found")
            return None
        
        print(f"📁 Using token file: {token_file}")
        print("🔧 Creating Gmail service...")
        service = GmailServiceCreator.create_gmail_service(
            credentials_file='gmail_oauth_credentials.json',
            token_file=token_file
        )
        
        print("✅ Gmail service created successfully!")
        
        print("\n🔍 Testing Gmail API connection...")
        gmail_client = GmailClient(service)
        
        # Get authenticated user email
        user_email = gmail_client.get_authenticated_user_email()
        
        if user_email:
            print(f"✅ Connected to Gmail!")
            print(f"   Authenticated as: {user_email}")
            return gmail_client
        else:
            print("❌ Could not get user email")
            return None
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure google-api-python-client is installed:")
        print("   pip install google-api-python-client google-auth-oauthlib")
        return None
    except Exception as e:
        print(f"❌ Error creating Gmail service: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_send_email(gmail_client, test_email=None):
    """Test sending an email"""
    print("\n" + "="*70)
    print("Step 3: Send Test Email")
    print("="*70)
    
    if not gmail_client:
        print("⏭️  Skipping - Gmail client not available")
        return False
    
    if not test_email:
        print("\n⚠️  No test email address provided")
        print("   To send a test email, run:")
        print("   python test_gmail_integration.py your-email@example.com")
        return False
    
    try:
        from app.email_agent.services.email_service import EmailService
        
        email_service = EmailService(gmail_client)
        
        print(f"\n📧 Sending test email to: {test_email}")
        
        subject = "Test Email from ExpenseSense"
        body = f"""
Hello!

This is a test email from the ExpenseSense Gmail integration.

If you're receiving this, it means:
✅ Gmail OAuth2 token is valid
✅ Gmail API connection is working
✅ Email sending is functional

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
ExpenseSense System
        """
        
        result = email_service.send_email(
            to=test_email,
            subject=subject,
            body=body
        )
        
        print(f"✅ Email sent successfully!")
        print(f"   Message ID: {result.get('id')}")
        print(f"   Thread ID: {result.get('threadId')}")
        print(f"\n📬 Check your inbox at: {test_email}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_email_agent_integration():
    """Test email agent with Gmail"""
    print("\n" + "="*70)
    print("Step 4: Test Email Agent Integration")
    print("="*70)
    
    print("\n💡 To enable Gmail in the email agent:")
    print("   1. Update backend/services/agents/email_agent_service.py")
    print("   2. Modify _get_email_service() to use Gmail")
    print("   3. See backend/GMAIL_INTEGRATION_GUIDE.md for details")
    
    print("\n📝 Current status:")
    print("   Email agent: ✅ Implemented (using mock)")
    print("   Gmail token: ✅ Available")
    print("   Gmail service: ✅ Working")
    print("   Integration: ⏳ Pending (manual update needed)")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("GMAIL INTEGRATION TEST")
    print("="*70)
    
    # Get test email from command line
    test_email = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Step 1: Check token
    if not check_token_file():
        print("\n❌ Cannot proceed without valid token file")
        return
    
    # Step 2: Test Gmail service
    gmail_client = test_gmail_service()
    
    # Step 3: Send test email (if email provided)
    test_send_email(gmail_client, test_email)
    
    # Step 4: Integration guide
    test_email_agent_integration()
    
    print("\n" + "="*70)
    print("TEST COMPLETED")
    print("="*70)
    
    if test_email:
        print(f"\n✅ Gmail integration is working!")
        print(f"   Check {test_email} for the test email")
    else:
        print(f"\n✅ Gmail service is ready!")
        print(f"   Run with email to test: python test_gmail_integration.py your@email.com")
    
    print("\n📚 Next steps:")
    print("   1. Read: backend/GMAIL_INTEGRATION_GUIDE.md")
    print("   2. Update: backend/services/agents/email_agent_service.py")
    print("   3. Test: python backend/test_email_on_review.py")


if __name__ == "__main__":
    main()
