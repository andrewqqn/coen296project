import os
import sys
import firebase_admin
from firebase_admin import auth, credentials

# This script needs to be run in a server environment
# where the Admin SDK is initialized.

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Get the project ID from an environment variable
project_id = os.environ.get('GCLOUD_PROJECT')

if not project_id:
    sys.exit("The GCLOUD_PROJECT environment variable is not set.")

# Initialize the Firebase Admin SDK
firebase_admin.initialize_app()

def set_admin_claim(email):
    """
    Sets a custom claim 'admin' to True for the user with the given email.
    """
    try:
        user = auth.get_user_by_email(email)
        # Add custom claims for additional privileges.
        auth.set_custom_user_claims(user.uid, {'admin': True})
        print(f"Successfully set admin claim for {email}")
    except Exception as e:
        print(f"Error setting admin claim: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python set_admin.py <email>")
        sys.exit(1)
    
    email_to_make_admin = sys.argv[1]
    set_admin_claim(email_to_make_admin)
