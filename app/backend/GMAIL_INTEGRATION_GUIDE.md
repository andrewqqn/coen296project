# Gmail Integration Guide

## Overview

The `gmail_token.json` file contains OAuth2 credentials that allow the system to send **real emails** through Gmail API instead of using the mock email service.

## What's in gmail_token.json?

```json
{
  "token": "ya29.a0ATi6K2s...",           // Access token (expires)
  "refresh_token": "1//016oswlAfHwAY...", // Refresh token (long-lived)
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "121877044442-...",
  "client_secret": "GOCSPX-...",
  "scopes": [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify"
  ],
  "expiry": "2025-11-27T01:37:09Z"        // Token expiration
}
```

## How It Works

### 1. OAuth2 Flow (Already Done)

The token was created through OAuth2 flow:
1. User authorized the app to access Gmail
2. Google provided access token + refresh token
3. Tokens saved to `gmail_token.json`

### 2. Token Refresh (Automatic)

When the access token expires:
1. System uses refresh_token to get new access token
2. Updated token saved back to file
3. No user interaction needed

### 3. Gmail API Usage

The token is used to:
- Send emails via Gmail API
- Read inbox messages
- Modify labels
- Search emails

## Integration with Email Agent

### Current Setup (Mock)

```python
# backend/infrastructure/email_client.py
def send_email(to, subject, body):
    print(f"Sending email to {to} ...")
    return {"status": "sent", "to": to}
```

### With Gmail (Real Emails)

```python
# Uses app/email_agent/gmail/gmail_service_creator.py
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load token
creds = Credentials.from_authorized_user_file('gmail_token.json', SCOPES)

# Create Gmail service
service = build('gmail', 'v1', credentials=creds)

# Send email
gmail_client = GmailClient(service)
email_service = EmailService(gmail_client)
email_service.send_email(to, subject, body)
```

## How to Enable Gmail in Email Agent

### Option 1: Update Email Agent Service (Recommended)

Update `backend/services/agents/email_agent_service.py`:

```python
def _get_email_service(self):
    """Lazy load email service"""
    if self._email_service is None:
        try:
            # Try to use Gmail
            import os
            token_file = os.path.join(
                os.path.dirname(__file__), 
                '../../../app/email_agent/gmail_token.json'
            )
            
            if os.path.exists(token_file):
                from app.email_agent.gmail.gmail_service_creator import GmailServiceCreator
                from app.email_agent.gmail.gmail_client import GmailClient
                from app.email_agent.services.email_service import EmailService
                
                # Create Gmail service
                service = GmailServiceCreator.create_gmail_service(
                    credentials_file='gmail_oauth_credentials.json',
                    token_file=token_file
                )
                
                # Create email service
                gmail_client = GmailClient(service)
                self._email_service = EmailService(gmail_client)
                
                logger.info("✅ Gmail service initialized - REAL emails will be sent!")
            else:
                # Fallback to mock
                from infrastructure.email_client import send_email
                self._email_service = {"send": send_email}
                logger.info("⚠️  Using mock email service")
                
        except Exception as e:
            logger.error(f"Gmail setup failed: {e}, using mock")
            from infrastructure.email_client import send_email
            self._email_service = {"send": send_email}
    
    return self._email_service
```

### Option 2: Environment Variable

Set environment variable to enable Gmail:

```bash
export USE_GMAIL=true
export GMAIL_TOKEN_FILE=app/email_agent/gmail_token.json
```

Then check in code:

```python
if os.getenv('USE_GMAIL') == 'true':
    # Use Gmail
else:
    # Use mock
```

## File Locations

```
project/
├── app/
│   └── email_agent/
│       ├── gmail_token.json              ← OAuth2 token (FOUND!)
│       ├── gmail_oauth_credentials.json  ← OAuth2 client config
│       ├── config.py                     ← Configuration
│       ├── gmail/
│       │   ├── gmail_client.py           ← Gmail API wrapper
│       │   └── gmail_service_creator.py  ← Service initialization
│       └── services/
│           └── email_service.py          ← Email sending logic
└── backend/
    ├── services/agents/
    │   └── email_agent_service.py        ← Email agent (A2A)
    └── infrastructure/
        └── email_client.py               ← Mock email service
```

