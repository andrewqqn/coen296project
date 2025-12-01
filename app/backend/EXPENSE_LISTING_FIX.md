# Expense Listing Fix - Firebase UID vs Employee ID

## Problem

Expenses created through the orchestrator agent were not showing up in the Expenses tab of the frontend.

## Root Cause

The issue was a mismatch between **Firebase Authentication UID** and **internal Employee ID**:

### Data Model
- **Employee** has two IDs:
  - `authentication_id`: Firebase Auth UID (e.g., "firebase_abc123")
  - `employee_id`: Internal employee ID (e.g., "emp_123")

- **Expense** has:
  - `employee_id`: Should reference the internal employee ID

### The Bug

1. **Orchestrator Router** was passing Firebase UID directly:
   ```python
   employee_id = user_claims.get("uid")  # This is Firebase UID!
   ```

2. **Orchestrator Agent** was using this Firebase UID as the employee_id when creating expenses:
   ```python
   employee_id = ctx.deps.user_id  # Still Firebase UID
   ```

3. **Frontend** was filtering expenses by Firebase UID:
   ```typescript
   expensesData = allExpenses.filter(
     (exp: Expense) => exp.employee_id === user?.uid  // Firebase UID
   );
   ```

4. **Result**: Expenses were created with Firebase UID as employee_id, but the database lookup expected internal employee_id, causing a mismatch.

## Solution

### Backend Fix

Updated `backend/controller/orchestrator_router.py` to convert Firebase UID to internal employee_id:

```python
# Before
employee_id = user_claims.get("uid")

# After
firebase_uid = user_claims.get("uid")

# Convert Firebase UID to internal employee_id
from services import employee_service
employee = employee_service.get_employee_by_auth_id(firebase_uid)
if not employee:
    raise HTTPException(status_code=404, detail="Employee profile not found")

employee_id = employee.get("employee_id")
```

This ensures:
1. The orchestrator receives the correct internal employee_id
2. Expenses are created with the correct employee_id
3. The frontend can properly filter and display expenses

### Why Agents Router Worked

The `/agents/query` endpoint already had this conversion logic:

```python
auth_uid = user_claims.get("uid")
employee = employee_service.get_employee_by_auth_id(auth_uid)
employee_id = employee.get("employee_id")
```

This is why expenses created through the agents endpoint worked correctly, but the legacy orchestrator endpoint did not.

## Testing

To verify the fix:

1. **Create an expense through orchestrator**:
   ```
   POST /orchestrator
   {
     "query": "Create an expense from this receipt",
     "files": [receipt.pdf]
   }
   ```

2. **Check the expense in database**:
   - `employee_id` should be internal ID (e.g., "emp_123")
   - NOT Firebase UID (e.g., "firebase_abc123")

3. **Verify in frontend**:
   - Expense should appear in the Expenses tab
   - Should be properly filtered by user

## Related Files

- `backend/controller/orchestrator_router.py` - Fixed
- `backend/controller/agents_router.py` - Already correct
- `backend/services/agents/orchestrator_agent.py` - Uses employee_id correctly
- `backend/domain/models/employee.py` - Defines both IDs
- `frontend/components/expense-list.tsx` - Filters by Firebase UID

## Additional Fix

Also restored the initial bank account balance for new employees from 0.0 to 1000.0 in the orchestrator agent's `create_employee` tool.
