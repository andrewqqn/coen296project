import pytest, requests
from pprint import pprint

created_employee_id = None

@pytest.mark.unit
def test_create_employee(base_url, headers, store):
    payload = {
        "authentication_id": "8vG0fjXtZ9ySDv9xzjACmrxuDonH",
        "email": "yzeng@scu.edu",
        "name": "Yulin Zeng",
        "position": "Software Engineer",
        "role": "admin",
        "bank_account": "12345678910",
        "notes": "expenSense Team member"
    }
    r = requests.post(f"{base_url}/employees", json=payload, headers=headers)
    assert r.status_code == 200
    pprint(r.json())
    store["employee_id"] = r.json()["employee_id"]


@pytest.mark.unit
def test_get_employees(base_url, headers):
    r = requests.get(f"{base_url}/employees", headers=headers)

    pprint(r.json())
    assert r.status_code == 200

@pytest.mark.unit
def test_get_employee_by_id(base_url, headers, store):
    created_employee_id = store.get("employee_id")
    print(f"request employee id: {created_employee_id}")

    created_employee_id = "TvIDxrxnWq7rwnVDRuIS"
    r = requests.get(f"{base_url}/employees/{created_employee_id}", headers=headers)
    pprint(r.json())
    assert r.status_code == 200

@pytest.mark.unit
def test_update_employee(base_url, headers):
    created_employee_id = store.get("employee_id")
    payload = {"position": "Senior Software Engineer", "notes": "Updated"}
    r = requests.patch(f"{base_url}/employees/{created_employee_id}", json=payload, headers=headers)
    pprint(r.json())
    assert r.status_code == 200