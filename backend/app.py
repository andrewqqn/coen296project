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
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://expensense-8110a.web.app",
    "https://expensense-8110a.firebaseapp.com",
]

# Allow any origin in development
if os.getenv("ENVIRONMENT") != "production":
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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

@app.get("/health")
def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy", "service": "expensense-backend"}


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

print("=" * 60)
print("🚀 Starting Expensense Backend")
print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
print(f"Port: {os.getenv('PORT', '8000')}")
print(f"Firebase Project: {os.getenv('FIREBASE_PROJECT_ID')}")
print(f"Using Emulator: {os.getenv('USE_FIRESTORE_EMULATOR', 'false')}")
print("=" * 60)

from infrastructure.chroma_client import init_chroma_policy_client

print("Initializing Chroma vector database...")
try:
    chroma_client = init_chroma_policy_client()
    collection = chroma_client.get_or_create_collection()
    
    # Only load embeddings if collection is empty (defer model download)
    if collection.count() == 0:
        print("No Chroma data found → will load policy PDF on first query")
    else:
        print(f"✓ Chroma loaded with {collection.count()} chunks")
except Exception as e:
    print(f"⚠ Chroma initialization warning: {e}")
    print("  → Chroma will be initialized on first use")

# Initialize multi-agent system
print("Initializing multi-agent system...")
from services.agents import expense_agent_service, document_agent_service, orchestrator_agent, email_agent_service
from services.agents.a2a_protocol import agent_registry

registered_agents = agent_registry.list_agents()
print(f"✓ Multi-agent system initialized with {len(registered_agents)} agents:")
for agent in registered_agents:
    print(f"  - {agent.name} ({agent.agent_id}): {len(agent.capabilities)} capabilities")

print("=" * 60)
print("✅ Backend startup complete - ready to accept requests")
print("=" * 60)


