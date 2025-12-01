"""
Test to verify expenses created through orchestrator show up in expense list
"""
import asyncio
from services import employee_service, expense_service
from services.multi_agent_orchestrator import process_query_with_agents


async def test_expense_listing():
    """
    Test that expenses created through orchestrator use correct employee_id
    """
    print("=" * 60)
    print("Testing Expense Listing Fix")
    print("=" * 60)
    
    # Get a test employee
    employees = employee_service.list_employees()
    if not employees:
        print("❌ No employees found. Create an employee first.")
        return
    
    test_employee = employees[0]
    employee_id = test_employee.get("employee_id")
    auth_id = test_employee.get("authentication_id")
    
    print(f"\n✓ Test Employee:")
    print(f"  - Employee ID: {employee_id}")
    print(f"  - Auth ID: {auth_id}")
    print(f"  - Name: {test_employee.get('name')}")
    
    # Get expenses before
    expenses_before = expense_service.list_expenses()
    employee_expenses_before = [e for e in expenses_before if e.get('employee_id') == employee_id]
    
    print(f"\n✓ Expenses before: {len(employee_expenses_before)} for this employee")
    
    # Create a test expense through orchestrator
    print(f"\n✓ Creating test expense through orchestrator...")
    
    result = await process_query_with_agents(
        query="Create an expense for $25.50 for office supplies on 2025-01-15",
        employee_id=employee_id,  # Using internal employee_id
        role=test_employee.get("role", "employee")
    )
    
    print(f"\n✓ Orchestrator result:")
    print(f"  - Success: {result.get('success')}")
    print(f"  - Response: {result.get('response')}")
    
    # Get expenses after
    expenses_after = expense_service.list_expenses()
    employee_expenses_after = [e for e in expenses_after if e.get('employee_id') == employee_id]
    
    print(f"\n✓ Expenses after: {len(employee_expenses_after)} for this employee")
    
    # Check if new expense was created
    if len(employee_expenses_after) > len(employee_expenses_before):
        new_expense = employee_expenses_after[0]
        print(f"\n✅ SUCCESS! New expense created:")
        print(f"  - Expense ID: {new_expense.get('expense_id')}")
        print(f"  - Employee ID: {new_expense.get('employee_id')}")
        print(f"  - Amount: ${new_expense.get('amount')}")
        print(f"  - Category: {new_expense.get('category')}")
        
        # Verify employee_id matches
        if new_expense.get('employee_id') == employee_id:
            print(f"\n✅ VERIFIED: Expense has correct employee_id!")
        else:
            print(f"\n❌ ERROR: Expense has wrong employee_id!")
            print(f"  Expected: {employee_id}")
            print(f"  Got: {new_expense.get('employee_id')}")
    else:
        print(f"\n❌ ERROR: No new expense was created")
        print(f"  This might be because the orchestrator couldn't parse the request")
        print(f"  Check the orchestrator response above")


if __name__ == "__main__":
    asyncio.run(test_expense_listing())
