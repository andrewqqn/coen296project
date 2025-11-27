from infrastructure.firebase_client import get_firestore_client

db = get_firestore_client()
COLLECTION = "bank_accounts"


def get(bank_account: str):
    doc = db.collection(COLLECTION).document(bank_account).get()
    if doc.exists:
        data = doc.to_dict()
        # Ensure balance has 2 decimal precision
        if "balance" in data:
            data["balance"] = round(float(data["balance"]), 2)
        return data
    return None


def create(bank_account: str, data: dict):
    ref = db.collection(COLLECTION).document(bank_account)
    # Ensure balance has 2 decimal precision
    if "balance" in data:
        data["balance"] = round(float(data["balance"]), 2)
    ref.set(data)
    return bank_account


def update(bank_account: str, data: dict):
    ref = db.collection(COLLECTION).document(bank_account)
    # Ensure balance has 2 decimal precision
    if "balance" in data:
        data["balance"] = round(float(data["balance"]), 2)
    ref.update(data)
    return get(bank_account)
