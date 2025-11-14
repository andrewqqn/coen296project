from infrastructure.firebase_client import get_firestore_client
db = get_firestore_client()
COLLECTION = "audit_logs"
def get_all(): return [doc.to_dict() | {"id": doc.id} for doc in db.collection(COLLECTION).order_by("timestamp").stream()]
def create(data: dict):
    ref = db.collection(COLLECTION).document()
    ref.set(data)
    return {"id": ref.id, **data}
