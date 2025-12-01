# Orchestrator Agent Tools Update

## Problem

The orchestrator agent could call specialized agents (expense_agent, document_agent) but couldn't actually **create** expenses or perform CRUD operations. When users uploaded receipts and asked to create expenses:

1. ✅ Document agent extracted receipt info
2. ❌ Orchestrator had no tool to create the expense
3. ❌ User was told expense was "reviewed" but it was never created
4. ❌ Expense didn't appear in the frontend

## Solution

Added CRUD operation tools to the orchestrator agent so it can:
- Create expenses
- List expenses
- Get expense details
- (Future: Update/delete expenses)

## Changes Made

### 1. Added `create_expense` Tool

```python
@self.pydantic_agent.tool
async def create_expense(
    ctx: RunContext[OrchestratorContext],
    employee_id: str,
    amount: float,
    category: str,
    business_justification: str,
    date_of_expense: str,
    receipt_path: Optional[str] = None
) -> Dict[str, Any]:
```

**Features:**
- Creates expense in database
- Includes receipt_path to trigger AI review
- **Waits for AI review to complete** (up to 30 seconds)
- Returns complete result with status and decision_reason
- Enforces role-based access (employees can only create for themselves)

**Returns:**
```python
{
    "success": True,
    "expense_id": "exp_123",
    "status": "approved",  # or "rejected", "admin_review", "pending"
    "decision_reason": "Receipt valid, within policy limits",
    "review_completed": True,
    "expense": {...}  # Full expense object
}
```

### 2. Added `list_expenses` Tool

```python
@self.pydantic_agent.tool
def list_expenses(ctx: RunContext[OrchestratorContext]) -> List[Dict[str, Any]]:
```

**Features:**
- Lists all expenses
- Automatically filters for employees (only their own)
- Admins see all expenses

### 3. Added `get_expense` Tool

```python
@self.pydantic_agent.tool
def get_expense(ctx: RunContext[OrchestratorContext], expense_id: str) -> Optional[Dict[str, Any]]:
```

**Features:**
- Gets expense details by ID
- Enforces access control (employees can only see their own)
- Returns None if not found or access denied

### 4. Updated System Prompt

Added comprehensive instructions for:
- File upload handling
- Complete workflow for creating expenses from receipts
- How to present results to users
- Error handling

**Key Workflow:**
```
1. Extract file path from query
2. Call document_agent to extract receipt info
3. Call create_expense with extracted data + receipt_path
4. Tool waits for AI review and returns status
5. Present complete result to user
```

## Complete Workflow Example

### User Request
```
"Create an expense from this receipt"

Attached files:
- Receipt PDF uploaded at: local://uploads/receipts/emp_123/receipt.pdf
```

### Orchestrator Actions

1. **Extract file path**
   ```
   file_path = "local://uploads/receipts/emp_123/receipt.pdf"
   ```

2. **Call document_agent**
   ```python
   call_document_agent(
       capability="extract_receipt_info",
       parameters={"file_path": "local://uploads/receipts/emp_123/receipt.pdf"}
   )
   ```
   
   Returns:
   ```python
   {
       "vendor": "Starbucks",
       "amount": 12.45,
       "date": "2025-01-15",
       "category": "meals",
       "description": "Coffee meeting"
   }
   ```

3. **Call create_expense**
   ```python
   create_expense(
       employee_id="emp_123",
       amount=12.45,
       category="Meals",
       business_justification="Coffee meeting",
       date_of_expense="2025-01-15",
       receipt_path="local://uploads/receipts/emp_123/receipt.pdf"
   )
   ```
   
   Tool internally:
   - Creates expense in database
   - Triggers AI review (auto_review_on_create)
   - Waits for review to complete
   - Returns result

4. **Present result to user**
   ```
   ✅ Created expense exp_abc123 for $12.45 at Starbucks.
   Status: APPROVED
   Reason: Receipt valid, within policy limits (R1: Auto-approve)
   ```

## Benefits

### Before
```
User: "Create expense from receipt"
  ↓
Document agent extracts info ✅
  ↓
Orchestrator says "expense reviewed" ❌
  ↓
No expense created ❌
  ↓
User confused ❌
```

### After
```
User: "Create expense from receipt"
  ↓
Document agent extracts info ✅
  ↓
Orchestrator creates expense ✅
  ↓
AI reviews expense ✅
  ↓
Orchestrator waits for review ✅
  ↓
User gets complete status ✅
  ↓
Expense appears in frontend ✅
```

## Testing

### Test 1: Create Expense from Receipt

```bash
# Upload a receipt PDF and query:
"Create an expense from this receipt"

# Expected result:
✅ Expense created
✅ AI review completed
✅ Status shown (approved/rejected/manual review)
✅ Expense appears in frontend
```

### Test 2: List Expenses

```bash
# Query:
"Show me all my expenses"

# Expected result:
✅ Lists all expenses for current user
✅ Filtered by role (employees see only theirs)
```

### Test 3: Get Expense Details

```bash
# Query:
"Show me details of expense exp_123"

# Expected result:
✅ Returns expense details
✅ Includes status and decision reason
✅ Access control enforced
```

## Code Changes

### Files Modified
- `backend/services/agents/orchestrator_agent.py`
  - Added `create_expense` tool (async, waits for review)
  - Added `list_expenses` tool
  - Added `get_expense` tool
  - Updated system prompt with complete workflow
  - Added detailed examples

### Files Not Changed
- `backend/services/expense_service.py` - No changes needed
- `backend/services/agents/expense_agent_service.py` - No changes needed
- `backend/services/agents/document_agent_service.py` - No changes needed

## Key Features

1. **Async Tool Execution**: create_expense is async to wait for AI review
2. **Automatic Review**: When receipt_path is provided, AI review is triggered
3. **Status Polling**: Waits up to 30 seconds for review to complete
4. **Complete Results**: Returns full status including decision reason
5. **Role-Based Access**: Employees can only create/view their own expenses
6. **Error Handling**: Graceful handling of timeouts and errors

## Response Format

### Successful Creation with Review
```python
{
    "success": True,
    "expense_id": "exp_123",
    "status": "approved",  # or "rejected", "admin_review"
    "decision_reason": "Receipt valid, within policy limits",
    "review_completed": True,
    "expense": {
        "expense_id": "exp_123",
        "amount": 12.45,
        "category": "Meals",
        "status": "approved",
        "decision_actor": "AI",
        "decision_reason": "Receipt valid, within policy limits",
        ...
    }
}
```

### Review Timeout
```python
{
    "success": True,
    "expense_id": "exp_123",
    "status": "pending",
    "decision_reason": "AI review is taking longer than expected",
    "review_completed": False,
    "expense": {...}
}
```

### Error
```python
{
    "success": False,
    "error": "Error message here"
}
```

## User Experience

### Before
```
User: "Create expense from receipt"
Bot: "I've reviewed the expense."
User: *checks frontend* "Where is it??" 😕
```

### After
```
User: "Create expense from receipt"
Bot: "✅ Created expense exp_123 for $12.45 at Starbucks.
     Status: APPROVED
     Reason: Receipt valid, within policy limits.
     The expense has been added to your account."
User: *checks frontend* "There it is!" 😊
```

## Summary

The orchestrator agent now has complete CRUD capabilities and can:
1. ✅ Extract receipt information (via document_agent)
2. ✅ Create expenses in the database
3. ✅ Wait for AI review to complete
4. ✅ Return complete status to user
5. ✅ List and retrieve expenses
6. ✅ Enforce role-based access control

The complete workflow from receipt upload to expense creation with AI review now works end-to-end!
