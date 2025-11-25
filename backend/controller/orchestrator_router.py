"""
Orchestrator Router - Natural language query endpoint using Pydantic AI
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from infrastructure.auth_middleware import verify_firebase_token
from services.orchestrator_service import process_query
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/orchestrator", tags=["Orchestrator"])


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


@router.post("", response_model=QueryResponse, summary="Process Natural Language Query")
@router.post("/", response_model=QueryResponse, include_in_schema=False)
async def orchestrate_query(
    request: QueryRequest,
    user_claims: dict = Depends(verify_firebase_token)
):
    """
    Process a natural language query and route it to the appropriate tools.
    
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
        logger.info(f"Received query from user {user_claims.get('uid')}: {request.query}")
        
        # Process the query using Pydantic AI
        result = await process_query(request.query)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Error processing query: {result.get('error', 'Unknown error')}"
            )
        
        return QueryResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in orchestrator endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
