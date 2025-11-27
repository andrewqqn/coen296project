"""
Orchestrator Agent - Coordinates between multiple specialized agents using A2A protocol
"""
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIResponsesModel

from services.agents.base_agent import BaseAgent
from services.agents.a2a_protocol import (
    AgentCard,
    AgentCapability,
    A2ARequest,
    A2AResponse,
    A2AMessage,
    agent_registry,
    create_a2a_message
)
from utils.rbac import require_role, filter_by_ownership, check_ownership

logger = logging.getLogger("orchestrator_agent")
logger.setLevel(logging.INFO)


class OrchestratorContext(BaseModel):
    """Context for orchestrator operations"""
    user_id: str
    role: str
    session_id: Optional[str] = None


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - High-level coordinator that delegates to specialized agents
    """
    
    def __init__(self):
        super().__init__(
            agent_id="orchestrator",
            name="Orchestrator Agent",
            description="Coordinates between specialized agents to fulfill complex user requests"
        )
        self._setup_pydantic_agent()
    
    def _setup_pydantic_agent(self):
        """Setup the Pydantic AI agent with tools for agent communication"""
        system_prompt = """You are an intelligent orchestrator for an Expense Reimbursement System.

Your role is to understand user requests and coordinate with specialized agents to fulfill them.

Available specialized agents:
1. Expense Agent - Reviews expenses, applies policy rules, validates receipts
2. Document Agent - Processes PDF receipts, extracts structured information

Available direct tools:
1. create_expense - Create a new expense record
2. list_expenses - List all expenses (filtered by role)
3. get_expense - Get details of a specific expense
4. query_policies - Search the reimbursement policy database
5. list_employees - List all employees (admin only)
6. get_employee - Get employee details (admin only)
7. create_employee - Create a new employee (admin only)
8. update_employee - Update employee information (admin only)
9. delete_employee - Delete an employee (admin only)

Common workflows:
- Review an expense → Use expense_agent's review_expense capability
- Process a receipt → Use call_document_agent to extract info
- Create expense from receipt → 
  1. Use call_document_agent to extract info from receipt
  2. Use create_expense with the extracted data (including receipt_path)
  3. The system will automatically trigger AI review after creation
  4. Use get_expense to check the review result
- List expenses → Use list_expenses tool
- Query policies → Use query_policies tool (e.g., "meal limits", "travel policy", "receipt requirements")
- Manage employees (admin only) → Use list_employees, get_employee, create_employee, update_employee, delete_employee

CRITICAL: File Upload and Expense Creation Workflow

When the user uploads a receipt and asks to create an expense, follow this EXACT workflow:

Step 1: Extract file path from query
- Look for "Attached files:" in the query
- Extract the file path (everything after "uploaded at: ")
- File paths look like: "local://uploads/receipts/user123/filename.pdf"

Step 2: Process the receipt
- Call: call_document_agent(file_path="local://uploads/receipts/...")
- This returns: vendor, amount, date, category, description

Step 3: Create the expense with receipt
- Call: create_expense(
    employee_id=ctx.deps.user_id,  # IMPORTANT: Always use ctx.deps.user_id for current user
    amount=extracted_amount,
    category=extracted_category,
    business_justification=extracted_description,
    date_of_expense=extracted_date,
    receipt_path="local://uploads/receipts/..."  # IMPORTANT: Include the receipt path!
  )
- Note: For employees, the tool automatically uses ctx.deps.user_id regardless of employee_id parameter
- This creates the expense AND automatically triggers AI review
- The tool waits for review to complete and returns the result
- Response includes: expense_id, status, decision_reason, review_completed

Step 4: Present the complete result
- Tell the user:
  * Expense ID
  * Amount and category
  * Status (approved/rejected/admin-review/pending)
  * Decision reason (why it was approved/rejected)
  * What happens next (if manual review needed)

Example Complete Workflow:
User: "Create an expense from this receipt

Attached files:
- Receipt PDF uploaded at: local://uploads/receipts/emp_123/receipt.pdf"

Your Actions:
1. Extract file path: "local://uploads/receipts/emp_123/receipt.pdf"
2. Call: call_document_agent(file_path="local://uploads/receipts/emp_123/receipt.pdf")
   Returns: {vendor: "Starbucks", amount: 12.45, date: "2025-01-15", category: "meals", description: "Coffee"}
