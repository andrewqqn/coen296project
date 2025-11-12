import pytest, requests
from datetime import datetime
import pytest, requests
from pprint import pprint

@pytest.mark.unit
def test_create_auditlog(base_url, headers):
    payload = {
        "authentication_id": "8vG0fjXtZ9ySDv9xzjACmrxuDonH",
        "email": "yzeng@scu.edu",
        "name": "Yulin Zeng",
        "position": "Software Engineer",
        "role": "admin",
        "bank_account": "123456789",
        "notes": "expenSense Team member"
    }

    r = requests.post(f"{base_url}/audit_logs", json=payload, headers=headers)
    assert r.status_code == 201

@pytest.mark.unit
def test_get_auditlogs(base_url, headers):
    r = requests.get(f"{base_url}/audit_logs", headers=headers)
    assert r.status_code == 200