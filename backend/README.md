# Backend Overview

# Local Test Setup
## Firebase emulators
### Firebase CLI Login
First time login
```
firebase login --reauth
```

### init Firebase emulators
init emulators
```
firebase init emulators 
```
i  Using project expensense-8110a (expenSense) .

✔ Which Firebase emulators do you want to set up? Press Space to select emulators, then Enter to confirm your choices. Authentication Emulator,
1. Authentication Emulator
2. Firestore Emulator
3. Storage Emulator

### Start emulators
```
firebase emulators:start
```

│ ✔  All emulators ready! It is now safe to connect your app. │
│ i  View Emulator UI at http://127.0.0.1:4000/    

check your local emulators GUI url

## Start local server
open a new terminal

```
uvicorn app:app --host 0.0.0.0 --port 8081 --reload
```

open http://0.0.0.0:8081/docs

go to Authentication tab
create a new user

data in get_token.py should match the user you created
for example:
```
data = {
    "email": "yzeng@scu.edu",
    "password": "123456",
    "returnSecureToken": True
}
```
use test folder's get_token.py to get token
```
python3 test/get_token.py
```

find the idToken in the output

copy the idToken and paste it in the Authentication tab of the swagger UI