3. Call: create_expense(employee_id=ctx.deps.user_id, amount=12.45, category="Meals", business_justification="Coffee", date_of_expense="2025-01-15", receipt_path="local://uploads/receipts/emp_123/receipt.pdf")
4. Tool returns: {success: True, expense_id: "exp_xyz", status: "approved", decision_reason: "Receipt valid, within policy", review_completed: True}
5. Tell user: "✅ Created expense exp_xyz for $12.45 at Starbucks. Status: APPROVED. Reason: Receipt valid, within policy limits."

If status is "rejected":
"❌ Created expense exp_xyz for $12.45 at Starbucks. Status: REJECTED. Reason: [decision_reason]"

If status is "admin-review":
"⏳ Created expense exp_xyz for $12.45 at Starbucks. Status: MANUAL REVIEW REQUIRED. Reason: [decision_reason]. An administrator will review this expense."

DO NOT:
- Say you can't access files (the paths are in the query!)
- Skip the receipt_path parameter when creating expense
- Forget to check the review result
- Create expense without extracting receipt info first
- Retry failed operations automatically (tools have retries disabled)

ERROR HANDLING:
If a tool returns {"success": False, "error": "..."}, explain the error to the user clearly.
Common errors:
- File not found: Ask user to verify the file was uploaded correctly
- PDF processing error: The file may be corrupted or not a valid PDF
- Permission denied: User may not have access to this resource

