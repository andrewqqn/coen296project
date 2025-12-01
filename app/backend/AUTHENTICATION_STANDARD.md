# Authentication and Authorization Standard

## Overview

This document defines the standard approach for authentication and authorization across the entire application. Following this standard ensures security, maintainability, and consistency.

## Core Principle

**Backend is the source of truth for identity and permissions.**

The frontend should:
- Send authentication tokens
- Display data
- NOT make authorization decisions
- NOT determine user identity

The backend should:
- Verify authentication tokens
- Extract user identity
- Make authorization decisions
- Filter data based on permissions

## Standard Pattern

### 1. Backend Endpoint Structure

```python
from fastapi import APIRouter, Depends, HTTPException
from infrastructure.auth_middleware import verify_firebase_token
from services import employee_service

@router.get("/resource")
def get_resource(user_claims: dict = Depends(verify_firebase_token)):
    """
    Standard authenticated endpoint pattern
    """
    # Step 1: Extract Firebase UID from verified token
    firebase_uid = user_claims.get("uid")
    
    # Step 2: Get employee record (converts to internal ID)
    employee = employee_service.get_employee_by_auth_id(firebase_uid)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    # Step 3: Extract internal employee_id and role
    employee_id = employee.get("employee_id")
    role = employee.get("role")
    
    # Step 4: Apply business logic with internal IDs
    # ... your logic here ...
    
    return result
```

### 2. Frontend Request Pattern

```typescript
// Get auth token
const token = await getAuthToken();

// Make request with ONLY the token
const response = await fetch(`${backendUrl}/resource`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    // Data fields only - NO employee_id or user identity
    amount: 100,
    description: "Business expense"
  })
});
```

## Implementation Examples

### Example 1: Create Expense (Correct ✓)

**Frontend:**
```typescript
const expenseData = {
  amount: parseFloat(formData.amount),
  business_justification: formData.business_justification,
  category: formData.category,
  date_of_expense: new Date(formData.date_of_expense).toISOString(),
  // NO employee_id - backend determines this from token
};

const response = await fetch(`${backendUrl}/expenses`, {
  method: "POST",
  headers: { Authorization: `Bearer ${token}` },
  body: formData
});
```

**Backend:**
```python
@router.post("/expenses")
async def create_expense(
    expense_data: str = Form(...),
    receipt: UploadFile = File(...),
    user_claims: dict = Depends(verify_firebase_token)
):
    firebase_uid = user_claims.get("uid")
    employee = employee_service.get_employee_by_auth_id(firebase_uid)
    employee_id = employee.get("employee_id")
    
    # SECURITY: Set employee_id from authenticated user
    data_dict = json.loads(expense_data)
    data_dict["employee_id"] = employee_id
    
    expense_create = ExpenseCreate(**data_dict)
    return await expense_service.create_expense_with_file(expense_create, receipt)
```

### Example 2: List Expenses (Correct ✓)

**Frontend:**
```typescript
// Simple request - backend handles filtering
const response = await fetch(`${backendUrl}/expenses`, {
  headers: { Authorization: `Bearer ${token}` }
});
const expenses = await response.json();
```

**Backend:**
```python
@router.get("/expenses")
def list_expense(user_claims: dict = Depends(verify_firebase_token)):
    firebase_uid = user_claims.get("uid")
    employee = employee_service.get_employee_by_auth_id(firebase_uid)
    employee_id = employee.get("employee_id")
    role = employee.get("role")
    
    all_expenses = expense_service.list_expenses()
    
    # Backend filters based on role
    if role == "admin":
        return all_expenses
    else:
        return [exp for exp in all_expenses if exp.get("employee_id") == employee_id]
```

## Anti-Patterns (Don't Do This ✗)

### ✗ Frontend Determines Identity

```typescript
// WRONG - Don't send user identity from frontend
const expenseData = {
  employee_id: user.uid,  // ✗ Security risk!
  amount: 100
};
```

**Why wrong:** Client can manipulate this to create expenses for other users.

### ✗ Frontend Filters Data

