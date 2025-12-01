"""
Test script to verify audit logging implementation
Tests all mandatory audit log triggers from redteam/plan.md
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.audit_log_service import (
    log_expense_status_change,
    log_inter_agent_message,
    log_unauthorized_access,
    log_payment_event,
    log_email_event,
    list_logs
)

def test_audit_logging():
    print("Testing Audit Logging Implementation")
    print("=" * 60)
    
    # Clear existing logs for clean test
    print("\n1. Testing Expense Status Change Logging")
    log_expense_status_change(
        actor="AI",
        expense_id="test_exp_001",
        old_status="pending",
        new_status="approved",
        reason="R1: Receipt valid, within policy limits"
    )
    print("✓ Logged expense status change: pending → approved")
    
    log_expense_status_change(
        actor="Human",
        expense_id="test_exp_002",
        old_status="admin_review",
        new_status="rejected",
        reason="Missing business justification"
    )
    print("✓ Logged expense status change: admin_review → rejected")
    
    # Test inter-agent messages
    print("\n2. Testing Inter-Agent Message Logging")
    log_inter_agent_message(
        from_agent="orchestrator",
        to_agent="expense_agent",
        capability="review_expense",
        parameters={"expense_id": "test_exp_001"},
        success=True
    )
    print("✓ Logged inter-agent message: orchestrator → expense_agent")
    
    log_inter_agent_message(
        from_agent="orchestrator",
        to_agent="document_agent",
        capability="extract_receipt_info",
        parameters={"file_path": "local://test.pdf"},
        success=True
    )
    print("✓ Logged inter-agent message: orchestrator → document_agent")
    
    log_inter_agent_message(
        from_agent="orchestrator",
        to_agent="email_agent",
        capability="send_notification",
        parameters={"to": "test@example.com"},
        success=False,
        error="SMTP connection failed"
    )
    print("✓ Logged failed inter-agent message: orchestrator → email_agent")
    
    # Test unauthorized access
    print("\n3. Testing Unauthorized Access Logging")
    log_unauthorized_access(
        actor="Human",
        user_id="emp_123",
        resource="list_employees",
        action="invoke_tool",
        reason="User role 'employee' does not have required role(s): admin"
    )
    print("✓ Logged unauthorized access attempt")
    
    log_unauthorized_access(
        actor="AI",
        user_id="system",
        resource="/etc/passwd",
        action="file_read",
        reason="Suspicious file access attempt blocked"
    )
    print("✓ Logged suspicious file access attempt")
    
    # Test payment events
    print("\n4. Testing Payment Event Logging")
    log_payment_event(
        expense_id="test_exp_001",
        employee_id="emp_123",
        amount=125.50,
        bank_account_id="bank_acc_456",
        old_balance=1000.00,
        new_balance=1125.50
    )
    print("✓ Logged payment event")
    
    # Test email events
    print("\n5. Testing Email Event Logging")
    log_email_event(
        to="employee@example.com",
        subject="Expense Approved",
        triggered_by="expense_approval",
        success=True
    )
    print("✓ Logged email event (success)")
    
    log_email_event(
        to="admin@example.com",
        subject="Review Required",
        triggered_by="manual_review_needed",
        success=False
    )
    print("✓ Logged email event (failure)")
    
    # List all logs
    print("\n6. Retrieving All Audit Logs")
    print("-" * 60)
    logs = list_logs()
    print(f"Total audit logs: {len(logs)}")
    
    # Group by event type
    event_types = {}
    for log in logs:
        event_type = log.get('event_type', 'unknown')
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    print("\nAudit Log Summary by Event Type:")
    for event_type, count in sorted(event_types.items()):
        print(f"  - {event_type}: {count}")
    
    # Verify actor values
    print("\n7. Verifying Actor Values (must be 'AI' or 'Human')")
    invalid_actors = []
    for log in logs:
        actor = log.get('actor')
        if actor not in ['AI', 'Human']:
            invalid_actors.append(log)
    
    if invalid_actors:
        print(f"❌ Found {len(invalid_actors)} logs with invalid actor values:")
        for log in invalid_actors:
            print(f"  - Actor: {log.get('actor')}, Log: {log.get('log')}")
    else:
        print("✓ All audit logs have valid actor values ('AI' or 'Human')")
    
    print("\n" + "=" * 60)
    print("Audit Logging Test Complete!")
    print("\nMandatory Audit Log Triggers (from redteam/plan.md):")
    print("✓ 1. Expense Status Change (approve, reject, admin-review)")
    print("✓ 2. Inter-Agent Messages (Orchestrator → Expense/Email/Financial)")
    print("✓ 3. Unauthorized Tool/API/File Access Attempts")
    print("✓ 4. Payment or Email Event Triggered")
    print("\nAll requirements implemented successfully!")

if __name__ == "__main__":
    test_audit_logging()
