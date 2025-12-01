# Bank Account Payment Fix

## Issue

After standardizing the expense creation workflow, bank accounts were no longer being updated when expenses were approved via the Submit Expense form. They only worked for AI Assistant expenses.

## Root Cause

The bank account update logic was only in the orchestrator agent's `create_expense` tool, which is only called when creating expenses through the AI Assistant. When expenses were created through the form endpoint (`POST /expenses`), they went through a different code path:

```
Submit Form → POST /expenses → expense_service.create_expense_with_file() 
           → auto_review_on_create() → expense_agent_service.evaluate_and_maybe_auto_approve()
           → [NO BANK ACCOUNT UPDATE] ✗
```

The AI review happened, but the bank account update didn't.

## Solution

Moved the bank account update logic to the expense agent service, where the AI approval decision is made. Now it happens automatically for ALL approved expenses, regardless of source.

### Code Change

**File**: `backend/services/agents/expense_agent_service.py`

**Location**: In `evaluate_and_maybe_auto_approve()` function, after updating expense status

```python
# After setting status to "approved"
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
                logger.info(f"[PAYMENT] Updated bank account {bank_account_id} balance: ${current_balance} -> ${new_balance}")
    except Exception as e:
        logger.error(f"[PAYMENT] Failed to update bank account balance: {str(e)}")
```

## Flow After Fix

### Submit Expense Form
```
1. User submits form → POST /expenses
2. Backend creates expense → expense_service.create_expense_with_file()
3. AI review triggered → auto_review_on_create()
4. AI approves → expense_agent_service.evaluate_and_maybe_auto_approve()
5. Status set to "approved"
6. Bank account updated ✓
```

### AI Assistant
```
1. User uploads receipt → POST /agents/query-with-files
2. Orchestrator creates expense → orchestrator_agent.create_expense()
3. AI review triggered → auto_review_on_create()
4. AI approves → expense_agent_service.evaluate_and_maybe_auto_approve()
5. Status set to "approved"
6. Bank account updated ✓
```

Both paths now converge at the same point where the bank account is updated.

## Benefits

1. **Consistency**: Bank account updates work the same way for all expense sources
2. **Maintainability**: Single location for payment logic
3. **Reliability**: Can't forget to update bank account when adding new expense creation paths
4. **Simplicity**: No duplicate code

## Testing

### Test Case 1: Submit Expense Form
```bash
# Create expense via form
curl -X POST http://localhost:8000/expenses \
  -H "Authorization: Bearer $TOKEN" \
  -F "expense_data={...}" \
  -F "receipt=@receipt.pdf"

# Wait for AI review (a few seconds)

# Check bank account balance increased
curl http://localhost:8000/employees/me \
  -H "Authorization: Bearer $TOKEN"
# Verify: bank_account.balance increased by expense amount
```

### Test Case 2: AI Assistant
```bash
# Create expense via AI assistant
curl -X POST http://localhost:8000/agents/query-with-files \
  -H "Authorization: Bearer $TOKEN" \
  -F "query=Create an expense from this receipt" \
  -F "files=@receipt.pdf"

# Check bank account balance increased
curl http://localhost:8000/employees/me \
  -H "Authorization: Bearer $TOKEN"
# Verify: bank_account.balance increased by expense amount
```

### Test Case 3: Rejected Expense
```bash
# Create expense that will be rejected (e.g., no receipt)
curl -X POST http://localhost:8000/expenses \
  -H "Authorization: Bearer $TOKEN" \
  -F "expense_data={...}" \
  -F "receipt=@invalid.pdf"

# Check bank account balance NOT changed
curl http://localhost:8000/employees/me \
  -H "Authorization: Bearer $TOKEN"
# Verify: bank_account.balance unchanged
```

## Logging

Added clear logging with `[PAYMENT]` prefix for easy tracking:

```
[PAYMENT] Updated bank account acc_123 balance: $1000.0 -> $1050.0 for expense exp_456
[PAYMENT] Could not retrieve balance for bank account acc_123
[PAYMENT] Employee emp_123 does not have a bank_account_id
[PAYMENT] Failed to update bank account balance: <error>
```

## Related Files

- `backend/services/agents/expense_agent_service.py` - Added bank account update logic
- `backend/services/agents/orchestrator_agent.py` - Still has update logic (for orchestrator-created expenses)
- `backend/BANK_ACCOUNT_AUTO_PAYMENT.md` - Updated documentation

## Future Improvements

1. **Transaction History**: Track all balance changes with timestamps
2. **Notifications**: Send email/notification when payment is processed
3. **Batch Processing**: Process multiple approved expenses at once
4. **Rollback**: Ability to reverse payment if expense is later rejected
5. **Audit Trail**: Link bank account changes to specific expenses in audit log
