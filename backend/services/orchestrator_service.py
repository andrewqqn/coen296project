"""
DEPRECATED: Legacy Orchestrator Service

This file is deprecated and no longer used. The system now uses the multi-agent
architecture in services/multi_agent_orchestrator.py and services/agents/.

The /orchestrator endpoint has been updated to use the new system while maintaining
backward compatibility.

For new development, use:
- services/multi_agent_orchestrator.py
- services/agents/orchestrator_agent.py
- controller/agents_router.py

This file is kept for reference only.
"""
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel
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
from services import employee_service, expense_service, audit_log_service

logger = get_logger(__name__)

# Initialize the OpenAI model for Pydantic AI
# Note: Pass the model name directly, API key will be read from environment
model = OpenAIResponsesModel('gpt-4o')


class UserContext(BaseModel):
    """Context about the current user making the request"""
    employee_id: str
    role: Literal["employee", "admin"]


def create_agent_for_role(role: Literal["employee", "admin"]) -> Agent:
    """
    Create an agent with tools appropriate for the user's role.
    
    Args:
        role: The user's role (employee or admin)
        
    Returns:
        Configured Agent instance
    """
    if role == "admin":
        system_prompt = """You are an intelligent assistant for an Expense Reimbursement System.
You help administrators manage employees, expenses, reimbursement policies, and audit logs.

As an admin assistant, you have full access to:
- List, create, update, or delete employees
- List, create, update, or delete expenses (for all employees)
- List, create, update, or delete reimbursement policies
- List or create audit logs
- Process PDF receipts to extract expense information and create expense records

IMPORTANT: When a user uploads a PDF receipt and asks to create an expense:
1. First call process_receipt_document with the file_url to extract information
2. Then call create_new_expense with the extracted information AND pass the file_url as receipt_url parameter
   Example: create_new_expense(amount=93.50, category="other", description="...", date_of_expense="2016-01-25", receipt_url="local://uploads/receipts/...")

Always provide clear, helpful responses based on the data retrieved."""
    else:
        system_prompt = """You are an intelligent assistant for an Expense Reimbursement System.
You help employees manage their expenses and view reimbursement policies.

As an employee assistant, you can:
- List, create, update, or delete YOUR OWN expenses only
- View expense details for YOUR expenses
- View reimbursement policies
- Process PDF receipts to extract expense information and create expense records

You do NOT have access to:
- Employee management functions
- Other employees' expenses
- Policy management
- Audit logs

IMPORTANT: When a user uploads a PDF receipt and asks to create an expense:
1. First call process_receipt_document with the file_url to extract information
2. Then call create_new_expense with the extracted information AND pass the file_url as receipt_url parameter
   Example: create_new_expense(amount=93.50, category="other", description="...", date_of_expense="2016-01-25", receipt_url="local://uploads/receipts/...")

Always provide clear, helpful responses based on the data retrieved."""
    
    return Agent(
        model=model,
        system_prompt=system_prompt,
        deps_type=UserContext
    )

