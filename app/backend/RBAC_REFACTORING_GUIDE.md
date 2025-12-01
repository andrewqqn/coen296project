# RBAC Refactoring Guide

## Current Problems

### 1. Inconsistent Permission Checks
**Before:**
```python
@agent.tool
def list_employees(ctx):
    # Permission check inside function
    if ctx.deps.role != "admin":
        return [{"error": "Access denied: Admin only"}]
    # ... rest of function
```

**Problems:**
- Permission logic mixed with business logic
- Easy to forget permission checks
- Inconsistent error formats
- Hard to audit who can access what

### 2. No Role Hierarchy
- Admin should automatically have all employee permissions
- Currently need to check both roles separately

### 3. Scattered Ownership Checks
```python
# Repeated in multiple places
if ctx.deps.role == "employee":
    filtered = [exp for exp in all_expenses if exp.get("employee_id") == ctx.deps.user_id]
```

## Solution: Decorator-Based RBAC

### 1. Use `@require_role` Decorator

**After:**
```python
from utils.rbac import require_role, filter_by_ownership

@agent.tool
@require_role("admin")
def list_employees(ctx):
    # No permission check needed - decorator handles it
    employees = employee_service.list_employees()
    return employees

@agent.tool
@require_role("employee", "admin")  # Both roles allowed
def list_expenses(ctx):
    all_expenses = expense_service.list_expenses()
    # Automatic filtering based on role
    return filter_by_ownership(ctx, all_expenses, owner_field="employee_id")
```

### 2. Benefits

✅ **Separation of Concerns**: Permission logic separate from business logic
✅ **Declarative**: Clear which roles can access each tool
✅ **DRY**: No repeated permission checks
✅ **Auditable**: Easy to see all permissions at a glance
✅ **Consistent**: Same error format everywhere
✅ **Type-Safe**: Decorator preserves function signatures

### 3. Role Hierarchy

```python
ROLE_HIERARCHY = {
    "admin": ["admin", "employee"],  # Admin has all employee permissions
    "employee": ["employee"]
}
```

This means:
- Admin can use tools marked `@require_role("employee")`
- Admin can use tools marked `@require_role("admin")`
- Employee can only use tools marked `@require_role("employee")`

## Refactoring Steps

### Step 1: Import RBAC utilities

```python
from utils.rbac import require_role, filter_by_ownership, check_ownership
```

### Step 2: Add decorators to tools

**Employee Management (Admin Only):**
```python
@agent.tool
@require_role("admin")
def list_employees(ctx):
    return employee_service.list_employees()

@agent.tool
@require_role("admin")
def create_employee(ctx, name, email, department, role="employee"):
    data = {"name": name, "email": email, "department": department, "role": role}
    return employee_service.create_employee(data)
```

**Expense Management (Both Roles):**
```python
@agent.tool
@require_role("employee", "admin")
def list_expenses(ctx):
    all_expenses = expense_service.list_expenses()
    return filter_by_ownership(ctx, all_expenses)

@agent.tool
@require_role("employee", "admin")
def get_expense(ctx, expense_id):
    expense = expense_service.get_expense(expense_id)
    if not expense:
        return None
    
    # Check ownership
    if not check_ownership(ctx, expense):
        logger.warning(f"User {ctx.deps.user_id} attempted to access expense {expense_id}")
        return None
    
    return expense
```

### Step 3: Remove manual permission checks

**Before:**
```python
def create_expense(ctx, employee_id, amount, ...):
    # Manual check
    if ctx.deps.role == "employee":
        actual_employee_id = ctx.deps.user_id
    else:
        actual_employee_id = employee_id or ctx.deps.user_id
    # ... rest
```

**After:**
```python
@require_role("employee", "admin")
def create_expense(ctx, employee_id, amount, ...):
    # Automatic - decorator already checked permission
    # For employees, enforce ownership
    if ctx.deps.role == "employee":
        employee_id = ctx.deps.user_id
    # ... rest
```

## Permission Matrix

| Tool | Employee | Admin | Notes |
|------|----------|-------|-------|
| **Employee Management** |
| list_employees | ❌ | ✅ | Admin only |
| get_employee | ❌ | ✅ | Admin only |
| create_employee | ❌ | ✅ | Admin only |
| update_employee | ❌ | ✅ | Admin only |
| delete_employee | ❌ | ✅ | Admin only |
| **Expense Management** |
| list_expenses | ✅ (own) | ✅ (all) | Filtered by ownership |
| get_expense | ✅ (own) | ✅ (all) | Ownership check |
| create_expense | ✅ (own) | ✅ (any) | Employee creates for self |
| update_expense | ✅ (own) | ✅ (any) | Ownership check |
| delete_expense | ✅ (own) | ✅ (any) | Ownership check |
| **Policy & Agents** |
| query_policies | ✅ | ✅ | Public |
| list_available_agents | ✅ | ✅ | Public |
| call_document_agent | ✅ | ✅ | Public |
| call_expense_agent | ✅ | ✅ | Public |

