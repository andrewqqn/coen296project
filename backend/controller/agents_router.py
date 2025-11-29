"""
Agents Router - Endpoints for multi-agent system
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional
from pydantic import BaseModel

from infrastructure.auth_middleware import verify_firebase_token
from services.multi_agent_orchestrator import (
    process_query_with_agents,
    list_registered_agents,
    get_agent_card
)
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/agents", tags=["Multi-Agent System"])


class AgentQueryRequest(BaseModel):
    """Request model for agent queries"""
    query: str
    message_history: Optional[List[dict]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Review expense exp_123",
                "message_history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi! How can I help?"}
                ]
            }
        }


class AgentQueryResponse(BaseModel):
    """Response model for agent queries"""
    success: bool
    response: Optional[str] = None
    agents_used: List[str] = []
    query: str
    error: Optional[str] = None


@router.get("/registry", summary="List All Registered Agents")
async def get_agent_registry(
    user_claims: dict = Depends(verify_firebase_token)
):
    """
    Get a list of all registered agents and their capabilities.
    This shows the "agent cards" that advertise what each agent can do.
    """
    try:
        agents = list_registered_agents()
        return {
            "success": True,
            "agents": agents,
            "count": len(agents)
        }
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registry/{agent_id}", summary="Get Agent Card")
async def get_agent_info(
    agent_id: str,
    user_claims: dict = Depends(verify_firebase_token)
):
    """
    Get the capability card for a specific agent.
    """
    try:
        card = get_agent_card(agent_id)
        if not card:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
        
        return {
            "success": True,
            "agent": card
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent card: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=AgentQueryResponse, summary="Process Query with Multi-Agent System")
async def process_agent_query(
    request: AgentQueryRequest,
    user_claims: dict = Depends(verify_firebase_token)
):
    """
    Process a natural language query using the multi-agent system.
    
    The orchestrator will coordinate with specialized agents:
    - Expense Agent: Reviews expenses, applies policy rules
    - Document Agent: Processes receipts, extracts information
    
    Examples:
    - "Review expense exp_123"
    - "Extract information from receipt at local://uploads/receipts/user1/file.pdf"
    - "Process the receipt and create an expense"
    """
    try:
        auth_uid = user_claims.get("uid")
        
        # Look up employee by authentication_id (Firebase Auth UID)
        from services import employee_service
        employee = employee_service.get_employee_by_auth_id(auth_uid)
        
        # Debug logging
        logger.info(f"[RBAC DEBUG] user_claims: {user_claims}")
        logger.info(f"[RBAC DEBUG] auth_uid from claims: {auth_uid}")
        logger.info(f"[RBAC DEBUG] employee from DB: {employee}")
        
        if not employee:
            logger.error(f"[RBAC DEBUG] No employee found for auth_uid: {auth_uid}")
            raise HTTPException(status_code=404, detail="Employee not found for this user")
        
        employee_id = employee.get("employee_id")
        role = employee.get("role", "employee")
        
        logger.info(f"[RBAC DEBUG] employee_id: {employee_id}, role: {role}")
        logger.info(f"Processing agent query from {role} user {employee_id}: {request.query}")
        
        result = await process_query_with_agents(
            query=request.query,
            employee_id=employee_id,
            role=role,
            message_history=request.message_history
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Error processing query: {result.get('error', 'Unknown error')}"
            )
        
        return AgentQueryResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent query endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query-with-files", response_model=AgentQueryResponse, summary="Process Query with File Uploads")
async def process_agent_query_with_files(
    query: str = Form(...),
    files: List[UploadFile] = File(None),
    user_claims: dict = Depends(verify_firebase_token)
):
    """
    Process a natural language query with file uploads (e.g., PDF receipts).
    
    The system will:
    1. Upload the files to storage
    2. Process the query with the orchestrator
    3. Coordinate with specialized agents as needed
    
    Example: Upload a receipt PDF and ask "Extract information from this receipt and create an expense"
    """
    try:
        auth_uid = user_claims.get("uid")
        
        # Look up employee by authentication_id (Firebase Auth UID)
        from services import employee_service
        employee = employee_service.get_employee_by_auth_id(auth_uid)
        
        # Debug logging
        logger.info(f"[RBAC DEBUG FILES] auth_uid from claims: {auth_uid}")
        logger.info(f"[RBAC DEBUG FILES] employee from DB: {employee}")
        
        if not employee:
            logger.error(f"[RBAC DEBUG FILES] No employee found for auth_uid: {auth_uid}")
            raise HTTPException(status_code=404, detail="Employee not found for this user")
        
        employee_id = employee.get("employee_id")
        role = employee.get("role", "employee")
        
        logger.info(f"[RBAC DEBUG FILES] employee_id: {employee_id}, role: {role}")
        logger.info(f"Processing agent query with files from {role} user {employee_id}")
        
        result = await process_query_with_agents(
            query=query,
            employee_id=employee_id,
            role=role,
            files=files
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Error processing query: {result.get('error', 'Unknown error')}"
            )
        
        return AgentQueryResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent query with files endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
