import requests

#  emulator login endpoint
url = "http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=fake-api-key"

data = {
    "email": "yzeng@scu.edu",
    "password": "123456",
    "returnSecureToken": True
}

r = requests.post(url, json=data)
print(r.json()['idToken'])
