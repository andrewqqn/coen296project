from domain.repositories import document_repo


def upload_receipt(file_name: str, file_data: bytes):
    """Upload a receipt and return file path."""
    return document_repo.upload_file(file_name, file_data)


def generate_receipt_url(file_path: str, expire_seconds: int = 3600):
    """Generate signed URL for viewing."""
    return document_repo.generate_signed_url(file_path, expire_seconds)


def delete_receipt(file_path: str):
    """Delete from Storage."""
    return document_repo.delete_file(file_path)


def download_receipt(file_path: str) -> bytes:
    """
    Download binary content of the receipt.
    Useful for Admin preview, OCR, or AI policy checks.
    """
    return document_repo.download_file(file_path)


def file_exists(file_path: str) -> bool:
    """
    Check if receipt exists in Storage (safe for admin).
    """
    return document_repo.file_exists(file_path)


def get_metadata(file_path: str) -> dict:
    """
    Retrieve metadata such as content type, size, updated_at.
    Useful for admin, audit, or validation.
    """
    return document_repo.get_metadata(file_path)
