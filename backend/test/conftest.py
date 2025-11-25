import pytest, requests, json
import base64

BASE_URL = "http://localhost:8081"
FIREBASE_EMULATOR_URL = (
    "http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=fake-api-key"
)

@pytest.fixture(scope="session")
def firebase_auth():
    data = {"email": "yzeng@scu.edu", "password": "123456", "returnSecureToken": True}
    r = requests.post(FIREBASE_EMULATOR_URL, json=data)
    assert r.status_code == 200, f"Login failed: {r.text}"
    resp = r.json()
    token = resp["idToken"]

    try:
        payload_b64 = token.split(".")[1] + "=="
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
        uid = payload.get("user_id") or payload.get("sub")
    except Exception as e:
        print("Failed to decode token:", e)
        uid = None

    return {"token": token, "uid": uid}

@pytest.fixture
def headers(firebase_auth):
    return {"Authorization": f"Bearer {firebase_auth['token']}"}

@pytest.fixture(scope="session")
def authentication_id(firebase_auth):
    return firebase_auth["uid"]

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

@pytest.fixture(scope="session")
def store():
    return {}
