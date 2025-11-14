# backend/infrastructure/auth_middleware.py
import os
import requests
from fastapi import Header, HTTPException


def verify_firebase_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.split(" ")[1]
    use_emulator = os.getenv("USE_FIRESTORE_EMULATOR", "false").lower() == "true"

    # Emulator
    if use_emulator:
        try:
            r = requests.post(
                "http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:lookup?key=fake-api-key",
                json={"idToken": token},
                timeout=5
            )
            if r.status_code != 200:
                raise HTTPException(status_code=401, detail=f"Invalid token: {r.text}")
            user_info = r.json()["users"][0]
            return {
                "uid": user_info["localId"],
                "email": user_info.get("email"),
                "emulator": True
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Emulator auth failed: {e}")

    else:
        from firebase_admin import auth
        try:
            decoded = auth.verify_id_token(token)
            return {"uid": decoded["uid"], "email": decoded.get("email")}
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token (prod): {e}")