# Admin-only tools for employee operations
def register_admin_employee_tools(agent: Agent):
    """Register employee management tools (admin only)"""
    
    @agent.tool
    def list_all_employees(ctx: RunContext[UserContext]) -> List[Dict[str, Any]]:
        """
        List all employees in the system.
        Use this when the user wants to see all employees or asks about employee information.
        """
        logger.info("Tool called: list_all_employees")
        return employee_service.list_employees()

    @agent.tool
    def get_employee_by_id(ctx: RunContext[UserContext], emp_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific employee by their ID.
        
        Args:
            emp_id: The employee ID to look up
        """
        logger.info(f"Tool called: get_employee_by_id with emp_id={emp_id}")
        return employee_service.get_employee(emp_id)

    @agent.tool
    def create_new_employee(ctx: RunContext[UserContext], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new employee in the system.
        
        Args:
            data: Employee data including name, email, department, etc.
        """
        logger.info(f"Tool called: create_new_employee with data={data}")
        return employee_service.create_employee(data)

    @agent.tool
    def update_existing_employee(ctx: RunContext[UserContext], emp_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing employee's information.
        
        Args:
            emp_id: The employee ID to update
            data: Updated employee data
        """
        logger.info(f"Tool called: update_existing_employee with emp_id={emp_id}, data={data}")
        return employee_service.update_employee(emp_id, data)

    @agent.tool
    def delete_existing_employee(ctx: RunContext[UserContext], emp_id: str) -> Dict[str, Any]:
        """
        Delete an employee from the system.
        
        Args:
            emp_id: The employee ID to delete
        """
        logger.info(f"Tool called: delete_existing_employee with emp_id={emp_id}")
        return employee_service.delete_employee(emp_id)

# Expense tools (available to both admin and employee, with filtering for employees)
def register_expense_tools(agent: Agent, role: Literal["employee", "admin"]):
    """Register expense management tools with role-based filtering"""
    
    @agent.tool
    def list_all_expenses(ctx: RunContext[UserContext]) -> List[Dict[str, Any]]:
        """
        List all expenses in the system.
        Use this when the user wants to see all expenses or asks about expense information.
        """
        logger.info(f"Tool called: list_all_expenses by {ctx.deps.role} user {ctx.deps.employee_id}")
        all_expenses = expense_service.list_expenses()
        
        # Filter expenses for employee role
        if ctx.deps.role == "employee":
            filtered = [exp for exp in all_expenses if exp.get("employee_id") == ctx.deps.employee_id]
            logger.info(f"Filtered {len(all_expenses)} expenses to {len(filtered)} for employee {ctx.deps.employee_id}")
            return filtered
        
        return all_expenses

    @agent.tool
    def get_expense_by_id(ctx: RunContext[UserContext], expense_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific expense by its ID.
        
        Args:
            expense_id: The expense ID to look up
        """
        logger.info(f"Tool called: get_expense_by_id with expense_id={expense_id} by {ctx.deps.role} user {ctx.deps.employee_id}")
        expense = expense_service.get_expense(expense_id)
        
        # Check access for employee role
        if expense and ctx.deps.role == "employee":
            if expense.get("employee_id") != ctx.deps.employee_id:
                logger.warning(f"Employee {ctx.deps.employee_id} attempted to access expense {expense_id} belonging to {expense.get('employee_id')}")
                return None
        
        return expense

    @agent.tool
    def create_new_expense(
        ctx: RunContext[UserContext], 
        amount: float,
        category: str,
        description: str = "",
        date_of_expense: Optional[str] = None,
        receipt_path: Optional[str] = None,
        employee_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new expense in the system.
        
        Args:
            amount: The expense amount (numeric value only, no currency symbols)
            category: The expense category (choose from: Travel, Meals, Conference, Other)
            description: Brief description/justification of the expense
            date_of_expense: Date of the expense in YYYY-MM-DD format (defaults to today if not provided)
            receipt_path: Optional path to receipt in storage (e.g., "expense_receipts/file.pdf")
            employee_id: The employee ID (only for admin; employees create expenses for themselves)
        """
        from domain.schemas.expense_schema import ExpenseCreate
        from datetime import datetime
        import time
        
        # For employees, always use their own employee_id
        if ctx.deps.role == "employee":
            actual_employee_id = ctx.deps.employee_id
            logger.info(f"Employee {ctx.deps.employee_id} creating expense for themselves")
        else:
            # Admin can specify employee_id or default to their own
            actual_employee_id = employee_id or ctx.deps.employee_id
            logger.info(f"Admin {ctx.deps.employee_id} creating expense for employee {actual_employee_id}")
        
        # Parse date or use today
        if date_of_expense:
            try:
                expense_date = datetime.fromisoformat(date_of_expense)
            except ValueError:
                expense_date = datetime.utcnow()
        else:
            expense_date = datetime.utcnow()
        
        # Normalize category to match schema
        category_map = {
            "meals": "Meals",
            "travel": "Travel",
            "transportation": "Travel",
            "conference": "Conference",
            "other": "Other",
            "office_supplies": "Other",
            "lodging": "Travel",
            "entertainment": "Other"
        }
        normalized_category = category_map.get(category.lower(), "Other")
        
        # Create ExpenseCreate object
        expense_create = ExpenseCreate(
            employee_id=actual_employee_id,
            amount=amount,
            category=normalized_category,
            business_justification=description or "No description provided",
            date_of_expense=expense_date
        )
        
        logger.info(f"Tool called: create_new_expense with data={expense_create.dict()}, receipt_path={receipt_path}")
        
        # Call the unified create_expense function
        result = expense_service.create_expense(expense_create, receipt_path=receipt_path)
        
        # Convert Pydantic model to dict for JSON serialization
        expense_dict = result.dict() if hasattr(result, 'dict') else result
        expense_id = expense_dict.get('expense_id') or expense_dict.get('id')
        
        # Wait for AI review to complete (with timeout)
        logger.info(f"Waiting for AI review to complete for expense {expense_id}")
        max_wait_time = 30  # seconds
        poll_interval = 1  # second
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            time.sleep(poll_interval)
            elapsed_time += poll_interval
            
            # Fetch the updated expense
            updated_expense = expense_service.get_expense(expense_id)
            
            if updated_expense:
                status = updated_expense.get('status')
                decision_actor = updated_expense.get('decision_actor')
                
                # Check if AI has made a decision
                if decision_actor == 'AI' and status in ['approved', 'rejected', 'admin_review']:
                    logger.info(f"AI review completed with status: {status}")
                    
                    # Add review result to the response
                    updated_expense['review_completed'] = True
                    updated_expense['review_status'] = status
                    updated_expense['review_reason'] = updated_expense.get('decision_reason', '')
                    updated_expense['expense_id'] = expense_id
                    
                    return updated_expense
        
        # If we timeout, return the expense with a pending status
        logger.warning(f"AI review timeout for expense {expense_id}")
        expense_dict['review_completed'] = False
        expense_dict['review_status'] = 'pending'
        expense_dict['review_reason'] = 'AI review is taking longer than expected'
        expense_dict['expense_id'] = expense_id
        
        return expense_dict

    @agent.tool
    def update_existing_expense(ctx: RunContext[UserContext], expense_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing expense's information.
        
        Args:
            expense_id: The expense ID to update
            data: Updated expense data
        """
        logger.info(f"Tool called: update_existing_expense with expense_id={expense_id} by {ctx.deps.role} user {ctx.deps.employee_id}")
        
        # Check access for employee role
        if ctx.deps.role == "employee":
            expense = expense_service.get_expense(expense_id)
            if not expense or expense.get("employee_id") != ctx.deps.employee_id:
                logger.warning(f"Employee {ctx.deps.employee_id} attempted to update expense {expense_id} without permission")
                return {"error": "Access denied: You can only update your own expenses"}
        
        return expense_service.update_expense(expense_id, data)

    @agent.tool
    def delete_existing_expense(ctx: RunContext[UserContext], expense_id: str) -> Dict[str, Any]:
        """
        Delete an expense from the system.
        
        Args:
            expense_id: The expense ID to delete
        """
        logger.info(f"Tool called: delete_existing_expense with expense_id={expense_id} by {ctx.deps.role} user {ctx.deps.employee_id}")
        
        # Check access for employee role
        if ctx.deps.role == "employee":
            expense = expense_service.get_expense(expense_id)
            if not expense or expense.get("employee_id") != ctx.deps.employee_id:
                logger.warning(f"Employee {ctx.deps.employee_id} attempted to delete expense {expense_id} without permission")
                return {"error": "Access denied: You can only delete your own expenses"}
        
        return expense_service.delete_expense(expense_id)

# Admin-only audit log tools
def register_audit_tools(agent: Agent):
    """Register audit log tools (admin only)"""
    
    @agent.tool
    def list_all_audit_logs(ctx: RunContext[UserContext]) -> List[Dict[str, Any]]:
        """
        List all audit logs in the system.
        Use this when the user wants to see system activity or audit trail.
        """
        logger.info(f"Tool called: list_all_audit_logs by admin {ctx.deps.employee_id}")
        return audit_log_service.list_logs()

    @agent.tool
    def create_audit_log(ctx: RunContext[UserContext], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new audit log entry.
        
        Args:
            data: Audit log data including action, user, timestamp, etc.
        """
        logger.info(f"Tool called: create_audit_log with data={data}")
        return audit_log_service.create_log(data)


# Receipt processing tool (available to both roles)
def register_receipt_tools(agent: Agent):
    """Register receipt processing tools"""
    
    @agent.tool
    def process_receipt_document(ctx: RunContext[UserContext], file_url: str, employee_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a PDF receipt document to extract expense information using AI vision.
        This tool analyzes receipt images to extract vendor, amount, date, category, and description.
        
        Args:
            file_url: URL or path to the uploaded receipt PDF (format: local://path/to/file.pdf)
            employee_id: The employee ID (only for admin; employees process receipts for themselves)
            
        Returns:
            Dictionary with extracted expense information that can be used to create an expense
        """
        # For employees, always use their own employee_id
        if ctx.deps.role == "employee":
            actual_employee_id = ctx.deps.employee_id
        else:
            actual_employee_id = employee_id or ctx.deps.employee_id
        
        logger.info(f"Tool called: process_receipt_document with file_url={file_url}, employee_id={actual_employee_id}")
        
        try:
            from pdf2image import convert_from_bytes
            from openai import OpenAI
            import base64
            from io import BytesIO
            import json
            
            client = OpenAI()
            
            # Read PDF file
            pdf_bytes = None
            
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
                
                with open(full_path, 'rb') as f:
                    pdf_bytes = f.read()
            else:
                # Handle remote URLs (production mode)
                logger.warning("Remote URL processing not yet implemented")
                return {
                    "success": False,
                    "error": "Remote URL processing not implemented",
                    "message": "Can only process local files in emulator mode"
                }
            
            # Convert PDF to images
            logger.info("Converting PDF to images...")
            pages = convert_from_bytes(pdf_bytes, dpi=100)
            
            if not pages:
                logger.error("PDF converted to zero pages")
                return {
                    "success": False,
                    "error": "PDF conversion failed",
                    "message": "Could not convert PDF to images"
                }
            
            # Convert first page to base64 JPEG
            img = pages[0]
            buf = BytesIO()
            img.save(buf, format="JPEG")
            jpeg_bytes = buf.getvalue()
            base64_image = base64.b64encode(jpeg_bytes).decode("utf-8")
            
            logger.info(f"Converted PDF to {len(pages)} page(s), using first page for analysis")
            
            # Use OpenAI vision API to extract structured information
            prompt = """Analyze this receipt image and extract the following information:

1. Vendor/merchant name
2. Total amount (just the number, no currency symbol)
3. Date of transaction (in YYYY-MM-DD format if possible)
4. Category (choose one: meals, transportation, office_supplies, lodging, entertainment, other)
5. Brief description (one sentence summary)

Return ONLY a valid JSON object with these exact keys: vendor, amount, date, category, description
Do not include any markdown, code blocks, or other text."""
            
            response = client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": [{"type": "input_text", "text": "You are a receipt analysis assistant. Extract structured data from receipt images and return only valid JSON."}]},
                    {"role": "user", "content": [
                        {"type": "input_image", "image_url": f"data:image/jpeg;base64,{base64_image}"},
                        {"type": "input_text", "text": prompt}
                    ]}
                ]
            )
            
            extracted_text = response.output_text.strip()
            logger.info(f"OpenAI response: {extracted_text}")
            
            # Parse the JSON response
            try:
                extracted_info = json.loads(extracted_text)
            except json.JSONDecodeError:
                # If response isn't valid JSON, try to extract it
                logger.warning("Response wasn't valid JSON, attempting to parse")
                extracted_info = {"raw_response": extracted_text}
            
            logger.info(f"Extracted info: {extracted_info}")
            
            return {
                "success": True,
                "extracted_info": extracted_info,
                "file_url": file_url,
                "employee_id": actual_employee_id,
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
        from config import USE_FIRESTORE_EMULATOR, PROJECT_ID, STORAGE_BUCKET

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
            from infrastructure.firebase_client import get_storage_bucket

            storage_path = f"receipts/{user_id}/{unique_filename}"
            logger.info(f"Uploading to storage. PROJECT_ID={PROJECT_ID}, STORAGE_BUCKET={STORAGE_BUCKET}")
            try:
                bucket = get_storage_bucket()
                logger.info(f"Got storage bucket: {getattr(bucket, 'name', '<no-name>')}")
            except Exception as e:
                logger.exception("Failed to get storage bucket")
                raise
            blob = bucket.blob(storage_path)

            # Upload to Firebase Storage
            blob.upload_from_string(content, content_type=file.content_type or 'application/pdf')
            blob.make_public()
            
            logger.info(f"File uploaded to Firebase Storage: {storage_path}")
            return blob.public_url
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise


async def process_query(
    query: str, 
    employee_id: str,
    role: Literal["employee", "admin"] = "employee",
    message_history: Optional[List[Dict[str, str]]] = None,
    files: Optional[List[UploadFile]] = None
) -> Dict[str, Any]:
    """
    Process a natural language query using Pydantic AI agent with role-based access control.
    
    Args:
        query: Natural language query from the user
        employee_id: The employee ID of the user making the request
        role: The user's role (employee or admin)
        message_history: Optional list of previous messages in the format:
            [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        files: Optional list of uploaded files (e.g., PDF receipts)
        
    Returns:
        Dictionary containing the response and metadata
    """
    try:
        logger.info(f"Processing query from {role} user {employee_id}: {query}")
        
        # Create user context
        user_context = UserContext(employee_id=employee_id, role=role)
        
        # Create agent with appropriate tools for the user's role
        agent = create_agent_for_role(role)
        
        # Register tools based on role
        if role == "admin":
            # Admin gets all tools
            register_admin_employee_tools(agent)
            register_expense_tools(agent, role)
            register_audit_tools(agent)
            register_receipt_tools(agent)
            logger.info("Registered all tools for admin user")
        else:
            # Employee gets limited tools
            register_expense_tools(agent, role)
            register_receipt_tools(agent)
            logger.info("Registered employee-level tools")
        
        # Handle file uploads if present
        uploaded_file_urls = []
        if files and len(files) > 0:
            logger.info(f"Processing {len(files)} uploaded file(s)")
            for file in files:
                if file.filename:
                    logger.info(f"Uploading file: {file.filename}")
                    file_url = await upload_file_to_storage(file, employee_id)
                    uploaded_file_urls.append(file_url)
                    logger.info(f"File uploaded: {file_url}")
            
            # Enhance the query with file information
            if uploaded_file_urls:
                file_info = "\n".join([f"- Receipt PDF uploaded: {url}" for url in uploaded_file_urls])
                enhanced_query = f"{query}\n\nAttached files:\n{file_info}"
                query = enhanced_query
                logger.info(f"Enhanced query with file info")
        
        # Convert message history to Pydantic AI's ModelMessage format
        pydantic_history: List[ModelMessage] = []
        if message_history:
            for msg in message_history:
                msg_role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if msg_role == "user":
                    pydantic_history.append(ModelRequest(parts=[UserPromptPart(content=content)]))
                elif msg_role == "assistant":
                    pydantic_history.append(ModelResponse(parts=[TextPart(content=content)]))
        
        # Run the agent with the user's query and conversation history
        if pydantic_history:
            result = await agent.run(query, message_history=pydantic_history, deps=user_context)
        else:
            result = await agent.run(query, deps=user_context)
        
        # Extract the response - access the output attribute which contains the actual output
        response_text = result.output
        
        # Get information about which tools were called and extract expense review results
        tools_used = []
        expense_review_result = None
        
        # Parse all messages to find tool calls and their results
        all_messages = result.all_messages()
        for message in all_messages:
            # Check for tool return messages (these contain the tool results)
            if hasattr(message, 'parts'):
                for part in message.parts:
                    # Check if this is a tool return with expense creation data
                    if hasattr(part, 'tool_name') and part.tool_name == 'create_new_expense':
                        tools_used.append('create_new_expense')
                    
                    # Check if this part contains the tool return content
                    if hasattr(part, 'content') and isinstance(part.content, dict):
                        tool_result = part.content
                        # Check if this is an expense with review information
                        if tool_result.get('review_completed') is not None:
                            expense_review_result = {
                                'expense_id': tool_result.get('expense_id') or tool_result.get('id'),
                                'status': tool_result.get('review_status') or tool_result.get('status'),
                                'reason': tool_result.get('review_reason') or tool_result.get('decision_reason', ''),
                                'amount': tool_result.get('amount'),
                                'category': tool_result.get('category'),
                                'completed': tool_result.get('review_completed'),
                                'decision_actor': tool_result.get('decision_actor')
                            }
        
        # Enhance the response with review outcome if an expense was created
        if expense_review_result:
            if expense_review_result['completed']:
                status = expense_review_result['status']
                amount = expense_review_result['amount']
                reason = expense_review_result['reason']
                
                if status == 'approved':
                    response_text += f"\n\n✅ **Expense Approved!**\nYour expense of ${amount} has been automatically approved by our AI system."
                elif status == 'rejected':
                    response_text += f"\n\n❌ **Expense Rejected**\nYour expense of ${amount} was rejected. Reason: {reason}"
                elif status == 'admin_review':
                    response_text += f"\n\n⏳ **Manual Review Required**\nYour expense of ${amount} has been flagged for manual review by an administrator. Reason: {reason}"
            else:
                response_text += f"\n\n⏳ **Review Pending**\nYour expense has been submitted and is being reviewed. Please check back shortly."
        
        logger.info(f"Query processed successfully. Response length: {len(response_text)}")
        
        return {
            "success": True,
            "response": response_text,
            "tools_used": tools_used,
            "query": query,
            "user_role": role,
            "expense_review": expense_review_result
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "response": None,
            "tools_used": [],
            "user_role": role
        }
