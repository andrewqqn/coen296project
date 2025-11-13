import os
import glob
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth

from config import *


def _find_service_account_in_backend():
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pattern = os.path.join(backend_dir, "*firebase-adminsdk*.json")
    matches = glob.glob(pattern)
    return matches[0] if matches else None


def init_firebase():
    if not firebase_admin._apps:
        sa_path = CREDENTIALS_PATH if CREDENTIALS_PATH else _find_service_account_in_backend()

        if USE_FIRESTORE_EMULATOR:
            if FIRESTORE_EMULATOR_HOST:
                os.environ["FIRESTORE_EMULATOR_HOST"] = FIRESTORE_EMULATOR_HOST
            if FIREBASE_AUTH_EMULATOR_HOST:
                os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = FIREBASE_AUTH_EMULATOR_HOST
            if FIREBASE_STORAGE_EMULATOR_HOST:
                os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = FIREBASE_STORAGE_EMULATOR_HOST
            if PROJECT_ID:
                os.environ["GCLOUD_PROJECT"] = PROJECT_ID

            if sa_path and os.path.exists(sa_path):
                # Use real service account even when pointing at emulators; this avoids credential refresh issues
                cred = credentials.Certificate(sa_path)
                firebase_admin.initialize_app(cred, options={
                    "projectId": PROJECT_ID,
                    "storageBucket": f"{PROJECT_ID}.appspot.com" if PROJECT_ID else None,
                })
                print(f"Firebase Admin SDK initialized in EMULATOR mode with service account (Project: {PROJECT_ID})")
            else:
                # No service account; initialize without credentials (best-effort emulator usage)
                firebase_admin.initialize_app(options={
                    "projectId": PROJECT_ID,
                    "storageBucket": f"{PROJECT_ID}.appspot.com" if PROJECT_ID else None,
                })
                print(f"Firebase Admin SDK initialized in EMULATOR mode (no service account) (Project: {PROJECT_ID})")

        else:
            # Production / non-emulator mode: require service account credentials
            if sa_path and os.path.exists(sa_path):
                cred = credentials.Certificate(sa_path)
                firebase_admin.initialize_app(cred, {
                    "storageBucket": STORAGE_BUCKET,
                    "projectId": PROJECT_ID
                })
                print("Firebase initialized with PRODUCTION service account credentials")
            else:
                raise RuntimeError("Production initialization requires a service account JSON. Set FIREBASE_CREDENTIALS_PATH or place a service account JSON in backend/.")


def get_firestore_client():
    init_firebase()
    return firestore.client()


def get_storage_bucket():
    init_firebase()

    b = storage.bucket()

    print("====== STORAGE DEBUG ======")
    print("Firebase App Name:", firebase_admin.get_app().name)
    print("Project ID:", firebase_admin.get_app().project_id)
    print("Bucket from SDK:", b)
    print("Bucket name:", b.name)
    print("FIREBASE_STORAGE_EMULATOR_HOST =", os.getenv("FIREBASE_STORAGE_EMULATOR_HOST"))
    print("GCLOUD_PROJECT =", os.getenv("GCLOUD_PROJECT"))
    print("USE_FIRESTORE_EMULATOR =", os.getenv("USE_FIRESTORE_EMULATOR"))
    print("===========================")

    return b



def get_auth_client():
    init_firebase()
    return auth