## Testing Gmail Integration

### Test 1: Check Token

```python
import os
import json

token_file = 'app/email_agent/gmail_token.json'
if os.path.exists(token_file):
    with open(token_file) as f:
        token = json.load(f)
    print(f"✅ Token found!")
    print(f"   Scopes: {token.get('scopes')}")
    print(f"   Expiry: {token.get('expiry')}")
else:
    print("❌ Token not found")
```

### Test 2: Send Test Email

```python
from app.email_agent.gmail.gmail_service_creator import GmailServiceCreator
from app.email_agent.gmail.gmail_client import GmailClient
from app.email_agent.services.email_service import EmailService

# Create service
service = GmailServiceCreator.create_gmail_service(
    credentials_file='gmail_oauth_credentials.json',
    token_file='app/email_agent/gmail_token.json'
)

# Send test email
gmail_client = GmailClient(service)
email_service = EmailService(gmail_client)

result = email_service.send_email(
    to='your-email@example.com',
    subject='Test from ExpenseSense',
    body='This is a test email from the Gmail integration!'
)

print(f"✅ Email sent! Message ID: {result.get('id')}")
```

### Test 3: Integration Test

```bash
cd backend
python test_gmail_integration.py
```

## Security Considerations

### 1. Token Security

⚠️ **IMPORTANT**: The `gmail_token.json` contains sensitive credentials!

- **DO NOT** commit to git
- **DO NOT** share publicly
- **DO** add to `.gitignore`
- **DO** use environment variables in production

### 2. Add to .gitignore

```bash
# Gmail credentials
gmail_token.json
gmail_oauth_credentials.json
app/email_agent/gmail_token.json
app/email_agent/gmail_oauth_credentials.json
```

### 3. Production Setup

For production:
1. Store tokens in secure vault (AWS Secrets Manager, etc.)
2. Use service account instead of user OAuth
3. Implement token rotation
4. Monitor API usage

## Scopes Explained

The token has these Gmail API scopes:

| Scope | Permission | Used For |
|-------|-----------|----------|
| `gmail.send` | Send emails | Expense notifications |
| `gmail.readonly` | Read emails | Search inbox |
| `gmail.modify` | Modify labels | Organize emails |

## Token Expiration

- **Access Token**: Expires in ~1 hour
- **Refresh Token**: Long-lived (doesn't expire unless revoked)
- **Auto-refresh**: System automatically refreshes access token using refresh token

## Troubleshooting

### Token Expired

If you see "Token expired" error:

```python
# Token will auto-refresh on next use
# If refresh fails, need to re-authenticate
```

### Invalid Token

If token is invalid:
1. Delete `gmail_token.json`
2. Run OAuth flow again to get new token
3. Or use mock email service

### Permission Denied

If you see "Permission denied":
- Check scopes in token match required scopes
- May need to re-authorize with correct scopes

## Quick Start

### Enable Gmail (3 steps)

1. **Verify token exists**:
   ```bash
   ls -la app/email_agent/gmail_token.json
   ```

2. **Update email agent** (see Option 1 above)

3. **Test**:
   ```bash
   python backend/test_gmail_integration.py
   ```

### Disable Gmail (use mock)

Just don't update the email agent - it will use mock by default.

## Summary

The `gmail_token.json` file enables **real Gmail email sending**:

- ✅ OAuth2 token already configured
- ✅ Includes refresh token for auto-renewal
- ✅ Has all required scopes (send, read, modify)
- ✅ Ready to integrate with email agent
- ⚠️ Keep secure - don't commit to git
- 🔧 Easy to enable/disable via configuration

To use it, update the `_get_email_service()` method in `email_agent_service.py` to check for the token file and initialize Gmail service if found.
