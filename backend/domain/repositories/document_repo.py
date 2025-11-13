import os
import time
import json
import base64
import hashlib
import hmac
import requests


PROJECT_ID = os.getenv("PROJECT_ID")
BUCKET = os.getenv("STORAGE_BUCKET")
EMU_HOST = os.getenv("FIREBASE_STORAGE_EMULATOR_HOST")
USE_EMULATOR = bool(EMU_HOST)

if USE_EMULATOR:
    BASE_UPLOAD = f"http://{EMU_HOST}/upload/storage/v1/b"
    BASE_STORAGE = f"http://{EMU_HOST}/storage/v1/b"
    BASE_DOWNLOAD = f"http://{EMU_HOST}/download/storage/v1/b"
    SESSION = requests.Session()
else:
    BASE_UPLOAD = "https://storage.googleapis.com/upload/storage/v1/b"
    BASE_STORAGE = "https://storage.googleapis.com/storage/v1/b"
    BASE_DOWNLOAD = "https://storage.googleapis.com/download/storage/v1/b"
    SESSION = requests.Session()   # Or AuthorizedSession?


# -----------------------------
# Upload File
# -----------------------------
def upload_file(file_path: str, file_bytes: bytes, content_type="application/octet-stream"):
    """Upload file using REST API (emulator or production)."""

    url = f"{BASE_UPLOAD}/{BUCKET}/o?uploadType=media&name={file_path}"
    headers = {"Content-Type": content_type}

    r = SESSION.post(url, data=file_bytes, headers=headers)

    if r.status_code not in (200, 201):
        raise Exception(f"Upload failed: {r.text}")

    if USE_EMULATOR:
        download_url = f"{BASE_DOWNLOAD}/{BUCKET}/o/{file_path}?alt=media"
    else:
        download_url = f"https://storage.googleapis.com/{BUCKET}/{file_path}"

    return {
        "success": True,
        "path": file_path,
        "download_url": download_url
    }


# -----------------------------
# Download File
# -----------------------------
def download_file(file_path: str) -> bytes:
    url = f"{BASE_DOWNLOAD}/{BUCKET}/o/{file_path}?alt=media"
    r = SESSION.get(url)

    if r.status_code != 200:
        raise Exception(f"Download failed: {r.text}")

    return r.content


# -----------------------------
# File Exists?
# -----------------------------
def file_exists(file_path: str) -> bool:
    url = f"{BASE_STORAGE}/{BUCKET}/o/{file_path}"
    r = SESSION.get(url)
    return r.status_code == 200


# -----------------------------
# Delete File
# -----------------------------
def delete_file(file_path: str):
    url = f"{BASE_STORAGE}/{BUCKET}/o/{file_path}"
    r = SESSION.delete(url)

    if r.status_code not in (200, 204):
        raise Exception(f"Delete failed: {r.text}")

    return True


def generate_signed_url(file_path: str, expire_seconds: int = 3600):
    """Simple version; emulator returns direct URL."""

    if USE_EMULATOR:
        # Emulator doesn't use signed URLs
        return f"{BASE_DOWNLOAD}/{BUCKET}/o/{file_path}?alt=media"

    # ---- Production signed URL (service account required) ----
    sa_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if not sa_path or not os.path.exists(sa_path):
        raise RuntimeError("Signed URL requires a service account JSON.")

    with open(sa_path, "r") as f:
        data = json.load(f)

    client_email = data["client_email"]
    private_key = data["private_key"]

    expires_at = int(time.time()) + expire_seconds
    to_sign = f"GET\n\n\n{expires_at}\n/{BUCKET}/{file_path}".encode("utf-8")

    signature = base64.b64encode(
        hmac.new(private_key.encode("utf-8"), to_sign, hashlib.sha256).digest()
    ).decode("utf-8")

    return (
        f"https://storage.googleapis.com/{BUCKET}/{file_path}"
        f"?GoogleAccessId={client_email}"
        f"&Expires={expires_at}"
        f"&Signature={signature}"
    )