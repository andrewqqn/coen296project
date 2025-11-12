import pytest, requests
from datetime import datetime


@pytest.mark.unit
def test_create_expense(base_url, headers, store):
    payload = {"expense_id": "EXP001", "employee_id": store.get("employee_id"), "amount": 99.99, "category": "Travel", "description": "Taxi", "status": "pending", "decision_type": "AI", "submitted_at": datetime.utcnow().isoformat(), "updated_at": datetime.utcnow().isoformat()}
    r = requests.post(f"{base_url}/expenses", json=payload, headers=headers)
    assert r.status_code == 200
    created_expense_id = payload["expense_id"]

@pytest.mark.unit
def test_get_expenses(base_url, headers, store):
    r = requests.get(f"{base_url}/expenses", headers=headers)
    assert r.status_code == 200

@pytest.mark.unit
def test_get_expense_by_id(base_url, headers, store):
    global created_expense_id
    r = requests.get(f"{base_url}/expenses/{created_expense_id}", headers=headers)
    assert r.status_code == 200

@pytest.mark.unit
def test_update_expense(base_url, headers, store):
    global created_expense_id
    payload = {"description": "Updated"}
    r = requests.patch(f"{base_url}/expenses/{created_expense_id}", json=payload, headers=headers)
    assert r.status_code == 200