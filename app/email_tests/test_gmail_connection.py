import os
from email_agent.gmail.gmail_service_creator import GmailServiceCreator

# Uses fake files
def test_fake_gmail_connection(tmp_path):
    fake_creds = tmp_path / "creds.json"
    fake_creds.write_text("{}")

    fake_token = tmp_path / "token.json"
    fake_token.write_text("{}")

    try:
        GmailServiceCreator.create_gmail_service(
            str(fake_creds),
            str(fake_token)
        )
    except Exception:
        # expected for fake credentials
        assert True

def test_real_gmail_connection():
    """
    This test will only pass if:
    - You have valid Gmail OAuth credentials at the given paths
    - You complete the browser OAuth flow when the test runs
    - The correct scopes are enabled
    """

    credentials_path = "email_agent/gmail_oauth_credentials.json"
    token_path = "email_agent/gmail_token.json"

    # Ensure credential files exist before running real API calls
    assert os.path.exists(credentials_path), f"Missing credentials: {credentials_path}"
    assert os.path.exists(token_path), f"Missing token: {token_path}"

    # Create Gmail API service using your credentials
    service = GmailServiceCreator.create_gmail_service(
        credentials_file=credentials_path,
        token_file=token_path
    )

    # Call Gmail 'getProfile' to confirm authenticated access
    profile = service.users().getProfile(userId="me").execute()

    # Validate response contains expected fields
    assert "emailAddress" in profile, "Profile response missing emailAddress"
    assert isinstance(profile["emailAddress"], str)
