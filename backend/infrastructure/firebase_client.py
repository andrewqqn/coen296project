import os
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth

from google.auth.credentials import AnonymousCredentials as GoogleAnonymousCredentials

from config import *


def init_firebase():
    if not firebase_admin._apps:
        if USE_FIRESTORE_EMULATOR:
            os.environ["FIRESTORE_EMULATOR_HOST"] = FIRESTORE_EMULATOR_HOST
            os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = FIREBASE_AUTH_EMULATOR_HOST
            os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = FIREBASE_STORAGE_EMULATOR_HOST
            os.environ["GCLOUD_PROJECT"] = PROJECT_ID

            cred = GoogleAnonymousCredentials()
            firebase_admin.initialize_app(cred, {
                "projectId": PROJECT_ID,
                "storageBucket": f"{PROJECT_ID}.appspot.com"
            })

            print(f"Firebase Admin SDK initialized in EMULATOR mode (Project: {PROJECT_ID})")

        else:
            cred = credentials.Certificate(CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {
                "storageBucket": STORAGE_BUCKET,
                "projectId": PROJECT_ID
            })
            print("Firebase initialized with PRODUCTION credentials")


def get_firestore_client():
    init_firebase()
    return firestore.client()


def get_storage_bucket():
    init_firebase()
    return storage.bucket()


def get_auth_client():
    init_firebase()
    return auth