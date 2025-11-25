import os
import json
import time
import base64
import urllib.parse
import requests


PROJECT_ID = os.getenv("PROJECT_ID")
BUCKET = os.getenv("STORAGE_BUCKET")  # expensense-8110a.firebasestorage.app
EMU_HOST = os.getenv("FIREBASE_STORAGE_EMULATOR_HOST")  # 127.0.0.1:9199
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
    SESSION = requests.Session()


# -------------------------------------------------------------
# 1. Upload File (Correct: use emulator JSON result)
# -------------------------------------------------------------
def upload_file(file_path: str, file_bytes: bytes, content_type="application/octet-stream"):
    """
    Upload a file using Firebase Storage REST API.
    Correctly handles URL encoding + emulator response (mediaLink).
    """

    encoded_path = urllib.parse.quote(file_path, safe='')

    url = f"{BASE_UPLOAD}/{BUCKET}/o?uploadType=media&name={encoded_path}"
    headers = {"Content-Type": content_type}

    r = SESSION.post(url, data=file_bytes, headers=headers)

    if r.status_code not in (200, 201):
        raise Exception(f"Upload failed: {r.text}")

    resp = r.json()

    # emulator and production both return `mediaLink`
    download_url = resp.get("mediaLink")

    return {
        "success": True,
        "path": resp["name"],        # exact path inside bucket
        "bucket": resp["bucket"],
        "generation": resp.get("generation"),
        "download_url": download_url,
    }


# -------------------------------------------------------------
# 2. Download File
# -------------------------------------------------------------
def download_file(file_path: str) -> bytes:
    """Download file (URL encoded)."""
    encoded = urllib.parse.quote(file_path, safe='')

    url = f"{BASE_DOWNLOAD}/{BUCKET}/o/{encoded}?alt=media"
    r = SESSION.get(url)

    if r.status_code != 200:
        raise Exception(f"Download failed: {r.text}")

    return r.content


# -------------------------------------------------------------
# 3. File Exists
# -------------------------------------------------------------
def file_exists(file_path: str) -> bool:
    encoded = urllib.parse.quote(file_path, safe='')
    url = f"{BASE_STORAGE}/{BUCKET}/o/{encoded}"
    r = SESSION.get(url)
    return r.status_code == 200


# -------------------------------------------------------------
# 4. Delete File
# -------------------------------------------------------------
def delete_file(file_path: str):
    encoded = urllib.parse.quote(file_path, safe='')
    url = f"{BASE_STORAGE}/{BUCKET}/o/{encoded}"
    r = SESSION.delete(url)

    if r.status_code not in (200, 204):
        raise Exception(f"Delete failed: {r.text}")

    return True


# -------------------------------------------------------------
# 5. Signed URL - Production only
# -------------------------------------------------------------
def generate_signed_url(file_path: str, expire_seconds: int = 3600):
    """Signed URL for production. Emulator doesn't support it."""

    if USE_EMULATOR:
        encoded = urllib.parse.quote(file_path, safe='')
        return f"{BASE_DOWNLOAD}/{BUCKET}/o/{encoded}?alt=media"

    sa_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if not sa_path or not os.path.exists(sa_path):
        raise RuntimeError("Signed URL requires a service account JSON.")

    with open(sa_path, "r") as f:
        data = json.load(f)

    client_email = data["client_email"]
    private_key = data["private_key"]

    expires_at = int(time.time()) + expire_seconds
    encoded = urllib.parse.quote(file_path, safe='')

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
