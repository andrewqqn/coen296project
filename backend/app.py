import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi
from firebase_admin import auth
from dotenv import load_dotenv
from application import employee_router, expense_router, audit_router, document_router

load_dotenv()
security = HTTPBearer(auto_error=False)

print("DEBUG: FIREBASE_STORAGE_EMULATOR_HOST=",
      os.getenv("FIREBASE_STORAGE_EMULATOR_HOST"))
print("DEBUG: USE_FIRESTORE_EMULATOR=",
      os.getenv("USE_FIRESTORE_EMULATOR"))
USE_AUTH_EMULATOR = os.getenv("USE_FIRESTORE_EMULATOR")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Authentication logic:
    - Emulator: accept any token, do NOT verify signature
    - Production: must verify using firebase_admin.auth.verify_id_token()
    """
    if credentials is None:
        raise HTTPException(401, "Missing Authorization header")

    token = credentials.credentials

    # ---------- Emulator Mode ----------
    if USE_AUTH_EMULATOR:
        return {
            "uid": f"emu-{token[-8:]}",
            "email": "testuser@emu.local",
            "token_raw": token
        }

    # ---------- Production Mode ----------
    try:
        decoded = auth.verify_id_token(token)
        return decoded
    except Exception:
        raise HTTPException(401, "Invalid or expired Firebase ID Token")


app = FastAPI(
    title="Expense Reimbursement System (CRUD + Agents)",
    description="All endpoints require a Firebase ID Token.",
    version="1.0.0",
)

# Register routers
app.include_router(employee_router.router)
app.include_router(expense_router.router)
app.include_router(audit_router.router)
app.include_router(document_router.router)


@app.get("/")
def root():
    return {"message": "Expense System (CRUD + Agents) running 🚀"}


# ---------- CUSTOM OPENAPI ----------
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    schema["components"]["securitySchemes"] = {
        "firebaseAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste Firebase ID Token here (Emulator or Production).",
        }
    }

    schema["security"] = [{"firebaseAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi

