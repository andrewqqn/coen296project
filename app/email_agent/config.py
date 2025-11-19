import os

GOOGLE_CREDENTIALS_FILE = os.environ.get(
    "GOOGLE_CREDENTIALS_FILE", # placeholder
    "credentials.json"  # Your OAuth2 credentials file
)

TOKEN_FILE = os.environ.get(
    "GOOGLE_TOKEN_FILE", # placeholder
    "token.json"  # Automatically refreshed token
)

EMAIL_SENDER = os.environ.get(
    "EMAIL_SENDER", # placeholder
    "yourname@gmail.com" # placeholder
)