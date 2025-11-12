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
        data: Expense data - MUST include amount, category, and description
    """
    # Add custom validation
    required_fields = ['amount', 'category', 'description']
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
    
    # Call the actual service
    from domain.services import expense_service
    return expense_service.create_expense(data)


# Example 4: Tool with context awareness
@custom_agent.tool
def get_user_expenses(ctx: RunContext[str], user_id: str = None) -> list[Dict[str, Any]]:
    """
    Get expenses filtered by user.
    
    Args:
        user_id: Optional user ID to filter by. If not provided, uses current user.
    """
    from domain.services import expense_service
    
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
        expense_data: Expense data to create
    """
    from domain.services import expense_service, audit_service
    from datetime import datetime
    
    # Create the expense
    result = expense_service.create_expense(expense_data)
    
    if result:
        # Create audit log
        audit_service.create_log({
            "action": "CREATE_EXPENSE",
            "resource_id": result.get('id'),
            "timestamp": datetime.utcnow().isoformat(),
            "details": f"Created expense: {expense_data.get('description', 'N/A')}"
        })
    
    return result


# Example 6: Tool with error handling and retry logic
@custom_agent.tool
def safe_get_expense(ctx: RunContext[None], expense_id: str) -> Dict[str, Any]:
    """
    Get expense with comprehensive error handling.
    
    Args:
        expense_id: The expense ID to retrieve
    """
    from domain.services import expense_service
    
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
    from domain.services import expense_service
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