## Implementation Example

```python
class OrchestratorAgent(BaseAgent):
    def _register_agent_tools(self):
        from utils.rbac import require_role, filter_by_ownership, check_ownership
        
        # ============================================================
        # EMPLOYEE MANAGEMENT (Admin Only)
        # ============================================================
        
        @self.pydantic_agent.tool
        @require_role("admin")
        def list_employees(ctx: RunContext[OrchestratorContext]) -> List[Dict]:
            """List all employees. Admin only."""
            from services import employee_service
            logger.info(f"Admin {ctx.deps.user_id} listing employees")
            return employee_service.list_employees()
        
        @self.pydantic_agent.tool
        @require_role("admin")
        def create_employee(
            ctx: RunContext[OrchestratorContext],
            name: str,
            email: str,
            department: str,
            role: str = "employee"
        ) -> Dict:
            """Create employee. Admin only."""
            from services import employee_service
            logger.info(f"Admin {ctx.deps.user_id} creating employee: {name}")
            data = {
                "name": name,
                "email": email,
                "department": department,
                "role": role
            }
            return employee_service.create_employee(data)
        
        # ============================================================
        # EXPENSE MANAGEMENT (Both Roles, Filtered)
        # ============================================================
        
        @self.pydantic_agent.tool
        @require_role("employee", "admin")
        def list_expenses(ctx: RunContext[OrchestratorContext]) -> List[Dict]:
            """List expenses. Employees see own, admins see all."""
            from services import expense_service
            logger.info(f"Listing expenses for {ctx.deps.role} user {ctx.deps.user_id}")
            
            all_expenses = expense_service.list_expenses()
            return filter_by_ownership(ctx, all_expenses, owner_field="employee_id")
        
        @self.pydantic_agent.tool
        @require_role("employee", "admin")
        async def create_expense(
            ctx: RunContext[OrchestratorContext],
            employee_id: str,
            amount: float,
            category: str,
            business_justification: str,
            date_of_expense: str,
            receipt_path: Optional[str] = None
        ) -> Dict:
            """Create expense. Employees create for self, admins for anyone."""
            from services import expense_service
            from domain.schemas.expense_schema import ExpenseCreate
            from datetime import datetime
            
            # Employees can only create for themselves
            if ctx.deps.role == "employee":
                employee_id = ctx.deps.user_id
            
            logger.info(f"Creating expense for {employee_id}: ${amount}")
            
            expense_create = ExpenseCreate(
                employee_id=employee_id,
                amount=amount,
                category=category,
                business_justification=business_justification,
                date_of_expense=datetime.fromisoformat(date_of_expense)
            )
            
            result = expense_service.create_expense(expense_create, receipt_path)
            # ... rest of implementation
```

## Testing RBAC

### Test 1: Admin Access
```python
# Admin should be able to list employees
ctx = OrchestratorContext(user_id="admin_123", role="admin")
result = list_employees(ctx)
assert "error" not in result
```

### Test 2: Employee Denied
```python
# Employee should NOT be able to list employees
ctx = OrchestratorContext(user_id="emp_123", role="employee")
result = list_employees(ctx)
assert "error" in result
assert "Access denied" in result["error"]
```

### Test 3: Ownership Filtering
```python
# Employee should only see their own expenses
ctx = OrchestratorContext(user_id="emp_123", role="employee")
result = list_expenses(ctx)
assert all(exp["employee_id"] == "emp_123" for exp in result)
```

## Migration Checklist

- [ ] Create `utils/rbac.py` with decorators
- [ ] Update `orchestrator_agent.py` to use decorators
- [ ] Remove manual permission checks from tools
- [ ] Add `@require_role` to all tools
- [ ] Use `filter_by_ownership` for list operations
- [ ] Use `check_ownership` for single-item operations
- [ ] Test admin access
- [ ] Test employee access
- [ ] Test ownership filtering
- [ ] Update documentation

## Summary

The decorator-based RBAC approach provides:

1. **Clear Permissions**: Easy to see who can access what
2. **Consistent Enforcement**: Can't forget permission checks
3. **Maintainable**: Changes in one place affect all tools
4. **Auditable**: Simple to generate permission reports
5. **Testable**: Easy to unit test permission logic

This is a standard pattern used in frameworks like Django, Flask-Security, and FastAPI-Users.
