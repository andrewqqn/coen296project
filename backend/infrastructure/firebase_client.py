import os
import glob
import firebase_admin
from firebase_admin import credentials, firestore

from config import *
from dotenv import load_dotenv
load_dotenv()


def _find_service_account_in_backend():
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pattern = os.path.join(backend_dir, "*firebase-adminsdk*.json")
    matches = glob.glob(pattern)
    return matches[0] if matches else None


def init_firebase():
    if not firebase_admin._apps:
        sa_path = CREDENTIALS_PATH if CREDENTIALS_PATH else _find_service_account_in_backend()

        if USE_FIRESTORE_EMULATOR:
            # Ensure emulator env vars exist BEFORE import storage/auth
            if FIRESTORE_EMULATOR_HOST:
                os.environ["FIRESTORE_EMULATOR_HOST"] = FIRESTORE_EMULATOR_HOST
            if FIREBASE_AUTH_EMULATOR_HOST:
                os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = FIREBASE_AUTH_EMULATOR_HOST
            if FIREBASE_STORAGE_EMULATOR_HOST:
                os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = FIREBASE_STORAGE_EMULATOR_HOST
            if PROJECT_ID:
                os.environ["GCLOUD_PROJECT"] = PROJECT_ID

            # Service account or no?
            if sa_path and os.path.exists(sa_path):
                cred = credentials.Certificate(sa_path)
                firebase_admin.initialize_app(cred, options={
                    "projectId": PROJECT_ID,
                    "storageBucket": f"{PROJECT_ID}.appspot.com",
                })
                print(f"Firebase Admin SDK initialized in EMULATOR mode with service account (Project: {PROJECT_ID})")
            else:
                firebase_admin.initialize_app(options={
                    "projectId": PROJECT_ID,
                    "storageBucket": f"{PROJECT_ID}.appspot.com",
                })
                print(f"Firebase Admin SDK initialized in EMULATOR mode (no service account) (Project: {PROJECT_ID})")

        else:
            # Production Mode
            if sa_path and os.path.exists(sa_path):
                cred = credentials.Certificate(sa_path)
                firebase_admin.initialize_app(cred, {
                    "storageBucket": STORAGE_BUCKET,
                    "projectId": PROJECT_ID
                })
                print("Firebase initialized with PRODUCTION service account credentials")
            else:
                raise RuntimeError("Production requires service account JSON.")

def get_firestore_client():
    init_firebase()
    return firestore.client()
