import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi

from infrastructure.firebase_client import init_firebase
init_firebase()

from firebase_admin import auth

from controller import employee_router, expense_router, audit_router, document_router, agents_router, bank_account_router
from application import orchestrator_router

security = HTTPBearer(auto_error=False)

def env_flag(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "y", "on")

USE_AUTH_EMULATOR = env_flag("USE_FIRESTORE_EMULATOR", default=False)


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
        logging.info(f"Using Firebase Auth Emulator: {token}")
        print(f"Using Firebase Auth Emulator: {token}")
        return {
            "uid": f"emu-{token[-8:]}",
            "email": "testuser@emu.local",
            "token_raw": token
        }

    # ---------- Production Mode ----------
    try:
        logging.info(f"Verifying Firebase ID Token: {token}")
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
    "https://expense-back-855319526387.us-central1.run.app"
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
    logging.info("Root endpoint received")
    return {"message": "Expense System (CRUD + Agents) running 🚀"}

@app.get("/health")
def health_check():
    logging.info("Health check received")
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


