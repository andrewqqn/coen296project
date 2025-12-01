"""
Verification script to check expense employee_id consistency
"""
from services import expense_service, employee_service


def verify_expense_ids():
    """
    Check all expenses and verify their employee_ids are valid
    """
    print("=" * 60)
    print("Expense Employee ID Verification")
    print("=" * 60)
    
    expenses = expense_service.list_expenses()
    employees = employee_service.list_employees()
    
    # Build lookup maps
    employee_by_internal_id = {e.get('employee_id'): e for e in employees}
    employee_by_auth_id = {e.get('authentication_id'): e for e in employees}
    
    print(f"\nTotal Expenses: {len(expenses)}")
    print(f"Total Employees: {len(employees)}")
    
    # Categorize expenses
    valid_internal_id = []
    valid_firebase_uid = []
    invalid = []
    
    for expense in expenses:
        expense_id = expense.get('expense_id')
        employee_id = expense.get('employee_id')
        
        if employee_id in employee_by_internal_id:
            valid_internal_id.append(expense)
        elif employee_id in employee_by_auth_id:
            valid_firebase_uid.append(expense)
        else:
            invalid.append(expense)
    
    print(f"\n✓ Expenses with valid internal employee_id: {len(valid_internal_id)}")
    print(f"⚠ Expenses with Firebase UID (old format): {len(valid_firebase_uid)}")
    print(f"✗ Expenses with invalid employee_id: {len(invalid)}")
    
    # Show details
    if valid_internal_id:
        print(f"\n--- Expenses with Internal ID (Correct) ---")
        for exp in valid_internal_id[:5]:  # Show first 5
            emp = employee_by_internal_id[exp.get('employee_id')]
            print(f"  {exp.get('expense_id')}: ${exp.get('amount')} - {emp.get('name')} ({exp.get('employee_id')})")
        if len(valid_internal_id) > 5:
            print(f"  ... and {len(valid_internal_id) - 5} more")
    
    if valid_firebase_uid:
        print(f"\n--- Expenses with Firebase UID (Old Format) ---")
        for exp in valid_firebase_uid[:5]:  # Show first 5
            emp = employee_by_auth_id[exp.get('employee_id')]
            print(f"  {exp.get('expense_id')}: ${exp.get('amount')} - {emp.get('name')} (Firebase UID: {exp.get('employee_id')[:20]}...)")
        if len(valid_firebase_uid) > 5:
            print(f"  ... and {len(valid_firebase_uid) - 5} more")
    
    if invalid:
        print(f"\n--- Invalid Expenses (Need Attention) ---")
        for exp in invalid:
            print(f"  {exp.get('expense_id')}: ${exp.get('amount')} - Invalid employee_id: {exp.get('employee_id')}")
    
    # Summary
    print(f"\n{'=' * 60}")
    print("Summary:")
    print(f"  ✓ {len(valid_internal_id)} expenses use correct internal employee_id")
    print(f"  ⚠ {len(valid_firebase_uid)} expenses use old Firebase UID format")
    print(f"  ✗ {len(invalid)} expenses have invalid employee_id")
    
    if valid_firebase_uid:
        print(f"\nNote: {len(valid_firebase_uid)} expenses still use Firebase UID.")
        print("These will still work due to backward compatibility in the frontend.")
        print("Consider running a migration to convert them to internal IDs.")
    
    if invalid:
        print(f"\n⚠ WARNING: {len(invalid)} expenses have invalid employee_ids!")
        print("These expenses may not be visible to any user.")


if __name__ == "__main__":
    verify_expense_ids()
