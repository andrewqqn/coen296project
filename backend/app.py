import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi

from dotenv import load_dotenv
load_dotenv()

from infrastructure.firebase_client import init_firebase
init_firebase()

from firebase_admin import auth

from controller import employee_router, expense_router, audit_router, document_router, agents_router, bank_account_router
from application import orchestrator_router

security = HTTPBearer(auto_error=False)
USE_AUTH_EMULATOR = os.getenv("USE_FIRESTORE_EMULATOR")

import logging
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            f"{LOG_DIR}/app.log",
            maxBytes=5_000_000,
            backupCount=3,
            encoding="utf-8",
        )
    ]
)


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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Register routers
app.include_router(employee_router.router)
app.include_router(expense_router.router)
app.include_router(audit_router.router)
app.include_router(document_router.router)
app.include_router(bank_account_router.router)
app.include_router(orchestrator_router.router)
app.include_router(agents_router.router)


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

from infrastructure.chroma_client import init_chroma_policy_client

chroma_client = init_chroma_policy_client()

collection = chroma_client.get_or_create_collection()
if collection.count() == 0:
    print("No Chroma data found → loading policy PDF now...")
    chroma_client.store_policy_pdf()
else:
    print(f"Chroma loaded with {collection.count()} chunks")

# Initialize multi-agent system
print("Initializing multi-agent system...")
from services.agents import expense_agent_service, document_agent_service, orchestrator_agent
from services.agents.a2a_protocol import agent_registry

registered_agents = agent_registry.list_agents()
print(f"✓ Multi-agent system initialized with {len(registered_agents)} agents:")
for agent in registered_agents:
    print(f"  - {agent.name} ({agent.agent_id}): {len(agent.capabilities)} capabilities")


