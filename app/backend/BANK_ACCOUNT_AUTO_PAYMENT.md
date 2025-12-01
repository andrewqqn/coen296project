# Automatic Bank Account Payment for Approved Expenses

## Overview

The orchestrator agent now automatically updates an employee's bank account balance when their expense is approved during the expense creation workflow.

## How It Works

### Automatic Payment Processing

When an expense is created with a receipt (from any source):

1. **Expense Creation**: User submits expense with receipt (via form or AI assistant)
2. **AI Review**: System automatically reviews the expense (`auto_review_on_create`)
3. **Approval Check**: If AI decision is "APPROVE"
4. **Balance Update**: Employee's bank account balance is automatically increased by the expense amount

This works for:
- ✓ Expenses created via Submit Expense form
- ✓ Expenses created via AI Assistant
- ✓ Any expense with a receipt that triggers AI review

### Implementation Details

The logic is implemented in the `evaluate_and_maybe_auto_approve` function in `expense_agent_service.py`:

```python
# In expense_agent_service.py, after AI makes decision
if status == "approved":
    try:
        from services import financial_service
        
        # Get employee to find their bank account
        emp_id = expense.get('employee_id')
        employee_data = get_employee(emp_id)
        
        if employee_data and employee_data.get('bank_account_id'):
            bank_account_id = employee_data['bank_account_id']
            expense_amount = float(expense.get('amount', 0))
            
            # Get current balance
            current_balance = financial_service.get_account_balance(bank_account_id)
            if current_balance is not None:
                # Add expense amount to balance
                new_balance = current_balance + expense_amount
                financial_service.update_account_balance(bank_account_id, new_balance)
                logger.info(f"Updated bank account {bank_account_id}: ${current_balance} -> ${new_balance}")
    except Exception as e:
        logger.error(f"Failed to update bank account: {str(e)}")
```

This happens automatically in the AI review process, so it works for expenses from:
- Submit Expense form (`POST /expenses`)
- AI Assistant (`POST /agents/query-with-files`)
- Any other source that triggers `auto_review_on_create()`

**Important**: This is the ONLY place where automatic payment happens. The orchestrator agent does NOT update bank accounts during expense creation - it relies on the expense agent service to handle payments.

### Manual Payment Processing

For cases where payment needs to be processed manually (e.g., admin-approved expenses), a new tool is available:

**Tool**: `process_approved_expense_payment`
- **Access**: Admin only
- **Purpose**: Manually trigger payment for an approved expense
- **Usage**: "Process payment for expense exp_123"

This tool:
- Verifies the expense is approved
- Finds the employee's bank account
- Updates the balance
- Returns detailed payment information

## User Experience

### Approved Expense
```
✅ Created expense exp_xyz for $12.45 at Starbucks. 
Status: APPROVED. 
Reason: Receipt valid, within policy limits. 
Your bank account has been credited with $12.45.
```

### Rejected Expense
```
❌ Created expense exp_xyz for $12.45 at Starbucks. 
Status: REJECTED. 
Reason: [decision_reason]
```

### Manual Review Required
```
⏳ Created expense exp_xyz for $12.45 at Starbucks. 
Status: MANUAL REVIEW REQUIRED. 
Reason: [decision_reason]. 
An administrator will review this expense.
```

## Requirements

For automatic payment to work:
1. Employee must have a `bank_account_id` field
2. Bank account must exist in the system
3. Expense must be approved (status = "approved")

## Error Handling

The system gracefully handles errors:
- Missing bank account: Logs warning, continues without payment
- Balance retrieval failure: Logs error, continues without payment
- Any exception: Logs full error, continues without payment

This ensures expense creation succeeds even if payment processing fails.

## Testing

Use `backend/test_bank_account_update.py` to test the functionality:

```python
# Test automatic payment during expense creation
asyncio.run(test_bank_account_update())

# Test manual payment processing
asyncio.run(test_manual_payment_processing())
```

## Future Enhancements

Potential improvements:
- Add transaction history to bank accounts
- Send notification when payment is processed
- Support different payment methods
- Add payment reversal for rejected expenses
- Implement payment batching for multiple expenses
