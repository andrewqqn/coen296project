"""
Example: Customizing the Orchestrator

This file shows how to customize the orchestrator agent for different use cases.
"""

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
import os

# Example 1: Using a different model (cheaper option)
model_mini = OpenAIModel('gpt-4o-mini', api_key=os.getenv("OPENAI_API_KEY"))

# Example 2: Custom system prompt for specific behavior
custom_agent = Agent(
    model_mini,
    system_prompt="""You are a helpful assistant for an expense management system.
    Be concise and professional. When listing data, format it as numbered lists.
    If the user asks for data that doesn't exist, politely inform them.
    Always confirm successful create/update/delete operations."""
)

# Example 3: Adding custom validation to tools
from pydantic_ai import RunContext
from typing import Dict, Any

@custom_agent.tool
def validated_create_expense(ctx: RunContext[None], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new expense with validation.
    
    Args:
        data: Expense data - MUST include amount, category, and business_justification
    """
    from domain.schemas.expense_schema import ExpenseCreate
    from datetime import datetime
    
    # Add custom validation
    required_fields = ['amount', 'category', 'business_justification', 'employee_id']
    missing = [f for f in required_fields if f not in data]
    
    if missing:
        return {
            "error": f"Missing required fields: {', '.join(missing)}",
            "success": False
        }
    
    # Additional business logic
    if data['amount'] <= 0:
        return {
            "error": "Amount must be positive",
            "success": False
        }
    
    # Create ExpenseCreate object
    expense_create = ExpenseCreate(
        employee_id=data['employee_id'],
        amount=data['amount'],
        category=data['category'],
        business_justification=data['business_justification'],
        date_of_expense=data.get('date_of_expense', datetime.utcnow())
    )
    
    # Call the actual service
    from services import expense_service
    result = expense_service.create_expense(expense_create, receipt_path=data.get('receipt_path'))
    return result.dict() if hasattr(result, 'dict') else result


# Example 4: Tool with context awareness
@custom_agent.tool
def get_user_expenses(ctx: RunContext[str], user_id: str = None) -> list[Dict[str, Any]]:
    """
    Get expenses filtered by user.
    
    Args:
        user_id: Optional user ID to filter by. If not provided, uses current user.
    """
    from services import expense_service
    
    # Get all expenses
    all_expenses = expense_service.list_expenses()
    
    # Filter by user if specified
    if user_id:
        return [e for e in all_expenses if e.get('user_id') == user_id]
    
    # Use context user (from authentication)
    if hasattr(ctx, 'deps') and isinstance(ctx.deps, str):
        return [e for e in all_expenses if e.get('user_id') == ctx.deps]
    
    return all_expenses


# Example 5: Combining multiple operations in one tool
@custom_agent.tool
def create_expense_and_log(ctx: RunContext[None], expense_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an expense and automatically create an audit log entry.
    
    Args:
        expense_data: Expense data to create (must include employee_id, amount, category, business_justification)
    """
    from services import expense_service, audit_log_service
    from domain.schemas.expense_schema import ExpenseCreate
    from datetime import datetime
    
    # Create ExpenseCreate object
    expense_create = ExpenseCreate(
        employee_id=expense_data['employee_id'],
        amount=expense_data['amount'],
        category=expense_data['category'],
        business_justification=expense_data.get('business_justification', 'N/A'),
        date_of_expense=expense_data.get('date_of_expense', datetime.utcnow())
    )
    
    # Create the expense
    result = expense_service.create_expense(expense_create, receipt_path=expense_data.get('receipt_path'))
    
    if result:
        # Create audit log
        audit_log_service.create_log({
            "action": "CREATE_EXPENSE",
            "resource_id": result.expense_id if hasattr(result, 'expense_id') else result.get('expense_id'),
            "timestamp": datetime.utcnow().isoformat(),
            "details": f"Created expense: {expense_data.get('business_justification', 'N/A')}"
        })
    
    return result.dict() if hasattr(result, 'dict') else result


# Example 6: Tool with error handling and retry logic
@custom_agent.tool
def safe_get_expense(ctx: RunContext[None], expense_id: str) -> Dict[str, Any]:
    """
    Get expense with comprehensive error handling.
    
    Args:
        expense_id: The expense ID to retrieve
    """
    from services import expense_service
    
    try:
        result = expense_service.get_expense(expense_id)
        
        if result is None:
            return {
                "error": f"Expense with ID {expense_id} not found",
                "success": False
            }
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        return {
            "error": f"Failed to retrieve expense: {str(e)}",
            "success": False
        }


# Example 7: Tool that aggregates data
@custom_agent.tool
def get_expense_summary(ctx: RunContext[None]) -> Dict[str, Any]:
    """
    Get a summary of all expenses including totals and counts by category.
    """
    from services import expense_service
    from collections import defaultdict
    
    expenses = expense_service.list_expenses()
    
    total_amount = sum(e.get('amount', 0) for e in expenses)
    count = len(expenses)
    
    by_category = defaultdict(lambda: {"count": 0, "total": 0})
    for expense in expenses:
        cat = expense.get('category', 'unknown')
        by_category[cat]["count"] += 1
        by_category[cat]["total"] += expense.get('amount', 0)
    
    return {
        "total_expenses": count,
        "total_amount": total_amount,
        "average_amount": total_amount / count if count > 0 else 0,
        "by_category": dict(by_category)
    }


# Example 8: Using different models for different complexity
simple_agent = Agent(
    OpenAIModel('gpt-4o-mini', api_key=os.getenv("OPENAI_API_KEY")),
    system_prompt="You handle simple queries efficiently and concisely."
)

complex_agent = Agent(
    OpenAIModel('gpt-4o', api_key=os.getenv("OPENAI_API_KEY")),
    system_prompt="You handle complex multi-step queries with detailed analysis."
)


# Example 9: Router function to choose agent based on query complexity
def smart_route(query: str):
    """Route to appropriate agent based on query complexity"""
    complex_keywords = ['analyze', 'compare', 'calculate', 'summarize', 'report']
    
    query_lower = query.lower()
    is_complex = any(keyword in query_lower for keyword in complex_keywords)
    
    return complex_agent if is_complex else simple_agent


# Example 10: Async processing with streaming
async def process_with_streaming(query: str):
    """Process query with streaming response"""
    from pydantic_ai import Agent
    
    agent = Agent(
        OpenAIModel('gpt-4o', api_key=os.getenv("OPENAI_API_KEY")),
    )
    
    # Stream the response
    async with agent.run_stream(query) as response:
        async for text in response.stream():
            print(text, end='', flush=True)
        
        # Get final result
        final = await response.get_data()
        return final


"""
Usage Examples:

1. Replace the agent in orchestrator_service.py:
   from examples.orchestrator_examples import custom_agent as agent

2. Add specific tools to existing agent:
   from examples.orchestrator_examples import get_expense_summary
   agent.tool(get_expense_summary)

3. Create specialized endpoints:
   @router.post("/orchestrator/summary")
   async def get_summary(query: QueryRequest):
       # Use agent with summary tool
       pass

4. Implement smart routing:
   agent = smart_route(query)
   result = await agent.run(query)
"""
