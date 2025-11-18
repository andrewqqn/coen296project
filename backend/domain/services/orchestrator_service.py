"""
Orchestrator service using Pydantic AI to route natural language queries to appropriate tools.
"""
from typing import Any, Dict, List, Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart
)
from fastapi import UploadFile
import os
import uuid
from utils.logger import get_logger
from infrastructure.firebase_client import get_storage_bucket

# Import all service functions
from domain.services import employee_service, expense_service, policy_service, audit_service

logger = get_logger(__name__)

# Initialize the OpenAI model for Pydantic AI
# Note: Pass the model name directly, API key will be read from environment
model = OpenAIResponsesModel('gpt-4o')

# Create the agent with system prompt
agent = Agent(
    model=model,
    system_prompt="""You are an intelligent assistant for an Expense Reimbursement System.
    You help users manage employees, expenses, reimbursement policies, and audit logs.
    
    When a user asks a question, analyze their intent and use the appropriate tools to help them.
    You can:
    - List, create, update, or delete employees
    - List, create, update, or delete expenses
    - List, create, update, or delete reimbursement policies
    - List or create audit logs
    - Process PDF receipts to extract expense information and create expense records
    
    When a user uploads a PDF receipt and asks to create an expense, use the process_receipt_document
    tool to extract information from the receipt, then use create_new_expense to create the expense record.
    
    Always provide clear, helpful responses based on the data retrieved."""
)

# Define tools for employee operations
@agent.tool
def list_all_employees(ctx: RunContext[None]) -> List[Dict[str, Any]]:
    """
    List all employees in the system.
    Use this when the user wants to see all employees or asks about employee information.
    """
    logger.info("Tool called: list_all_employees")
    return employee_service.list_employees()

@agent.tool
def get_employee_by_id(ctx: RunContext[None], emp_id: str) -> Optional[Dict[str, Any]]:
    """
    Get details of a specific employee by their ID.
    
    Args:
        emp_id: The employee ID to look up
    """
    logger.info(f"Tool called: get_employee_by_id with emp_id={emp_id}")
    return employee_service.get_employee(emp_id)

