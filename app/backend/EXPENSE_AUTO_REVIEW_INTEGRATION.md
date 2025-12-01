# Expense Auto-Review Integration with Orchestrator

## Overview
The orchestrator now waits for AI auto-review results after creating an expense and returns a formatted response to the frontend based on the review outcome.

## Changes Made

### 1. Modified `backend/services/orchestrator_service.py`

#### `create_new_expense` Tool Enhancement
- After creating an expense, the tool now polls the database to wait for AI review completion
- Implements a 30-second timeout with 1-second polling intervals
- Checks for `decision_actor == 'AI'` and status in `['approved', 'rejected', 'admin_review']`
- Returns enhanced expense data with review metadata:
  - `review_completed`: Boolean indicating if review finished
  - `review_status`: The final status (approved/rejected/admin_review/pending)
  - `review_reason`: The AI's decision reason
  - `expense_id`: The expense identifier

#### `process_query` Response Enhancement
- Detects when an expense was created with review results
- Appends user-friendly status messages to the response:
  - ✅ **Approved**: "Your expense of $X has been automatically approved"
  - ❌ **Rejected**: "Your expense was rejected. Reason: ..."
  - ⏳ **Manual Review**: "Your expense has been flagged for manual review"
  - ⏳ **Pending**: "Your expense is being reviewed. Please check back shortly"
- Returns `expense_review` object in the response for frontend consumption

### 2. Flow Diagram

```
User uploads receipt → Orchestrator processes query
                              ↓
                    create_new_expense tool called
                              ↓
                    Expense created in Firestore
                              ↓
                    auto_review_on_create triggered
                              ↓
                    AI analyzes receipt (async)
                              ↓
                    Orchestrator polls for result (max 30s)
                              ↓
                    AI updates expense status
                              ↓
                    Orchestrator detects completion
                              ↓
                    Enhanced response returned to frontend
```

## API Response Structure

### Success Response with Review
```json
{
  "success": true,
  "response": "I've created your expense...\n\n✅ **Expense Approved!**\nYour expense of $93.50 has been automatically approved by our AI system.",
  "tools_used": [],
  "query": "Create an expense from this receipt",
  "user_role": "employee",
  "expense_review": {
    "expense_id": "abc123",
    "status": "approved",
    "reason": "R1: Receipt is valid and matches submitted details",
    "amount": 93.50,
    "category": "Other",
    "completed": true
  }
}
```

### Timeout Response
```json
{
  "success": true,
  "response": "I've created your expense...\n\n⏳ **Review Pending**\nYour expense has been submitted and is being reviewed.",
  "expense_review": {
    "expense_id": "abc123",
    "status": "pending",
    "reason": "AI review is taking longer than expected",
    "amount": 93.50,
    "category": "Other",
    "completed": false
  }
}
```

## Frontend Integration

The frontend can now:
1. Display the enhanced response text with status emojis
2. Access structured review data via `expense_review` object
3. Show appropriate UI based on `expense_review.status`:
   - Green checkmark for "approved"
   - Red X for "rejected"
   - Yellow clock for "admin_review" or "pending"

## Configuration

### Timeout Settings
Located in `create_new_expense` tool:
```python
max_wait_time = 30  # seconds
poll_interval = 1   # second
```

Adjust these values based on:
- Average AI review time
- User experience requirements
- Server load considerations

## Testing

Test the integration by:
1. Uploading a receipt PDF via the orchestrator
2. Asking to create an expense
3. Verifying the response includes review status
4. Checking that the expense status in Firestore matches

Example test query:
```
"Create an expense from this receipt" (with PDF attached)
```

## Notes

- The AI review runs synchronously from the orchestrator's perspective but asynchronously in the expense service
- If the review takes longer than 30 seconds, the user gets a "pending" status but the review continues in the background
- The expense is always created immediately; the wait is only for the review result
- Employees can only create expenses for themselves; admins can specify an employee_id
