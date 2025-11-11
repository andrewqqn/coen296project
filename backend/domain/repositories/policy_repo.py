from infrastructure.firebase_client import get_firestore_client
db = get_firestore_client()
COLLECTION = "policies"
def get_all(): return [doc.to_dict() | {"policy_id": doc.id} for doc in db.collection(COLLECTION).stream()]
def get(policy_id: str):
    doc = db.collection(COLLECTION).document(policy_id).get()
    return doc.to_dict() | {"policy_id": doc.id} if doc.exists else None
def create(data: dict):
    ref = db.collection(COLLECTION).document()
    ref.set(data)
    return get(ref.id)
def update(policy_id: str, data: dict):
    db.collection(COLLECTION).document(policy_id).update(data)
    return get(policy_id)
def delete(policy_id: str):
    db.collection(COLLECTION).document(policy_id).delete()
    return {"deleted": True, "policy_id": policy_id}