@agent.tool
def create_new_employee(ctx: RunContext[None], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new employee in the system.
    
    Args:
        data: Employee data including name, email, department, etc.
    """
    logger.info(f"Tool called: create_new_employee with data={data}")
    return employee_service.create_employee(data)

@agent.tool
def update_existing_employee(ctx: RunContext[None], emp_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing employee's information.
    
    Args:
        emp_id: The employee ID to update
        data: Updated employee data
    """
    logger.info(f"Tool called: update_existing_employee with emp_id={emp_id}, data={data}")
    return employee_service.update_employee(emp_id, data)

@agent.tool
def delete_existing_employee(ctx: RunContext[None], emp_id: str) -> Dict[str, Any]:
    """
    Delete an employee from the system.
    
    Args:
        emp_id: The employee ID to delete
    """
    logger.info(f"Tool called: delete_existing_employee with emp_id={emp_id}")
    return employee_service.delete_employee(emp_id)

# Define tools for expense operations
@agent.tool
def list_all_expenses(ctx: RunContext[None]) -> List[Dict[str, Any]]:
    """
    List all expenses in the system.
    Use this when the user wants to see all expenses or asks about expense information.
    """
    logger.info("Tool called: list_all_expenses")
    return expense_service.list_expenses()

@agent.tool
def get_expense_by_id(ctx: RunContext[None], expense_id: str) -> Optional[Dict[str, Any]]:
    """
    Get details of a specific expense by its ID.
    
    Args:
        expense_id: The expense ID to look up
    """
    logger.info(f"Tool called: get_expense_by_id with expense_id={expense_id}")
    return expense_service.get_expense(expense_id)

@agent.tool
def create_new_expense(
    ctx: RunContext[None], 
    employee_id: str,
    amount: float,
    category: str,
    description: str = "",
    receipt_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new expense in the system.
    
    Args:
        employee_id: The employee ID who is submitting the expense
        amount: The expense amount (numeric value only, no currency symbols)
        category: The expense category (e.g., meals, transportation, office_supplies, lodging, other)
        description: Brief description of the expense
        receipt_url: Optional URL to the receipt document
    """
    data = {
        "employee_id": employee_id,
        "amount": amount,
        "category": category,
        "description": description
    }
    if receipt_url:
        data["receipt_url"] = receipt_url
    
    logger.info(f"Tool called: create_new_expense with data={data}")
    return expense_service.create_expense(data)

@agent.tool
def update_existing_expense(ctx: RunContext[None], expense_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing expense's information.
    
    Args:
        expense_id: The expense ID to update
        data: Updated expense data
    """
    logger.info(f"Tool called: update_existing_expense with expense_id={expense_id}, data={data}")
    return expense_service.update_expense(expense_id, data)

@agent.tool
def delete_existing_expense(ctx: RunContext[None], expense_id: str) -> Dict[str, Any]:
    """
    Delete an expense from the system.
    
    Args:
        expense_id: The expense ID to delete
    """
    logger.info(f"Tool called: delete_existing_expense with expense_id={expense_id}")
    return expense_service.delete_expense(expense_id)

# Define tools for policy operations
@agent.tool
def list_all_policies(ctx: RunContext[None]) -> List[Dict[str, Any]]:
    """
    List all reimbursement policies in the system.
    Use this when the user wants to see all policies or asks about policy information.
    """
    logger.info("Tool called: list_all_policies")
    return policy_service.list_policies()

@agent.tool
def create_new_policy(ctx: RunContext[None], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new reimbursement policy in the system.
    
    Args:
        data: Policy data including name, rules, limits, etc.
    """
    logger.info(f"Tool called: create_new_policy with data={data}")
    return policy_service.create_policy(data)

@agent.tool
def update_existing_policy(ctx: RunContext[None], policy_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing policy's information.
    
    Args:
        policy_id: The policy ID to update
        data: Updated policy data
    """
    logger.info(f"Tool called: update_existing_policy with policy_id={policy_id}, data={data}")
    return policy_service.update_policy(policy_id, data)

@agent.tool
def delete_existing_policy(ctx: RunContext[None], policy_id: str) -> Dict[str, Any]:
    """
    Delete a policy from the system.
    
    Args:
        policy_id: The policy ID to delete
    """
    logger.info(f"Tool called: delete_existing_policy with policy_id={policy_id}")
    return policy_service.delete_policy(policy_id)

# Define tools for audit log operations
@agent.tool
def list_all_audit_logs(ctx: RunContext[None]) -> List[Dict[str, Any]]:
    """
    List all audit logs in the system.
    Use this when the user wants to see system activity or audit trail.
    """
    logger.info("Tool called: list_all_audit_logs")
    return audit_service.list_logs()

@agent.tool
def create_audit_log(ctx: RunContext[None], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new audit log entry.
    
    Args:
        data: Audit log data including action, user, timestamp, etc.
    """
    logger.info(f"Tool called: create_audit_log with data={data}")
    return audit_service.create_log(data)


@agent.tool
def process_receipt_document(ctx: RunContext[None], file_url: str, employee_id: str) -> Dict[str, Any]:
    """
    Process a PDF receipt document to extract expense information using AI.
    This tool analyzes receipts to extract vendor, amount, date, category, and description.
    
    Args:
        file_url: URL or path to the uploaded receipt PDF (format: local://path/to/file.pdf)
        employee_id: The employee ID who is submitting the expense
        
    Returns:
        Dictionary with extracted expense information that can be used to create an expense
    """
    logger.info(f"Tool called: process_receipt_document with file_url={file_url}, employee_id={employee_id}")
    
    try:
        from infrastructure.llm_client import run_llm_prompt
        import PyPDF2
        
        # Extract text from PDF
        pdf_text = ""
        
        # Handle local:// URLs (emulator mode)
        if file_url.startswith("local://"):
            # Convert local:// URL to actual file path
            local_path = file_url.replace("local://", "")
            full_path = os.path.join(os.getcwd(), local_path)
            
            logger.info(f"Reading PDF from local path: {full_path}")
            
            if not os.path.exists(full_path):
                logger.error(f"File not found: {full_path}")
                return {
                    "success": False,
                    "error": f"File not found: {full_path}",
                    "message": "Receipt file not found"
                }
            
            # Extract text from PDF
            with open(full_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                logger.info(f"PDF has {len(pdf_reader.pages)} page(s)")
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    pdf_text += page.extract_text() + "\n"
        else:
            # Handle remote URLs (production mode)
            # For production, you'd need to download the file first
            logger.warning("Remote URL processing not yet implemented")
            return {
                "success": False,
                "error": "Remote URL processing not implemented",
                "message": "Can only process local files in emulator mode"
            }
        
        logger.info(f"Extracted {len(pdf_text)} characters from PDF")
        logger.info(f"PDF text preview: {pdf_text[:500]}...")
        
        # Use LLM to extract structured information from the text
        prompt = f"""Analyze this receipt text and extract the following information in a structured format:

Receipt Text:
{pdf_text}

Please extract:
1. Vendor/merchant name
2. Total amount (just the number, no currency symbol)
3. Date of transaction (in YYYY-MM-DD format if possible)
4. Category (choose one: meals, transportation, office_supplies, lodging, entertainment, other)
5. Brief description (one sentence summary)

Return ONLY a JSON object with these exact keys: vendor, amount, date, category, description
Do not include any other text or explanation."""
        
        extracted_info = run_llm_prompt(prompt)
        
        logger.info(f"Extracted info: {extracted_info}")
        
        return {
            "success": True,
            "extracted_info": extracted_info,
            "file_url": file_url,
            "employee_id": employee_id,
            "pdf_text_preview": pdf_text[:500],
            "message": "Receipt processed successfully. You can now create an expense with this information."
        }
        
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to process receipt document"
        }


async def upload_file_to_storage(file: UploadFile, user_id: str) -> str:
    """
    Upload a file to Firebase Storage and return the public URL.
    In emulator mode, saves files locally and returns a local path.
    
    Args:
        file: The uploaded file
        user_id: The user ID for organizing files
        
    Returns:
        Public URL of the uploaded file (or local path in emulator mode)
    """
    try:
        from config import USE_FIRESTORE_EMULATOR, FIREBASE_STORAGE_EMULATOR_HOST
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.pdf'
        unique_filename = f"receipts/{user_id}/{uuid.uuid4()}{file_extension}"
        
        # Read file content
        content = await file.read()
        
        # Check if we're using emulator
        if USE_FIRESTORE_EMULATOR:
            logger.info("Using emulator mode - saving file locally")
            
            # Save file locally for emulator mode
            local_dir = os.path.join(os.getcwd(), "uploads", "receipts", user_id)
            os.makedirs(local_dir, exist_ok=True)
            
            local_filename = f"{uuid.uuid4()}{file_extension}"
            local_path = os.path.join(local_dir, local_filename)
            
            with open(local_path, 'wb') as f:
                f.write(content)
            
            # Return a local reference
            file_url = f"local://uploads/receipts/{user_id}/{local_filename}"
            logger.info(f"File saved locally: {local_path}")
            return file_url
        else:
            # Production mode - upload to Firebase Storage
            bucket = get_storage_bucket()
            blob = bucket.blob(unique_filename)
            
            # Upload to Firebase Storage
            blob.upload_from_string(content, content_type=file.content_type or 'application/pdf')
            
            # Make the blob publicly accessible (optional, adjust based on your security requirements)
            blob.make_public()
            
            logger.info(f"File uploaded to Firebase Storage: {unique_filename}")
            return blob.public_url
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise


async def process_query(
    query: str, 
    message_history: Optional[List[Dict[str, str]]] = None,
    files: Optional[List[UploadFile]] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a natural language query using Pydantic AI agent.
    
    Args:
        query: Natural language query from the user
        message_history: Optional list of previous messages in the format:
            [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        files: Optional list of uploaded files (e.g., PDF receipts)
        user_id: Optional user ID for file uploads
        
    Returns:
        Dictionary containing the response and metadata
    """
    try:
        logger.info(f"Processing query: {query}")
        
        # Handle file uploads if present
        uploaded_file_urls = []
        if files and len(files) > 0:
            logger.info(f"Processing {len(files)} uploaded file(s)")
            for file in files:
                if file.filename:
                    logger.info(f"Uploading file: {file.filename}")
                    file_url = await upload_file_to_storage(file, user_id or "anonymous")
                    uploaded_file_urls.append(file_url)
                    logger.info(f"File uploaded: {file_url}")
            
            # Enhance the query with file information
            if uploaded_file_urls:
                file_info = "\n".join([f"- Receipt PDF uploaded: {url}" for url in uploaded_file_urls])
                enhanced_query = f"{query}\n\nAttached files:\n{file_info}"
                if user_id:
                    enhanced_query += f"\n\nEmployee ID: {user_id}"
                query = enhanced_query
                logger.info(f"Enhanced query with file info: {query}")
        
        # Convert message history to Pydantic AI's ModelMessage format
        pydantic_history: List[ModelMessage] = []
        if message_history:
            for msg in message_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "user":
                    pydantic_history.append(ModelRequest(parts=[UserPromptPart(content=content)]))
                elif role == "assistant":
                    pydantic_history.append(ModelResponse(parts=[TextPart(content=content)]))
        
        # Run the agent with the user's query and conversation history
        if pydantic_history:
            result = await agent.run(query, message_history=pydantic_history)
        else:
            result = await agent.run(query)
        
        # Extract the response - access the output attribute which contains the actual output
        response_text = result.output
        
        # Get information about which tools were called
        tools_used = []
        
        logger.info(f"Query processed successfully. Response length: {len(response_text)}")
        
        return {
            "success": True,
            "response": response_text,
            "tools_used": tools_used,
            "query": query
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "response": None,
            "tools_used": []
        }
