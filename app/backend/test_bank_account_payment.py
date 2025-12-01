"""
Test to verify bank account is updated when expenses are approved
"""
import asyncio
from services import employee_service, financial_service, expense_service
from services.agents.expense_agent_service import evaluate_and_maybe_auto_approve


async def test_bank_account_payment():
    """
    Test that bank account balance is updated when AI approves an expense
    """
    print("=" * 60)
    print("Testing Bank Account Payment on Approval")
    print("=" * 60)
    
    # Get a test employee
    employees = employee_service.list_employees()
    if not employees:
        print("❌ No employees found. Create an employee first.")
        return
    
    test_employee = employees[0]
    employee_id = test_employee.get("employee_id")
    bank_account_id = test_employee.get("bank_account_id")
    
    if not bank_account_id:
        print(f"❌ Employee {employee_id} has no bank account")
        return
    
    print(f"\n✓ Test Employee:")
    print(f"  - Employee ID: {employee_id}")
    print(f"  - Name: {test_employee.get('name')}")
    print(f"  - Bank Account: {bank_account_id}")
    
    # Get initial balance
    initial_balance = financial_service.get_account_balance(bank_account_id)
    print(f"\n✓ Initial Balance: ${initial_balance}")
    
    # Get expenses for this employee
    expenses = expense_service.list_expenses()
    employee_expenses = [e for e in expenses if e.get('employee_id') == employee_id]
    
    # Find a pending expense with a receipt
    pending_expense = None
    for exp in employee_expenses:
        if exp.get('status') == 'pending' and exp.get('receipt_path'):
            pending_expense = exp
            break
    
    if not pending_expense:
        print(f"\n⚠ No pending expenses with receipts found for this employee")
        print(f"  Create an expense with a receipt first, then run this test")
        return
    
    expense_id = pending_expense.get('expense_id')
    expense_amount = float(pending_expense.get('amount', 0))
    
    print(f"\n✓ Found Pending Expense:")
    print(f"  - Expense ID: {expense_id}")
    print(f"  - Amount: ${expense_amount}")
    print(f"  - Category: {pending_expense.get('category')}")
    print(f"  - Receipt: {pending_expense.get('receipt_path')}")
    
    # Trigger AI review
    print(f"\n✓ Triggering AI review...")
    try:
        result = await evaluate_and_maybe_auto_approve(expense_id)
        
        print(f"\n✓ AI Review Result:")
        print(f"  - Decision: {result.decision}")
        print(f"  - Rule: {result.rule}")
        print(f"  - Reason: {result.reason}")
        print(f"  - Confidence: {result.confidence}")
        
        # Check new balance
        new_balance = financial_service.get_account_balance(bank_account_id)
        print(f"\n✓ Balance After Review:")
        print(f"  - Previous: ${initial_balance}")
        print(f"  - Current: ${new_balance}")
        print(f"  - Change: ${new_balance - initial_balance}")
        
        # Verify
        if result.decision == "APPROVE":
            expected_balance = initial_balance + expense_amount
            if abs(new_balance - expected_balance) < 0.01:  # Float comparison
                print(f"\n✅ SUCCESS! Bank account updated correctly")
                print(f"  Expected: ${expected_balance}")
                print(f"  Actual: ${new_balance}")
            else:
                print(f"\n❌ ERROR! Bank account not updated correctly")
                print(f"  Expected: ${expected_balance}")
                print(f"  Actual: ${new_balance}")
        elif result.decision == "REJECT":
            if new_balance == initial_balance:
                print(f"\n✅ CORRECT! Bank account not updated (expense rejected)")
            else:
                print(f"\n❌ ERROR! Bank account changed despite rejection")
        else:  # MANUAL
            if new_balance == initial_balance:
                print(f"\n✅ CORRECT! Bank account not updated (manual review required)")
            else:
                print(f"\n❌ ERROR! Bank account changed despite manual review")
                
    except Exception as e:
        print(f"\n❌ ERROR during AI review: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_bank_account_payment())
