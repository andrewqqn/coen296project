from repositories import document_repo


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
    """Download receipt from Firebase Storage or local filesystem"""
    import os
    
    # Handle local:// paths (from orchestrator file uploads)
    if file_path.startswith("local://"):
        local_path = file_path.replace("local://", "")
        full_path = os.path.join(os.getcwd(), local_path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Local file not found: {full_path}")
        
        with open(full_path, "rb") as f:
            return f.read()
    
    # Otherwise download from Firebase Storage
    return download_document(file_path)


def generate_receipt_url(file_path: str, expire_seconds: int = 3600):
    return generate_document_url(file_path, expire_seconds)
