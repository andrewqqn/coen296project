"""
Orchestrator Router - Natural language query endpoint
LEGACY ENDPOINT - Redirects to new multi-agent system
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from infrastructure.auth_middleware import verify_firebase_token
from services.multi_agent_orchestrator import process_query_with_agents
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/orchestrator", tags=["Orchestrator (Legacy)"])


class QueryRequest(BaseModel):
    """Request model for natural language queries"""
    query: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me all employees"
            }
        }


class QueryResponse(BaseModel):
    """Response model for orchestrator queries"""
    success: bool
    response: str | None = None
    tools_used: list[str] = []
    query: str
    error: str | None = None


# Support both `/orchestrator` and `/orchestrator/` so frontend trailing slashes work
@router.options("")
@router.options("/")
async def orchestrate_options():
    """Handle CORS preflight request"""
    return {}


@router.post("", response_model=QueryResponse, summary="Process Natural Language Query (Legacy)")
@router.post("/", response_model=QueryResponse, include_in_schema=False)
async def orchestrate_query(
    request: QueryRequest,
    user_claims: dict = Depends(verify_firebase_token)
):
    """
    Process a natural language query and route it to the appropriate tools.
    
    **LEGACY ENDPOINT**: This endpoint now uses the new multi-agent system.
    For new integrations, use `/agents/query` instead.
    
    The orchestrator uses GPT-4 to understand the user's intent and automatically
    calls the necessary functions to fulfill the request.
    
    Examples of queries:
    - "List all employees"
    - "Show me the expense with ID abc123"
    - "Create a new employee named John Doe with email john@example.com"
    - "What are all the reimbursement policies?"
    - "Show me recent audit logs"
    - "Update employee emp123 to change their department to Engineering"
    """
    try:
        firebase_uid = user_claims.get("uid")
        role = user_claims.get("role", "employee")
        
        # Convert Firebase UID to internal employee_id
        from services import employee_service
        employee = employee_service.get_employee_by_auth_id(firebase_uid)
        if not employee:
            raise HTTPException(
                status_code=404,
                detail="Employee profile not found. Please contact an administrator."
            )
        
        employee_id = employee.get("employee_id")
        
        logger.info(f"[LEGACY] Received query from user {employee_id} (Firebase UID: {firebase_uid}): {request.query}")
        logger.info(f"[LEGACY] Redirecting to multi-agent system")
        
        # Use the new multi-agent system
        result = await process_query_with_agents(
            query=request.query,
            employee_id=employee_id,
            role=role
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Error processing query: {result.get('error', 'Unknown error')}"
            )
        
        # Map new response format to legacy format
        return QueryResponse(
            success=result["success"],
            response=result.get("response"),
            tools_used=result.get("agents_used", []),  # Map agents_used to tools_used
            query=result["query"],
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in orchestrator endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