Always explain what you're doing and provide complete results."""
        
        self.pydantic_agent = self.create_pydantic_agent(system_prompt, "gpt-4o")
        
        # Register tools for communicating with other agents
        self._register_agent_tools()
    
    def _register_agent_tools(self):
        """Register tools for communicating with specialized agents"""
        
        @self.pydantic_agent.tool
        async def call_expense_agent(
            ctx: RunContext[OrchestratorContext],
            capability: str,
            parameters: Dict[str, Any]
        ) -> Dict[str, Any]:
            """
            Call the Expense Agent to review expenses or apply policy rules.
            
            Args:
                capability: The capability to invoke (review_expense, apply_static_rules)
                parameters: Parameters for the capability
            
            Returns:
                Dictionary with review results. Always returns a dict, never raises exceptions.
                Format: {"success": True/False, "error": "...", ...other fields}
            """
            try:
                logger.info(f"Orchestrator calling expense_agent.{capability} with params: {parameters}")
                
                # Import here to avoid circular dependency
                from services.agents.expense_agent_service import expense_agent
                
                request = A2ARequest(
                    capability_name=capability,
                    parameters=parameters,
                    context={"user_id": ctx.deps.user_id, "role": ctx.deps.role}
                )
                
                message = create_a2a_message(
                    sender_id=self.agent_id,
                    recipient_id="expense_agent",
                    message_type="request",
                    payload=request.dict(),
                    capability_name=capability
                )
                
                response_message = await expense_agent.process_message(
                    message,
                    context={"user_id": ctx.deps.user_id, "role": ctx.deps.role}
                )
                
                if response_message.message_type == "error":
                    error = response_message.payload.get("error", "Unknown error")
                    logger.error(f"Error from expense_agent: {error}")
                    return {"success": False, "error": error}
                
                result = response_message.payload.get("result", {})
                logger.info(f"Expense agent returned: {result}")
                return {"success": True, **result}
                
            except Exception as e:
                error_msg = f"Exception calling expense_agent: {str(e)}"
                logger.error(error_msg, exc_info=True)
                # Return error dict instead of raising
                return {"success": False, "error": error_msg}
        
        @self.pydantic_agent.tool
        async def call_document_agent(
            ctx: RunContext[OrchestratorContext],
            file_path: str,
            capability: str = "extract_receipt_info"
        ) -> Dict[str, Any]:
            """
            Call the Document Agent to process receipts and extract information from a PDF file.
            
            Args:
                file_path: Path to the PDF file (e.g., "local://uploads/receipts/user123/file.pdf")
                capability: The capability to invoke (default: "extract_receipt_info")
            
            Returns:
                Dictionary with extracted information. Always returns a dict, never raises exceptions.
                Format: {"success": True/False, "error": "...", "vendor": "...", "amount": ..., etc}
            """
            # Wrap EVERYTHING in try-except to ensure no exceptions escape
            try:
                logger.info(f"[TOOL START] call_document_agent: file_path={file_path}, capability={capability}")
                
                # Validate file_path
                if not file_path or not isinstance(file_path, str):
                    error_msg = "Invalid file_path: must be a non-empty string"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
                
                # Import here to avoid circular dependency
                try:
                    from services.agents.document_agent_service import document_agent
                    logger.info("[TOOL] Document agent imported successfully")
                except Exception as import_error:
                    error_msg = f"Failed to import document_agent: {str(import_error)}"
                    logger.error(error_msg, exc_info=True)
                    return {"success": False, "error": error_msg}
                
                # Create request with file_path in parameters
                try:
                    request = A2ARequest(
                        capability_name=capability,
                        parameters={"file_path": file_path},
                        context={"user_id": ctx.deps.user_id, "role": ctx.deps.role}
                    )
                    logger.info("[TOOL] A2ARequest created successfully")
                except Exception as req_error:
                    error_msg = f"Failed to create A2ARequest: {str(req_error)}"
                    logger.error(error_msg, exc_info=True)
                    return {"success": False, "error": error_msg}
                
                # Create message
                try:
                    message = create_a2a_message(
                        sender_id=self.agent_id,
                        recipient_id="document_agent",
                        message_type="request",
                        payload=request.dict(),
                        capability_name=capability
                    )
                    logger.info("[TOOL] A2A message created successfully")
                except Exception as msg_error:
                    error_msg = f"Failed to create A2A message: {str(msg_error)}"
                    logger.error(error_msg, exc_info=True)
                    return {"success": False, "error": error_msg}
                
                # Process message
                try:
                    response_message = await document_agent.process_message(
                        message,
                        context={"user_id": ctx.deps.user_id, "role": ctx.deps.role}
                    )
                    logger.info(f"[TOOL] Document agent processed message, type={response_message.message_type}")
                except Exception as process_error:
                    error_msg = f"Failed to process message: {str(process_error)}"
                    logger.error(error_msg, exc_info=True)
                    return {"success": False, "error": error_msg}
                
                # Check response
                if response_message.message_type == "error":
                    error = response_message.payload.get("error", "Unknown error")
                    logger.error(f"[TOOL] Error from document_agent: {error}")
                    return {"success": False, "error": error}
                
                result = response_message.payload.get("result", {})
                logger.info(f"[TOOL SUCCESS] Document agent returned: {result}")
                return {"success": True, **result}
                
            except Exception as e:
                error_msg = f"[TOOL EXCEPTION] Unexpected exception in call_document_agent: {str(e)}"
                logger.error(error_msg, exc_info=True)
                # Return error dict instead of raising - THIS MUST NOT RAISE!
                return {"success": False, "error": error_msg}
        
        @self.pydantic_agent.tool
        @require_role("admin")
        def list_employees(ctx: RunContext[OrchestratorContext]) -> List[Dict[str, Any]]:
            """
            List all employees in the system. Admin only.
            
            Returns:
                List of all employees with their details
            """
            from services import employee_service
            
            logger.info(f"Admin {ctx.deps.user_id} listing all employees")
            
            try:
                employees = employee_service.list_employees()
                logger.info(f"Found {len(employees)} employees")
                return employees
            except Exception as e:
                logger.error(f"Error listing employees: {str(e)}", exc_info=True)
                return [{"error": str(e)}]
        
        @self.pydantic_agent.tool
        @require_role("admin")
        def get_employee(
            ctx: RunContext[OrchestratorContext],
            employee_id: str
        ) -> Optional[Dict[str, Any]]:
            """
            Get details of a specific employee by ID. Admin only.
            
            Args:
                employee_id: The employee ID to retrieve
            
            Returns:
                Employee details or None if not found
            """
            from services import employee_service
            
            logger.info(f"Admin {ctx.deps.user_id} getting employee {employee_id}")
            
            try:
                employee = employee_service.get_employee(employee_id)
                return employee
            except Exception as e:
                logger.error(f"Error getting employee: {str(e)}", exc_info=True)
                return {"error": str(e)}
        
        @self.pydantic_agent.tool
        @require_role("admin")
        def create_employee(
            ctx: RunContext[OrchestratorContext],
            name: str,
            email: str,
            department: str,
            role: str = "employee"
        ) -> Dict[str, Any]:
            """
            Create a new employee. Admin only.
            
            Args:
                name: Employee's full name
                email: Employee's email address
                department: Department name
                role: Role (employee or admin), defaults to employee
            
            Returns:
                Created employee details
            """
            from services import employee_service, financial_service
            import uuid
            
            logger.info(f"Admin {ctx.deps.user_id} creating employee: {name}")
            
            try:
                data = {
                    "name": name,
                    "email": email,
                    "department": department,
                    "role": role
                }
                result = employee_service.create_employee(data)
                logger.info(f"Created employee: {result}")
                
                # Create associated bank account
                employee_id = result.get("employee_id")
                if employee_id:
                    bank_account_id = str(uuid.uuid4())
                    bank_account_data = {
                        "holder_name": name,
                        "email": email,
                        "employee_id": employee_id,
                        "balance": 0.0
                    }
                    financial_service.create_bank_account(bank_account_id, bank_account_data)
                    logger.info(f"Created bank account {bank_account_id} for employee {employee_id}")
                    
                    # Update employee with bank_account_id
                    employee_service.update_employee(employee_id, {"bank_account_id": bank_account_id})
                    result["bank_account_id"] = bank_account_id
                    logger.info(f"Linked bank account {bank_account_id} to employee {employee_id}")

                return result
            except Exception as e:
                logger.error(f"Error creating employee: {str(e)}", exc_info=True)
                return {"error": str(e)}
        
        @self.pydantic_agent.tool
        @require_role("admin")
        def update_employee(
            ctx: RunContext[OrchestratorContext],
            employee_id: str,
            name: Optional[str] = None,
            email: Optional[str] = None,
            department: Optional[str] = None,
            role: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Update an existing employee. Admin only.
            
            Args:
                employee_id: The employee ID to update
                name: New name (optional)
                email: New email (optional)
                department: New department (optional)
                role: New role (optional)
            
            Returns:
                Updated employee details
            """
            from services import employee_service
            
            logger.info(f"Admin {ctx.deps.user_id} updating employee {employee_id}")
            
            try:
                # Build update data with only provided fields
                data = {}
                if name is not None:
                    data["name"] = name
                if email is not None:
                    data["email"] = email
                if department is not None:
                    data["department"] = department
                if role is not None:
                    data["role"] = role
                
                if not data:
                    return {"error": "No fields to update"}
                
                result = employee_service.update_employee(employee_id, data)
                logger.info(f"Updated employee: {result}")
                return result
            except Exception as e:
                logger.error(f"Error updating employee: {str(e)}", exc_info=True)
                return {"error": str(e)}
        
        @self.pydantic_agent.tool
        @require_role("admin")
        def delete_employee(
            ctx: RunContext[OrchestratorContext],
            employee_id: str
        ) -> Dict[str, Any]:
            """
            Delete an employee from the system. Admin only.
            
            Args:
                employee_id: The employee ID to delete
            
            Returns:
                Confirmation of deletion
            """
            from services import employee_service
            
            logger.info(f"Admin {ctx.deps.user_id} deleting employee {employee_id}")
            
            try:
                result = employee_service.delete_employee(employee_id)
                logger.info(f"Deleted employee {employee_id}")
                return result
            except Exception as e:
                logger.error(f"Error deleting employee: {str(e)}", exc_info=True)
                return {"error": str(e)}
        
        @self.pydantic_agent.tool
        def query_policies(
            ctx: RunContext[OrchestratorContext],
            query: str = "reimbursement policies"
        ) -> List[Dict[str, Any]]:
            """
            Query the reimbursement policy database to find relevant policy information.
            
            Args:
                query: Search query for policies (e.g., "meal limits", "travel policy", "receipt requirements")
            
            Returns:
                List of relevant policy snippets with their content
            """
            from services.vector_db_service import query_vector_db
            
            logger.info(f"Querying policies with: {query}")
            
            try:
                results = query_vector_db(query, top_k=5)
                logger.info(f"Found {len(results)} policy snippets")
                return results
            except Exception as e:
                logger.error(f"Error querying policies: {str(e)}", exc_info=True)
                return [{"error": str(e)}]
        
        @self.pydantic_agent.tool
        def list_available_agents(ctx: RunContext[OrchestratorContext]) -> List[Dict[str, Any]]:
            """
            List all available agents and their capabilities.
            Use this to discover what agents can do.
            """
            logger.info("Listing available agents")
            agents = agent_registry.list_agents()
            
            result = []
            for card in agents:
                if card.agent_id == self.agent_id:
                    continue  # Don't include self
                
                result.append({
                    "agent_id": card.agent_id,
                    "name": card.name,
                    "description": card.description,
                    "capabilities": [
                        {
                            "name": cap.name,
                            "description": cap.description
                        }
                        for cap in card.capabilities
                    ]
                })
            
            return result
        
        @self.pydantic_agent.tool
        @require_role("employee", "admin")
        async def create_expense(
            ctx: RunContext[OrchestratorContext],
            employee_id: str,
            amount: float,
            category: str,
            business_justification: str,
            date_of_expense: str,
            receipt_path: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Create a new expense in the system.
            
            Args:
                employee_id: The employee ID (use ctx.deps.user_id for current user)
                amount: The expense amount (numeric value, no currency symbols)
                category: Category (Meals, Travel, Conference, Other)
                business_justification: Description/justification
                date_of_expense: Date in YYYY-MM-DD format
                receipt_path: Optional path to receipt file (e.g., "local://uploads/receipts/...")
            
            Returns:
                Dictionary with expense details including expense_id and review status
            """
            import asyncio
            from services import expense_service
            from domain.schemas.expense_schema import ExpenseCreate
            from datetime import datetime
            
            # Employees can only create for themselves
            if ctx.deps.role == "employee":
                employee_id = ctx.deps.user_id
            
            logger.info(f"Creating expense for {employee_id}: ${amount} - {category}")
            
            try:
                # Parse date
                try:
                    expense_date = datetime.fromisoformat(date_of_expense)
                except ValueError:
                    expense_date = datetime.utcnow()
                
                # Create expense
                expense_create = ExpenseCreate(
                    employee_id=employee_id,
                    amount=amount,
                    category=category,
                    business_justification=business_justification,
                    date_of_expense=expense_date
                )
                
                result = expense_service.create_expense(expense_create, receipt_path=receipt_path)
                
                # Convert to dict
                expense_dict = result.dict() if hasattr(result, 'dict') else result
                expense_id = expense_dict.get('expense_id') or expense_dict.get('id')
                
                # If there's a receipt, wait for AI review to complete
                if receipt_path:
                    logger.info(f"Waiting for AI review to complete for expense {expense_id}")
                    max_wait = 30  # seconds
                    poll_interval = 1  # second
                    elapsed = 0
                    
                    while elapsed < max_wait:
                        await asyncio.sleep(poll_interval)
                        elapsed += poll_interval
                        
                        # Check if review is complete
                        updated_expense = expense_service.get_expense(expense_id)
                        if updated_expense:
                            decision_actor = updated_expense.get('decision_actor')
                            status = updated_expense.get('status')
                            
                            if decision_actor == 'AI' and status in ['approved', 'rejected', 'admin-review']:
                                logger.info(f"AI review completed with status: {status}")
                                return {
                                    "success": True,
                                    "expense": updated_expense,
                                    "expense_id": expense_id,
                                    "review_completed": True,
                                    "status": status,
                                    "decision_reason": updated_expense.get('decision_reason', '')
                                }
                    
                    # Timeout - return with pending status
                    logger.warning(f"AI review timeout for expense {expense_id}")
                    return {
                        "success": True,
                        "expense": expense_dict,
                        "expense_id": expense_id,
                        "review_completed": False,
                        "status": "pending",
                        "decision_reason": "AI review is taking longer than expected"
                    }
                
                # No receipt - return immediately
                return {
                    "success": True,
                    "expense": expense_dict,
                    "expense_id": expense_id,
                    "review_completed": False,
                    "status": "pending"
                }
                
            except Exception as e:
                logger.error(f"Error creating expense: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.pydantic_agent.tool
        @require_role("employee", "admin")
        def list_expenses(ctx: RunContext[OrchestratorContext]) -> List[Dict[str, Any]]:
            """
            List all expenses. For employees, only returns their own expenses.
            For admins, returns all expenses.
            """
            from services import expense_service
            
            logger.info(f"Listing expenses for {ctx.deps.role} user {ctx.deps.user_id}")
            
            try:
                all_expenses = expense_service.list_expenses()
                # Automatic filtering based on role
                return filter_by_ownership(ctx, all_expenses, owner_field="employee_id")
                
            except Exception as e:
                logger.error(f"Error listing expenses: {str(e)}", exc_info=True)
                return []
        
        @self.pydantic_agent.tool
        @require_role("employee", "admin")
        def get_expense(ctx: RunContext[OrchestratorContext], expense_id: str) -> Optional[Dict[str, Any]]:
            """
            Get details of a specific expense by ID.
            
            Args:
                expense_id: The expense ID to retrieve
            """
            from services import expense_service
            
            logger.info(f"Getting expense {expense_id} for {ctx.deps.role} user {ctx.deps.user_id}")
            
            try:
                expense = expense_service.get_expense(expense_id)
                
                if not expense:
                    return None
                
                # Check ownership for employees
                if not check_ownership(ctx, expense, owner_field="employee_id"):
                    logger.warning(f"User {ctx.deps.user_id} attempted to access expense {expense_id}")
                    return None
                
                return expense
                
            except Exception as e:
                logger.error(f"Error getting expense: {str(e)}", exc_info=True)
                return None
    
    def get_agent_card(self) -> AgentCard:
        """Return the agent's capability card"""
        return AgentCard(
            agent_id=self.agent_id,
            name=self.name,
            description=self.description,
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="process_user_query",
                    description="Process a natural language query and coordinate with specialized agents",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The user's natural language query"
                            },
                            "context": {
                                "type": "object",
                                "description": "Additional context (user_id, role, etc.)"
                            }
                        },
                        "required": ["query"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "response": {"type": "string"},
                            "agents_used": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                )
            ],
            metadata={
                "model": "gpt-4o",
                "coordinates_agents": ["expense_agent", "document_agent"]
            }
        )
    
    async def handle_request(self, request: A2ARequest, context: Dict[str, Any]) -> A2AResponse:
        """Handle incoming A2A requests"""
        try:
            if request.capability_name != "process_user_query":
                return A2AResponse(
                    success=False,
                    error=f"Unknown capability: {request.capability_name}"
                )
            
            query = request.parameters.get("query")
            if not query:
                return A2AResponse(
                    success=False,
                    error="Missing required parameter: query"
                )
            
            # Create orchestrator context
            orch_context = OrchestratorContext(
                user_id=context.get("user_id", "unknown"),
                role=context.get("role", "employee"),
                session_id=context.get("session_id")
            )
            
            # Run the Pydantic AI agent
            result = await self.pydantic_agent.run(query, deps=orch_context)
            
            # Extract agents used from message history
            agents_used = set()
            for message in result.all_messages():
                if hasattr(message, 'parts'):
                    for part in message.parts:
                        if hasattr(part, 'tool_name'):
                            if 'expense_agent' in part.tool_name:
                                agents_used.add('expense_agent')
                            elif 'document_agent' in part.tool_name:
                                agents_used.add('document_agent')
            
            return A2AResponse(
                success=True,
                result={
                    "response": result.output,
                    "agents_used": list(agents_used)
                },
                metadata={
                    "query": query,
                    "user_id": orch_context.user_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error in orchestrator: {str(e)}", exc_info=True)
            return A2AResponse(
                success=False,
                error=str(e)
            )
    
    async def process_query(
        self,
        query: str,
        user_id: str,
        role: str = "employee",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to process a user query
        """
        context = OrchestratorContext(
            user_id=user_id,
            role=role,
            session_id=session_id
        )
        
        try:
            result = await self.pydantic_agent.run(query, deps=context)
            
            # Extract agents used
            agents_used = set()
            for message in result.all_messages():
                if hasattr(message, 'parts'):
                    for part in message.parts:
                        if hasattr(part, 'tool_name'):
                            if 'expense_agent' in part.tool_name:
                                agents_used.add('expense_agent')
                            elif 'document_agent' in part.tool_name:
                                agents_used.add('document_agent')
            
            return {
                "success": True,
                "response": result.output,
                "agents_used": list(agents_used),
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "response": None,
                "agents_used": []
            }


# Create and register the orchestrator agent
orchestrator_agent = OrchestratorAgent()
orchestrator_agent.register()
