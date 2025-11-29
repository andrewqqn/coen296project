from infrastructure.firebase_client import get_firestore_client
from google.cloud.firestore_v1.base_query import FieldFilter

db = get_firestore_client()
COLLECTION = "expenses"

def get_all():
    return [doc.to_dict() | {"expense_id": doc.id} for doc in db.collection(COLLECTION).stream()]

def get(expense_id: str):
    doc = db.collection(COLLECTION).document(expense_id).get()
    return doc.to_dict() | {"expense_id": doc.id} if doc.exists else None

def create(data: dict):
    ref = db.collection(COLLECTION).document()
    ref.set(data)
    return ref.id

def update(expense_id: str, data: dict):
    db.collection(COLLECTION).document(expense_id).update(data)
    return get(expense_id)

def delete(expense_id: str):
    db.collection(COLLECTION).document(expense_id).delete()
    return {"deleted": True, "expense_id": expense_id}

def get_by_employee(employee_id: str):
    return [
        doc.to_dict() | {"id": doc.id}
        for doc in db.collection(COLLECTION)
                    .where(filter=FieldFilter("employee_id", "==", employee_id))
                    .stream()
    ]
