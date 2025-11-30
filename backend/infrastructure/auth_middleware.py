# backend/infrastructure/auth_middleware.py
import os
import requests
import logging
from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)


def verify_firebase_token(authorization: str = Header(...)):
    logger.info("verify_firebase_token called")
    if not authorization:
        logger.error("No Authorization header provided")
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    logger.debug(f"Authorization header length: {len(authorization)}")
    if not authorization.startswith("Bearer "):
        logger.error("Authorization header does not start with 'Bearer '")
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.split(" ")[1]
    use_emulator = os.getenv("USE_FIRESTORE_EMULATOR", "false").lower() == "true"
    logger.info(f"verify_firebase_token: use_emulator={use_emulator}")

    # Emulator
    if use_emulator:
        try:
            r = requests.post(
                "http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:lookup?key=fake-api-key",
                json={"idToken": token},
                timeout=5
            )
            if r.status_code != 200:
                logger.error(f"Emulator token lookup failed: {r.status_code} {r.text}")
                raise HTTPException(status_code=401, detail=f"Invalid token: {r.text}")
            user_info = r.json()["users"][0]
            logger.info(f"Emulator auth succeeded for uid={user_info.get('localId')}")
            return {
                "uid": user_info["localId"],
                "email": user_info.get("email"),
                "emulator": True
            }
        except Exception as e:
            logger.exception("Emulator auth failed")
            raise HTTPException(status_code=401, detail=f"Emulator auth failed: {e}")

    else:
        from firebase_admin import auth
        try:
            decoded = auth.verify_id_token(token)
            logger.info(f"Production auth verified uid={decoded.get('uid')}")
            return {"uid": decoded["uid"], "email": decoded.get("email")}
        except Exception as e:
            logger.exception("Production token verification failed")
            raise HTTPException(status_code=401, detail=f"Invalid token (prod): {e}")
