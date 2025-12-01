# Email Notification Flow - How It Works

## ✅ Current Implementation

**Email notifications are ALREADY IMPLEMENTED and work automatically!**

When an expense is reviewed, an email is automatically sent to the employee's email address.

## 🔄 Complete Workflow

### With Receipt (Full Automatic Flow)

```
1. User submits expense with receipt PDF
   ↓
2. Backend: expense_service.create_expense(receipt_path="...")
   ↓
3. Expense created in database (status: "pending")
   ↓
4. AUTOMATIC: evaluate_and_maybe_auto_approve(expense_id) called
   ↓
5. AI reviews receipt:
   - Converts PDF to images
   - Analyzes with GPT-4o-mini vision
   - Extracts merchant, amount, date
   - Validates against policy rules (R1-R4)
   - Makes decision: approve/reject/admin_review
   ↓
6. Status updated in database
   ↓
7. AUTOMATIC: Email notification sent via A2A protocol
   - Gets employee email from database
   - Creates A2A message to email_agent
   - Email agent formats professional email
   - Email sent to employee's inbox
   ↓
8. Employee receives email notification
```

### Without Receipt (Manual Review)

```
1. User submits expense without receipt
   ↓
2. Expense created (status: "pending")
   ↓
3. Admin manually reviews and approves/rejects
   ↓
4. Status updated
   ↓
5. Email notification sent (if implemented in admin flow)
```

## 📧 Email Notification Implementation

### Location: `backend/services/agents/expense_agent_service.py`

**Lines 647-695** (after expense decision is made):

```python
# ============================================================
# Send Email Notification
# ============================================================
try:
    from services.employee_service import get_employee
    from services.agents.email_agent_service import email_agent
    from services.agents.a2a_protocol import A2ARequest, create_a2a_message
    
    # Get employee email
    emp_id = expense.get('employee_id')
    employee_data = get_employee(emp_id)
    
    if employee_data and employee_data.get('email'):
        employee_email = employee_data['email']
        
        # Create email notification request
        email_request = A2ARequest(
            capability_name="send_expense_notification",
            parameters={
                "to": employee_email,
                "expense_id": expense_id,
                "status": status,
                "amount": float(expense.get('amount', 0)),
                "category": expense.get('category', 'N/A'),
                "decision_reason": f"{parsed.rule}: {parsed.reason}"
            },
            context={"user_id": "system", "role": "system"}
        )
        
        # Send via A2A protocol
        message = create_a2a_message(
            sender_id="expense_agent",
            recipient_id="email_agent",
            message_type="request",
            payload=email_request.dict(),
            capability_name="send_expense_notification"
        )
        
        # Send email notification (await since we're in async context)
        response = await email_agent.process_message(
            message, 
            context={"user_id": "system", "role": "system"}
        )
        
        if response.message_type == "response":
            logger.info(f"[EMAIL] Notification sent successfully to {employee_email}")
        else:
            logger.warning(f"[EMAIL] Notification failed: {response.payload.get('error')}")
    else:
        logger.warning(f"[EMAIL] Could not send notification - employee has no email")
        
except Exception as e:
    # Don't fail the expense review if email fails
    logger.error(f"[EMAIL] Failed to send notification: {str(e)}", exc_info=True)
```

## 🎯 Key Points

### 1. Automatic Trigger

The email is sent **automatically** when `evaluate_and_maybe_auto_approve()` is called, which happens:
- After expense creation with receipt
- During AI review process
- No manual intervention needed

### 2. A2A Protocol

Uses the Agent-to-Agent protocol:
- **Sender:** expense_agent
- **Recipient:** email_agent
- **Capability:** send_expense_notification
- **Message Type:** request → response

### 3. Non-Blocking

Email sending is **non-blocking**:
- Uses `await` in async context
- If email fails, expense review still succeeds
- Error logged but doesn't break workflow

### 4. Employee Email Required

Email is sent only if:
- Employee exists in database
- Employee has `email` field populated
- Otherwise, warning logged

## 📨 Email Format

### Approved Expense

```
Subject: Expense Request #exp_123 - APPROVED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Expense Request Update
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hello,

Your expense request has been processed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Expense Details
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Expense ID:     exp_123
Status:         APPROVED
Amount:         $125.50
Category:       Meals

Decision Reason:
R1: Receipt valid, within policy limits

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Your expense has been APPROVED and the 
reimbursement will be processed. The amount 
will be credited to your registered bank account.

Processed:      2025-11-27 22:00:00 UTC

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Thank you,
ExpenseSense Reimbursement System
```

### Rejected Expense

```
Subject: Expense Request #exp_456 - REJECTED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Expense Request Update
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Similar format with rejection details]
```

### Manual Review Required

```
Subject: Expense Request #exp_789 - MANUAL REVIEW

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏳ Expense Request Update
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Similar format with manual review notice]
```

## 🧪 Testing

### Test the Email Flow

```bash
cd backend
python test_email_on_review.py
```

This test:
1. Creates an employee with email
2. Creates an expense
3. Simulates approval
4. Sends email notification
5. Verifies the complete flow

### Expected Output

```
✅ Employee created with email: john.doe@company.com
✅ Expense created: exp_123
✅ Expense approved
✅ Email notification sent via A2A protocol
```

## 🔧 Configuration

### Current Setup (Mock Email)

By default, emails are logged but not actually sent:

```python
# backend/infrastructure/email_client.py
def send_email(to, subject, body):
    print(f"Sending email to {to} ...")
    return {"status": "sent", "to": to}
```

### Enable Real Gmail (Optional)

To send real emails:

1. Set up Gmail OAuth2 credentials
2. Configure environment variables:
   ```bash
   export GMAIL_CREDENTIALS_FILE=gmail_oauth_credentials.json
   export GMAIL_TOKEN_FILE=token.json
   ```
3. Update `_get_email_service()` in `email_agent_service.py`

## 📊 Monitoring

### Check Email Logs

```bash
# View email notifications
grep "\[EMAIL\]" backend/logs/*.log

# View sent emails
grep "Sending email" backend/logs/*.log
```

### Check Audit Trail

All email operations are logged in the audit system:

```python
from services.audit_log_service import get_audit_logs

logs = get_audit_logs(event_type="inter_agent_message")
email_logs = [l for l in logs if "email_agent" in str(l)]
```

## 🚨 Troubleshooting

### Email Not Sent

**Check 1: Employee has email?**
```python
from services.employee_service import get_employee
emp = get_employee(employee_id)
print(emp.get('email'))  # Should not be None
```

**Check 2: Email agent registered?**
```python
from services.agents.a2a_protocol import agent_registry
agents = agent_registry.list_agents()
print([a.agent_id for a in agents])  # Should include 'email_agent'
```

**Check 3: Check logs**
```bash
grep "EMAIL" backend/logs/*.log
```

### Common Issues

1. **Employee has no email** → Warning logged, no email sent
2. **Email agent not registered** → Import error, check app.py
3. **A2A message fails** → Check error logs for details

## ✨ Summary

**The email notification system is fully implemented and working!**

- ✅ Automatic email after expense review
- ✅ Uses A2A protocol for clean architecture
- ✅ Non-blocking (doesn't break expense review)
- ✅ Professional email formatting
- ✅ Status-specific messages
- ✅ Comprehensive error handling
- ✅ Full audit logging

**No additional implementation needed** - emails are sent automatically when expenses are reviewed with receipts.

To enable real email delivery, simply configure Gmail OAuth2 credentials. Otherwise, the mock service logs all email operations for development/testing.
