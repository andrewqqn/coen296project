from infrastructure.firebase_client import get_firestore_client

db = get_firestore_client()
COLLECTION = "bank_accounts"


def get(bank_account: str):
    doc = db.collection(COLLECTION).document(bank_account).get()
    return doc.to_dict() | {"bank_account": doc.id} if doc.exists else None


def create(bank_account: str, data: dict):
    ref = db.collection(COLLECTION).document(bank_account)
    ref.set(data)
    return bank_account


def update(bank_account: str, data: dict):
    ref = db.collection(COLLECTION).document(bank_account)
    ref.update(data)
    return get(bank_account)
