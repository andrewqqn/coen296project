import os
import json
import time
import base64
import urllib.parse
import requests
import logging
from google.auth import default as google_auth_default, transport

# --- Configuration ---
PROJECT_ID = os.getenv("PROJECT_ID")
BUCKET = os.getenv("STORAGE_BUCKET")
EMU_HOST = os.getenv("FIREBASE_STORAGE_EMULATOR_HOST")
USE_EMULATOR = bool(EMU_HOST)

# --- Global HTTP Client ---
if USE_EMULATOR:
    BASE_UPLOAD = f"http://{EMU_HOST}/upload/storage/v1/b"
    BASE_STORAGE = f"http://{EMU_HOST}/storage/v1/b"
    BASE_DOWNLOAD = f"http://{EMU_HOST}/download/storage/v1/b"
    SESSION = requests.Session()
else:
    BASE_UPLOAD = "https://storage.googleapis.com/upload/storage/v1/b"
    BASE_STORAGE = "https://storage.googleapis.com/storage/v1/b"
    BASE_DOWNLOAD = "https://storage.googleapis.com/download/storage/v1/b"
    SESSION = requests.Session()
    # For production, we need a transport session to get the token
    AUTH_REQUEST = transport.requests.Request()
    CREDENTIALS, PROJECT_ID = google_auth_default()
    logging.info(f"Initialized Google Auth default credentials for project: {PROJECT_ID}")


# -------------------------------------------------------------
# Utility Function to get Production Authorization Headers
# -------------------------------------------------------------
def _get_auth_headers():
    """
    Retrieves the necessary Authorization header for Google Cloud Storage REST API.
    Uses credentials initialized globally.
    """
    if USE_EMULATOR:
        return {}

    # Refresh the access token if needed
    CREDENTIALS.refresh(AUTH_REQUEST)
    return {"Authorization": f"Bearer {CREDENTIALS.token}"}


# -------------------------------------------------------------
# 1. Upload File
# -------------------------------------------------------------
def upload_file(file_path: str, file_bytes: bytes, content_type="application/octet-stream"):
    """
    Upload a file using Google Cloud Storage REST API.
    Adds Authorization header in production mode (Cloud Run) to fix 401 error.
    """
    encoded_path = urllib.parse.quote(file_path, safe='')

    # The URL for the upload endpoint
    url = f"{BASE_UPLOAD}/{BUCKET}/o?uploadType=media&name={encoded_path}"

    # Base headers
    headers = {"Content-Type": content_type}

    # Add Authorization header if in production mode
    headers.update(_get_auth_headers())

    r = SESSION.post(url, data=file_bytes, headers=headers)

    if r.status_code not in (200, 201):
        # Log failure details before raising
        logging.error(f"Storage Upload Failed ({r.status_code}): {r.text}")
        raise Exception(f"Upload failed: {r.text}")

    resp = r.json()
    download_url = resp.get("mediaLink")

    return {
        "success": True,
        "path": resp["name"],
        "bucket": resp["bucket"],
        "generation": resp.get("generation"),
        "download_url": download_url,
    }


# -------------------------------------------------------------
# 2. Download File
# -------------------------------------------------------------
def download_file(file_path: str) -> bytes:
    """
    Download file using Google Cloud Storage REST API.
    Adds Authorization header in production mode.
    """
    encoded = urllib.parse.quote(file_path, safe='')
    url = f"{BASE_DOWNLOAD}/{BUCKET}/o/{encoded}?alt=media"

    headers = _get_auth_headers()

    r = SESSION.get(url, headers=headers)

    if r.status_code != 200:
        logging.error(f"Storage Download Failed ({r.status_code}): {r.text}")
        raise Exception(f"Download failed: {r.text}")

    return r.content


# -------------------------------------------------------------
# 3. File Exists
# -------------------------------------------------------------
def file_exists(file_path: str) -> bool:
    """
    Check if a file exists using Google Cloud Storage REST API.
    Adds Authorization header in production mode.
    """
    encoded = urllib.parse.quote(file_path, safe='')
    url = f"{BASE_STORAGE}/{BUCKET}/o/{encoded}"

    headers = _get_auth_headers()
    r = SESSION.get(url, headers=headers)
    return r.status_code == 200


# -------------------------------------------------------------
# 4. Delete File
# -------------------------------------------------------------
def delete_file(file_path: str):
    """
    Delete a file using Google Cloud Storage REST API.
    Adds Authorization header in production mode.
    """
    encoded = urllib.parse.quote(file_path, safe='')
    url = f"{BASE_STORAGE}/{BUCKET}/o/{encoded}"

    headers = _get_auth_headers()
    r = SESSION.delete(url, headers=headers)

    if r.status_code not in (200, 204):
        logging.error(f"Storage Delete Failed ({r.status_code}): {r.text}")
        raise Exception(f"Delete failed: {r.text}")

    return True


# -------------------------------------------------------------
# 5. Signed URL - Production only (uses file based credentials)
# -------------------------------------------------------------
def generate_signed_url(file_path: str, expire_seconds: int = 3600):
    """Signed URL for production. Emulator doesn't support it."""

    if USE_EMULATOR:
        encoded = urllib.parse.quote(file_path, safe='')
        return f"{BASE_DOWNLOAD}/{BUCKET}/o/{encoded}?alt=media"

    # NOTE: Signed URLs typically require the private key for signing,
    # which means relying on the service account JSON file (sa_path).
    # This remains the only reliable way to generate the signed URL string
    # without switching to the official Google Cloud Storage Python library.
    sa_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if not sa_path or not os.path.exists(sa_path):
        # Fallback to the default (unsigned) GCS URL since we cannot sign it
        logging.warning("Cannot generate signed URL: FIREBASE_CREDENTIALS_PATH not found. Returning public link.")
        encoded = urllib.parse.quote(file_path, safe='')
        return f"https://storage.googleapis.com/{BUCKET}/{encoded}"

    with open(sa_path, "r") as f:
        data = json.load(f)

    client_email = data["client_email"]
    private_key = data["private_key"]

    expires_at = int(time.time()) + expire_seconds
    encoded = urllib.parse.quote(file_path, safe='')

    # GCS V1 signing protocol
    to_sign = f"GET\n\n\n{expires_at}\n/{BUCKET}/{encoded}".encode("utf-8")

    import hashlib, hmac

    signature = base64.b64encode(
        hmac.new(private_key.encode("utf-8"), to_sign, hashlib.sha256).digest()
    ).decode("utf-8")

    return (
        f"https://storage.googleapis.com/{BUCKET}/{encoded}"
        f"?GoogleAccessId={client_email}"
        f"&Expires={expires_at}"
        f"&Signature={signature}"
    )