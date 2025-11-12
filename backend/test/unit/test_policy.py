import pytest, requests
created_policy_id = None

@pytest.mark.unit
def test_create_policy(base_url, headers):
    payload = {"policy_id": "POL001", "category": "Travel", "max_amount": 200.0, "eligible_roles": ["admin", "employee"], "description": "Travel policy", "active": True}
    r = requests.post(f"{base_url}/policies", json=payload, headers=headers)
    assert r.status_code == 201
    global created_policy_id
    created_policy_id = payload["policy_id"]

@pytest.mark.unit
def test_get_policies(base_url, headers):
    r = requests.get(f"{base_url}/policies", headers=headers)
    assert r.status_code == 200

@pytest.mark.unit
def test_update_policy(base_url, headers):
    global created_policy_id
    payload = {"max_amount": 250.0, "description": "Updated"}
    r = requests.patch(f"{base_url}/policies/{created_policy_id}", json=payload, headers=headers)
    assert r.status_code == 200