
# 🧱 Backend Overview

## ⚙️ Local Test Setup

### 🧩 1. Start Firebase Emulators

#### 🔐 Login to Firebase CLI

If this is your first time using Firebase CLI, log in with:

```bash
firebase login --reauth
```

#### 🧱 Initialize Firebase Emulators

Run:

```bash
firebase init emulators
```

When prompted, choose:

1. **Authentication Emulator**
2. **Firestore Emulator**
3. **Storage Emulator**

Example output:

```
i  Using project expensense-8110a (expenSense)
✔  Firebase initialization complete!
```

#### ▶️ Start the Emulators

```bash
firebase emulators:start
```

Once everything is running, you should see:

```
✔  All emulators ready! It is now safe to connect your app.
i  View Emulator UI at http://127.0.0.1:4000/
```

Then open your browser and check the local emulator UI:
👉 [http://127.0.0.1:4000](http://127.0.0.1:4000)

---

### 🖥️ 2. Start the Local FastAPI Server

Open a **new terminal** and run:

```bash
uvicorn app:app --host 0.0.0.0 --port 8081 --reload
```

Then visit:
👉 [http://0.0.0.0:8081/docs](http://0.0.0.0:8081/docs)
This will open the **Swagger UI** for testing your API.

---

### 🔑 3. Test Authentication with Firebase Emulator

1. Go to the **Authentication** section in the Firebase Emulator UI.
2. Create a new test user (e.g. `yzeng@scu.edu` with password `123456`).

Then make sure your `test/get_token.py` file matches this user:

```python
data = {
    "email": "yzeng@scu.edu",
    "password": "123456",
    "returnSecureToken": True
}
```

Run the script to obtain an ID token:

```bash
python3 test/get_token.py
```

You should see a JSON response.
Copy the value of **idToken** from the output, for example:

```
"idToken": "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0...."
```

Paste that token into the **“Authorize”** dialog in Swagger UI
(upper right corner, 🔒 button).
