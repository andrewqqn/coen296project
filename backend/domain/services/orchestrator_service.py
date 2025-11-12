"""
Orchestrator service using Pydantic AI to route natural language queries to appropriate tools.
"""
from typing import Any, Dict, List, Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIResponsesModel
import os
from utils.logger import get_logger

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
def create_new_expense(ctx: RunContext[None], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new expense in the system.
    
    Args:
        data: Expense data including amount, category, description, etc.
    """
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


async def process_query(query: str) -> Dict[str, Any]:
    """
    Process a natural language query using Pydantic AI agent.
    
    Args:
        query: Natural language query from the user
        
    Returns:
        Dictionary containing the response and metadata
    """
    try:
        logger.info(f"Processing query: {query}")
        
        # Run the agent with the user's query
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
