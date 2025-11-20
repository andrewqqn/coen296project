import os

GMAIL_CREDENTIALS_FILE = os.environ.get(
    "GMAIL_CREDENTIALS_FILE", 
    "gmail_oauth_credentials.json"  # OAuth2 credentials file
)

GMAIL_TOKEN_FILE = os.environ.get(
    "GMAIL_TOKEN_FILE",
    "token.json"  # Automatically refreshed token
)