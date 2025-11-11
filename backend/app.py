from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.openapi.utils import get_openapi
from application import employee_router, expense_router, policy_router, audit_router, agent_router

security = HTTPBearer(auto_error=False)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    return credentials.credentials  # 或替换为 Firebase 验证

app = FastAPI(
    title="Expense Reimbursement System (CRUD + Agents)",
    description="All requests require a Firebase ID Token after Google Sign-In.",
    version="1.0.0",
)

# ✅ 挂载 routers（不需要额外 Depends）
app.include_router(employee_router.router)
app.include_router(expense_router.router)
app.include_router(policy_router.router)
app.include_router(audit_router.router)
app.include_router(agent_router.router)

@app.get("/")
def root():
    return {"message": "Expense System (CRUD + Agents) running 🚀"}

# ✅ 自定义 OpenAPI schema — 添加全局 Bearer 安全定义
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "firebaseAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste your Firebase ID Token here (from emulator or prod).",
        }
    }
    openapi_schema["security"] = [{"firebaseAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
