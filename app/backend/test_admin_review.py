"""
Test script for admin expense review functionality
"""
import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"

def test_admin_review():
    """
    Test the admin review endpoint.
    
    Prerequisites:
    1. Backend server running
    2. Firebase emulator running
    3. An expense with status="admin_review" exists
    4. Admin user authenticated
    """
    
    print("=" * 60)
    print("Admin Expense Review Test")
    print("=" * 60)
    
    # You'll need to replace these with actual values
    admin_token = input("Enter admin Firebase token: ").strip()
    expense_id = input("Enter expense ID to review: ").strip()
    
    if not admin_token or not expense_id:
        print("❌ Token and expense ID are required")
        return
    
    # Test 1: Get the expense first
    print("\n1. Fetching expense details...")
    response = requests.get(
        f"{BACKEND_URL}/expenses/{expense_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if response.status_code == 200:
        expense = response.json()
        print(f"✓ Expense found: {expense['category']} - ${expense['amount']}")
        print(f"  Status: {expense['status']}")
        print(f"  Employee: {expense['employee_id']}")
        
        if expense['status'] != 'admin_review':
            print(f"⚠️  Warning: Expense status is '{expense['status']}', not 'admin_review'")
            print("   The review endpoint will reject this.")
    else:
        print(f"❌ Failed to fetch expense: {response.status_code}")
        print(f"   {response.text}")
        return
    
    # Test 2: Submit review
    action = input("\nEnter action (approve/reject): ").strip().lower()
    if action not in ['approve', 'reject']:
        print("❌ Invalid action. Must be 'approve' or 'reject'")
        return
    
    reason = input("Enter reason: ").strip()
    if not reason:
        print("❌ Reason is required")
        return
    
    print(f"\n2. Submitting {action} review...")
    response = requests.post(
        f"{BACKEND_URL}/expenses/{expense_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        data={
            "action": action,
            "reason": reason
        }
    )
    
    if response.status_code == 200:
        updated_expense = response.json()
        print(f"✓ Review submitted successfully!")
        print(f"  New status: {updated_expense['status']}")
        print(f"  Decision actor: {updated_expense['decision_actor']}")
        print(f"  Decision reason: {updated_expense['decision_reason']}")
    else:
        print(f"❌ Failed to submit review: {response.status_code}")
        print(f"   {response.text}")
        return
    
    print("\n" + "=" * 60)
    print("Test completed successfully! ✓")
    print("=" * 60)


def test_non_admin_access():
    """
    Test that non-admin users cannot access the review endpoint.
    """
    print("\n" + "=" * 60)
    print("Non-Admin Access Test")
    print("=" * 60)
    
    employee_token = input("Enter employee (non-admin) Firebase token: ").strip()
    expense_id = input("Enter expense ID: ").strip()
    
    if not employee_token or not expense_id:
        print("❌ Token and expense ID are required")
        return
    
    print("\nAttempting to review as non-admin...")
    response = requests.post(
        f"{BACKEND_URL}/expenses/{expense_id}/review",
        headers={"Authorization": f"Bearer {employee_token}"},
        data={
            "action": "approve",
            "reason": "Test reason"
        }
    )
    
    if response.status_code == 403:
        print("✓ Correctly rejected non-admin user (403 Forbidden)")
    else:
        print(f"❌ Unexpected response: {response.status_code}")
        print(f"   Expected 403, got {response.status_code}")
        print(f"   {response.text}")


if __name__ == "__main__":
    print("\nAdmin Expense Review Test Suite")
    print("================================\n")
    print("Choose a test:")
    print("1. Test admin review (happy path)")
    print("2. Test non-admin access (should fail)")
    print("3. Run both tests")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        test_admin_review()
    elif choice == "2":
        test_non_admin_access()
    elif choice == "3":
        test_admin_review()
        test_non_admin_access()
    else:
        print("Invalid choice")
