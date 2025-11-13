from infrastructure.firebase_client import get_storage_bucket

UPLOAD_FOLDER = "expense_receipts"


class StorageError(RuntimeError):
    """Raised when storage operations fail or bucket is not configured."""

def _get_bucket():
    b = get_storage_bucket()
    print("====== STORAGE DEBUG ======")
    print("Storage bucket:", b)
    print("===========================")

    if b is None:
        raise StorageError("Storage bucket is not configured")
    return b


def upload_file(file_name: str, file_data: bytes) -> str:
    file_path = f"{UPLOAD_FOLDER}/{file_name}"
    b = _get_bucket()
    try:
        blob = b.blob(file_path)
        blob.upload_from_string(file_data)
        return file_path  # only store path in Firestore
    except Exception as e:
        raise StorageError(f"upload_file failed for {file_path}: {e}") from e


def generate_signed_url(file_path: str, expire_seconds: int = 3600) -> str:
    """
    Create a temporary signed URL for reading the file.
    """
    b = _get_bucket()
    try:
        blob = b.blob(file_path)
        return blob.generate_signed_url(expiration=expire_seconds)
    except Exception as e:
        raise StorageError(f"generate_signed_url failed for {file_path}: {e}") from e


def delete_file(file_path: str):
    b = _get_bucket()
    try:
        blob = b.blob(file_path)
        blob.delete()
        return {"deleted": True, "file_path": file_path}
    except Exception as e:
        raise StorageError(f"delete_file failed for {file_path}: {e}") from e


def download_file(file_path: str) -> bytes:
    b = _get_bucket()
    try:
        blob = b.blob(file_path)
        return blob.download_as_bytes()
    except Exception as e:
        raise StorageError(f"download_file failed for {file_path}: {e}") from e


def file_exists(file_path: str) -> bool:
    b = _get_bucket()
    try:
        blob = b.blob(file_path)
        # Some storage client implementations expose exists as a method or property
        exists = blob.exists() if callable(getattr(blob, "exists", None)) else bool(getattr(blob, "exists", False))
        return exists
    except Exception as e:
        raise StorageError(f"file_exists check failed for {file_path}: {e}") from e


def get_metadata(file_path: str) -> dict:
    b = _get_bucket()
    try:
        blob = b.blob(file_path)
        # ensure latest metadata
        if callable(getattr(blob, "reload", None)):
            blob.reload()
        return {
            "content_type": getattr(blob, "content_type", None),
            "size": getattr(blob, "size", None),
            "updated": getattr(blob, "updated", None),
            "file_path": file_path,
        }
    except Exception as e:
        raise StorageError(f"get_metadata failed for {file_path}: {e}") from e
