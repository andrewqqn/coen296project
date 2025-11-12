from infrastructure.firebase_client import get_firestore_client
db = get_firestore_client()
COLLECTION = "employees"
def get_all(): return [doc.to_dict() | {"employee_id": doc.id} for doc in db.collection(COLLECTION).stream()]
def get(emp_id: str):
    doc = db.collection(COLLECTION).document(emp_id).get()
    return doc.to_dict() | {"employee_id": doc.id} if doc.exists else None
def create(data: dict):
    ref = db.collection(COLLECTION).document()
    data["employee_id"] = ref.id
    ref.set(data)
    return data
def update(emp_id: str, data: dict):
    db.collection(COLLECTION).document(emp_id).update(data)
    return {"update": True, "employee_id": emp_id}
def delete(emp_id: str):
    db.collection(COLLECTION).document(emp_id).delete()
    return {"deleted": True, "employee_id": emp_id}