```typescript
// WRONG - Don't filter on frontend
const allExpenses = await fetch(`${backendUrl}/expenses`);
const myExpenses = allExpenses.filter(exp => exp.employee_id === user.uid);
```

**Why wrong:** 
- Exposes other users' data to client
- Client can bypass filter
- Inconsistent with backend logic

### ✗ No Authentication

```python
# WRONG - No auth check
@router.post("/expenses")
async def create_expense(expense_data: ExpenseCreate):
    return expense_service.create_expense(expense_data)
```

**Why wrong:**
- Anyone can create expenses
- No way to verify user identity
- Security vulnerability

## ID Usage Rules

### Two Types of IDs

1. **Firebase Authentication UID** (`authentication_id`)
   - External ID from Firebase Auth
   - Used ONLY for authentication
   - Format: Firebase-generated string
   - Example: "firebase_abc123xyz"

2. **Internal Employee ID** (`employee_id`)
   - Internal database ID
   - Used for ALL business logic
   - Format: "emp_" prefix + unique ID
   - Example: "emp_123"

### Conversion Pattern

```python
# Always convert at the boundary
firebase_uid = user_claims.get("uid")  # From auth token
employee = employee_service.get_employee_by_auth_id(firebase_uid)
employee_id = employee.get("employee_id")  # Use this for everything
```

### Where to Use Each ID

| Context | Use Firebase UID | Use Internal employee_id |
|---------|-----------------|-------------------------|
| Authentication | ✓ | ✗ |
| Database queries | ✗ | ✓ |
| Business logic | ✗ | ✓ |
| Foreign keys | ✗ | ✓ |
| API responses | ✗ | ✓ |
| Frontend display | ✗ | ✓ |

## Migration Checklist

When updating an endpoint to follow this standard:

- [ ] Add `Depends(verify_firebase_token)` to endpoint
- [ ] Extract Firebase UID from `user_claims`
- [ ] Convert to internal employee_id using `get_employee_by_auth_id()`
- [ ] Remove employee_id from request body/parameters
- [ ] Set employee_id in backend from authenticated user
- [ ] Add role-based filtering if needed
- [ ] Update frontend to NOT send employee_id
- [ ] Update frontend to NOT filter data
- [ ] Test with different users and roles
- [ ] Verify security (can't access other users' data)

## Benefits of This Approach

1. **Security**: Identity determined by cryptographically verified token, not client input
2. **Maintainability**: Single source of truth for auth logic
3. **Consistency**: Same pattern across all endpoints
4. **Simplicity**: Frontend code is simpler
5. **Testability**: Auth logic centralized and easier to test
6. **Auditability**: All identity decisions logged in backend

## Endpoints Following This Standard

✓ `/agents/query` - Multi-agent system
✓ `/agents/query-with-files` - Multi-agent with files
✓ `/orchestrator` - Legacy orchestrator
✓ `/expenses` (GET) - List expenses
✓ `/expenses` (POST) - Create expense
✓ `/employees/me` - Get current employee

## Endpoints Needing Update

Review and update these endpoints to follow the standard:
- `/expenses/{expense_id}` (PATCH) - Should verify ownership
- `/expenses/{expense_id}` (DELETE) - Should verify ownership
- Other endpoints as needed

## Testing Authentication

```python
# Test script
import requests

# Valid token
token = "valid_firebase_token"
response = requests.get(
    "http://localhost:8000/expenses",
    headers={"Authorization": f"Bearer {token}"}
)
assert response.status_code == 200

# Invalid token
response = requests.get(
    "http://localhost:8000/expenses",
    headers={"Authorization": "Bearer invalid"}
)
assert response.status_code == 401

# No token
response = requests.get("http://localhost:8000/expenses")
assert response.status_code == 403
```

## Questions?

If you're unsure whether an endpoint follows this standard, ask:
1. Does it use `Depends(verify_firebase_token)`?
2. Does it convert Firebase UID to internal employee_id?
3. Does it ignore client-sent identity fields?
4. Does it make authorization decisions server-side?

If any answer is "no", the endpoint needs updating.
