"""
Orchestrator Router - Natural language query endpoint using Pydantic AI
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Body, Request
from pydantic import BaseModel
from typing import Optional, List, Literal
import json
from infrastructure.auth_middleware import verify_firebase_token
from domain.services.orchestrator_service import process_query
from domain.services import employee_service
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/orchestrator", tags=["Orchestrator"])


class Message(BaseModel):
    """Message model for conversation history"""
    role: str  # "user" or "assistant"
    content: str


class QueryRequest(BaseModel):
    """Request model for natural language queries"""
    query: str
    message_history: Optional[List[Message]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me all employees",
                "message_history": [
                    {"role": "user", "content": "List all expenses"},
                    {"role": "assistant", "content": "Here are all the expenses..."}
                ]
            }
        }


class QueryResponse(BaseModel):
    """Response model for orchestrator queries"""
    success: bool
    response: str | None = None
    tools_used: list[str] = []
    query: str
    error: str | None = None
    user_role: str | None = None


# Support both `/orchestrator` and `/orchestrator/` so frontend trailing slashes work
@router.options("")
@router.options("/")
async def orchestrate_options():
    """Handle CORS preflight request"""
    return {}


@router.post("", response_model=QueryResponse, summary="Process Natural Language Query")
@router.post("/", response_model=QueryResponse, include_in_schema=False)
async def orchestrate_query(
    request: Request,
    user_claims: dict = Depends(verify_firebase_token)
):
    """
    Process a natural language query and route it to the appropriate tools.
    
    The orchestrator uses GPT-4 to understand the user's intent and automatically
    calls the necessary functions to fulfill the request.
    
    Supports both JSON requests (without files) and multipart/form-data (with PDF attachments).
    
    Examples of queries:
    - "List all employees"
    - "Show me the expense with ID abc123"
    - "Create a new employee named John Doe with email john@example.com"
    - "What are all the reimbursement policies?"
    - "Show me recent audit logs"
    - "Update employee emp123 to change their department to Engineering"
    - "Create an expense from this receipt" (with PDF attachment)
    """
    try:
        # Get user authentication ID from Firebase token
        auth_id = user_claims.get('uid')
        if not auth_id:
            raise HTTPException(status_code=401, detail="User authentication ID not found")
        
        # Look up employee record to get employee_id and role
        # First, try to find employee by authentication_id
        all_employees = employee_service.list_employees()
        employee = None
        for emp in all_employees:
            if emp.get('authentication_id') == auth_id:
                employee = emp
                break
        
        if not employee:
            raise HTTPException(
                status_code=404, 
                detail=f"Employee record not found for authentication ID: {auth_id}. Please ensure the user is registered as an employee."
            )
        
        employee_id = employee.get('employee_id')
        role: Literal["employee", "admin"] = employee.get('role', 'employee')
        
        logger.info(f"User {auth_id} mapped to employee {employee_id} with role {role}")
        
        content_type = request.headers.get("content-type", "")
        logger.info(f"Received request with Content-Type: {content_type}")
        
        # Handle multipart/form-data (with files)
        if "multipart/form-data" in content_type:
            form = await request.form()
            logger.info(f"Form keys: {list(form.keys())}")
            
            query = str(form.get("query", ""))
            message_history_str = form.get("message_history")
            files_raw = form.getlist("files")
            
            logger.info(f"Raw files from form: {files_raw}")
            logger.info(f"Number of raw files: {len(files_raw)}")
            
            # Files from form.getlist are already UploadFile objects, just filter out empty strings
            files: List[UploadFile] = []
            for f in files_raw:
                if f and hasattr(f, 'filename') and hasattr(f, 'read'):
                    files.append(f)  # type: ignore
            
            logger.info(f"Filtered UploadFile objects: {len(files)}")
            for i, f in enumerate(files):
                logger.info(f"File {i}: {f.filename}, content_type: {f.content_type}")
            
            if not query:
                raise HTTPException(status_code=422, detail="Query field is required")
            
            # Parse message history if provided
            message_history_dicts = None
            if message_history_str and isinstance(message_history_str, str):
                try:
                    message_history_dicts = json.loads(message_history_str)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse message_history JSON")
            
            logger.info(f"Received query from employee {employee_id} ({role}): {query}")
            logger.info(f"Received {len(files)} file(s)")
            
            # Process the query with files
            result = await process_query(
                query=query,
                employee_id=employee_id,
                role=role,
                message_history=message_history_dicts,
                files=files if files else None
            )
        
        # Handle application/json (without files)
        else:
            body = await request.json()
            query = body.get("query")
            message_history = body.get("message_history")
            
            if not query:
                raise HTTPException(status_code=422, detail="Query field is required")
            
            logger.info(f"Received query from employee {employee_id} ({role}): {query}")
            
            # Process the query without files
            result = await process_query(
                query=query,
                employee_id=employee_id,
                role=role,
                message_history=message_history,
                files=None
            )
        
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
