from domain.repositories import document_repo


# ---- Base generic document API ----

def upload_document(file_path: str, file_data: bytes):
    return document_repo.upload_file(file_path, file_data)


def download_document(file_path: str) -> bytes:
    return document_repo.download_file(file_path)


def generate_document_url(file_path: str, expire_seconds: int = 3600):
    return document_repo.generate_signed_url(file_path, expire_seconds)


# ---- Domain-specific wrappers (optional) ----

def upload_receipt(file_name: str, file_data: bytes):
    return upload_document(f"expense_receipts/{file_name}", file_data)


def download_receipt(file_path: str):
    return download_document(file_path)


def generate_receipt_url(file_path: str, expire_seconds: int = 3600):
    return generate_document_url(file_path, expire_seconds)
