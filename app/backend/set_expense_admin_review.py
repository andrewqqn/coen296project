"""
Helper script to set an expense to admin_review status for testing
"""
from infrastructure.firebase_client import get_firestore_client
from datetime import datetime

def set_expense_to_admin_review(expense_id: str):
    """Set an expense to admin_review status"""
    db = get_firestore_client()
    
    # Update the expense
    expense_ref = db.collection('expenses').document(expense_id)
    expense_doc = expense_ref.get()
    
    if not expense_doc.exists:
        print(f"❌ Expense {expense_id} not found")
        return False
    
    expense_ref.update({
        'status': 'admin_review',
        'updated_at': datetime.utcnow().isoformat()
    })
    
    print(f"✓ Expense {expense_id} set to admin_review status")
    return True


def list_expenses():
    """List all expenses to help find one to test with"""
    db = get_firestore_client()
    expenses = db.collection('expenses').stream()
    
    print("\nAvailable Expenses:")
    print("-" * 80)
    
    for doc in expenses:
        expense = doc.to_dict()
        print(f"ID: {doc.id}")
        print(f"  Employee: {expense.get('employee_id')}")
        print(f"  Amount: ${expense.get('amount')}")
        print(f"  Category: {expense.get('category')}")
        print(f"  Status: {expense.get('status')}")
        print(f"  Submitted: {expense.get('submitted_at')}")
        print()


if __name__ == "__main__":
    import sys
    
    print("Set Expense to Admin Review Status")
    print("=" * 80)
    
    if len(sys.argv) > 1:
        expense_id = sys.argv[1]
        set_expense_to_admin_review(expense_id)
    else:
        print("\nUsage: python set_expense_admin_review.py <expense_id>")
        print("\nOr run without arguments to list all expenses:\n")
        
        list_expenses()
        
        expense_id = input("\nEnter expense ID to set to admin_review (or press Enter to exit): ").strip()
        if expense_id:
            set_expense_to_admin_review(expense_id)
