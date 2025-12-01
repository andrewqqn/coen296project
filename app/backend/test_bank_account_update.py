"""
Test script to verify bank account balance updates when expenses are approved
"""
import asyncio
import logging
from services.agents.orchestrator_agent import orchestrator_agent
from services import employee_service, financial_service, expense_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_bank_account_update():
    """Test that bank account balance is updated when expense is approved"""
    
    # Test employee ID (should exist in your system)
    test_employee_id = "emp_123"
    
    # Get employee and their bank account
    employee = employee_service.get_employee(test_employee_id)
    if not employee:
        logger.error(f"Employee {test_employee_id} not found")
        return
    
    bank_account_id = employee.get('bank_account_id')
    if not bank_account_id:
        logger.error(f"Employee {test_employee_id} has no bank account")
        return
    
    # Get initial balance
    initial_balance = financial_service.get_account_balance(bank_account_id)
    logger.info(f"Initial balance for {bank_account_id}: ${initial_balance}")
    
    # Create a test expense with a receipt
    # Note: This would normally be done through the orchestrator with a real receipt
    test_query = """
    Create an expense from this receipt
    
    Attached files:
    - Receipt PDF uploaded at: local://uploads/receipts/emp_123/test_receipt.pdf
    """
    
    logger.info("Processing test expense creation...")
    result = await orchestrator_agent.process_query(
        query=test_query,
        user_id=test_employee_id,
        role="employee"
    )
    
    logger.info(f"Result: {result}")
    
    # Check new balance
    new_balance = financial_service.get_account_balance(bank_account_id)
    logger.info(f"New balance for {bank_account_id}: ${new_balance}")
    
    if new_balance > initial_balance:
        logger.info(f"✅ SUCCESS: Balance increased by ${new_balance - initial_balance}")
    else:
        logger.warning(f"⚠️ Balance did not increase (may not have been approved)")


async def test_manual_payment_processing():
    """Test manual payment processing for an already-approved expense"""
    
    # Test with an existing approved expense
    test_expense_id = "exp_test_123"
    
    logger.info(f"Testing manual payment processing for expense {test_expense_id}")
    
    result = await orchestrator_agent.process_query(
        query=f"Process payment for expense {test_expense_id}",
        user_id="admin_user",
        role="admin"
    )
    
    logger.info(f"Result: {result}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Bank Account Balance Updates")
    print("=" * 60)
    
    # Run the test
    # asyncio.run(test_bank_account_update())
    
    # Or test manual payment processing
    # asyncio.run(test_manual_payment_processing())
    
    print("\nNote: Uncomment the test you want to run above")
    print("Make sure you have valid test data (employee, bank account, receipt)")
