# Role-Based Access Control (RBAC) Implementation

## Overview
The orchestrator service now implements role-based access control with two roles:
- **Admin**: Full access to all tools and data
- **Employee**: Limited access to their own expenses and view-only access to policies

## Implementation Details

### User Context
Each request now includes:
- `employee_id`: The employee's unique identifier
- `role`: Either "employee" or "admin"

### Tool Access by Role

#### Admin Tools (Full Access)
- **Employee Management**: list, get, create, update, delete employees
- **Expense Management**: list, get, create, update, delete ALL expenses
- **Policy Management**: list, create, update, delete policies
- **Audit Logs**: list and create audit logs
- **Receipt Processing**: process PDF receipts

#### Employee Tools (Limited Access)
- **Expense Management**: list, get, create, update, delete ONLY THEIR OWN expenses
- **Policy Viewing**: list all policies (read-only)
- **Receipt Processing**: process PDF receipts for themselves

### Data Filtering for Employees

When an employee uses expense tools:
1. `list_all_expenses`: Automatically filters to show only expenses where `employee_id` matches the user
2. `get_expense_by_id`: Returns `None` if the expense doesn't belong to the user
3. `create_new_expense`: Always creates expenses for the user's own `employee_id`
4. `update_existing_expense`: Checks ownership before allowing updates
5. `delete_existing_expense`: Checks ownership before allowing deletion

### Authentication Flow

1. User authenticates with Firebase (gets ID token)
2. Frontend sends request with Bearer token
3. Backend verifies token and extracts `authentication_id` (Firebase UID)
4. Backend looks up employee record by `authentication_id`
5. Backend extracts `employee_id` and `role` from employee record
6. Backend creates role-specific agent with appropriate tools
7. Agent processes query with user context

## Testing

### Test as Admin
```bash
# Assuming you have an admin user with authentication_id in the system
curl -X POST http://localhost:8000/orchestrator \
  -H "Authorization: Bearer <admin_firebase_token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "List all employees"}'
```

### Test as Employee
```bash
# Assuming you have an employee user with authentication_id in the system
curl -X POST http://localhost:8000/orchestrator \
  -H "Authorization: Bearer <employee_firebase_token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me my expenses"}'
```

### Expected Behavior

**Admin queries:**
- "List all employees" → Returns all employees
- "Show all expenses" → Returns all expenses from all employees
- "Create a policy" → Successfully creates policy

**Employee queries:**
- "List all employees" → Error: Tool not available
- "Show all expenses" → Returns only their own expenses
- "Show me expenses for employee emp123" → Returns only their own expenses (filtered)
- "Create a policy" → Error: Tool not available
- "What are the reimbursement policies?" → Returns all policies (read-only)

## Security Notes

1. Employee role cannot access other employees' data
2. Employee role cannot manage employees, policies, or audit logs
3. All filtering happens at the tool level, not just in the LLM prompt
4. Access control is enforced before any database operations
5. Unauthorized access attempts are logged

## Future Enhancements

- Add more granular roles (e.g., manager, finance)
- Implement department-based access control
- Add approval workflows for expenses
- Implement expense status transitions (pending → approved → reimbursed)
