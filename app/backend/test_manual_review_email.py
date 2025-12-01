"""
Test manual review email notification
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_manual_review():
    """Simulate manual review and email sending"""
    print("\n" + "="*70)
    print("Testing Manual Review Email Notification")
    print("="*70)
    
    from services import expense_service, employee_service
    from domain.schemas.expense_schema import ExpenseCreate
    from datetime import datetime, timezone
    from domain.repositories import expense_repo
    
    # Create employee
    print("\n📋 Creating employee...")
    try:
        employee = employee_service.create_employee({
            "name": "Test User",
            "email": "nguyen.andrew.quang@gmail.com",
            "department": "Engineering",
            "role": "employee"
        })
        emp_id = employee.get("employee_id")
        print(f"✅ Created employee: {emp_id}")
    except Exception as e:
        print(f"⚠️  Using existing employee")
        emp_id = "test_emp"
    
    # Create expense
    print("\n📝 Creating expense...")
    expense = expense_service.create_expense(
        ExpenseCreate(
            employee_id=emp_id,
            amount=650.00,
            category="Travel",
            business_justification="Conference travel",
            date_of_expense=datetime.now(timezone.utc)
        ),
        receipt_path=None
    )
    
    expense_dict = expense.dict() if hasattr(expense, 'dict') else expense
    expense_id = expense_dict.get('expense_id') or expense_dict.get('id')
    print(f"✅ Created expense: {expense_id}")
    
    # Set to admin_review
    print("\n⏳ Setting to admin_review status...")
    expense_repo.update(expense_id, {
        "status": "admin_review",
        "decision_actor": "AI",
        "decision_reason": "R3: Amount exceeds $500"
    })
    
    # Simulate admin approval with email
    print("\n👤 Admin approving expense...")
    expense_repo.update(expense_id, {
        "status": "approved",
        "decision_actor": "Human",
        "decision_reason": "Manual Review: Approved for conference"
    })
    
    # Send email (simulating what the endpoint does)
    print("\n📧 Sending email notification...")
    
    import asyncio
    import threading
    from services.agents.email_agent_service import email_agent
    from services.agents.a2a_protocol import A2ARequest, create_a2a_message
    
    email_request = A2ARequest(
        capability_name="send_expense_notification",
        parameters={
            "to": "nguyen.andrew.quang@gmail.com",
            "expense_id": expense_id,
            "status": "approved",
            "amount": 650.00,
            "category": "Travel",
            "decision_reason": "Manual Review: Approved for conference"
        },
        context={"user_id": "admin", "role": "admin"}
    )
    
    message = create_a2a_message(
        sender_id="admin_review",
        recipient_id="email_agent",
        message_type="request",
        payload=email_request.model_dump(),
        capability_name="send_expense_notification"
    )
    
    # Send in background thread (like the endpoint does)
    result = {"sent": False}
    
    def send_notification_sync():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            response = loop.run_until_complete(
                email_agent.process_message(
                    message,
                    context={"user_id": "admin", "role": "admin"}
                )
            )
            
            if response.message_type == "response":
                result["sent"] = True
                result["data"] = response.payload.get("result", {})
                print(f"✅ Email sent!")
                print(f"   Message ID: {result['data'].get('message_id')}")
            else:
                print(f"❌ Email failed: {response.payload.get('error')}")
            
            loop.close()
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    thread = threading.Thread(target=send_notification_sync, daemon=True)
    thread.start()
    thread.join(timeout=10)  # Wait up to 10 seconds
    
    if result.get("sent"):
        print(f"\n📬 Check your inbox at: nguyen.andrew.quang@gmail.com")
        print(f"   Subject: Expense Request #{expense_id} - APPROVED")
    
    print("\n" + "="*70)
    print("TEST COMPLETED")
    print("="*70)


if __name__ == "__main__":
    test_manual_review()
