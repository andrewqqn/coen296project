# Email Agent Quick Start Guide

## 🚀 Quick Start

The Email Agent is now integrated and ready to use. Here's how to get started:

## 1. Verify Installation

```bash
cd backend
python -c "from services.agents import email_agent_service; print('✅ Email Agent installed')"
```

Expected output:
```
✅ Email Agent installed
```

## 2. Run Tests

```bash
# Basic tests
python test_email_agent.py

# Complete workflow test
python test_complete_email_workflow.py

# Usage examples
python examples/email_agent_examples.py
```

## 3. Basic Usage

### Send Expense Notification

```python
from services.agents.email_agent_service import email_agent
from services.agents.a2a_protocol import A2ARequest, create_a2a_message

# Create request
request = A2ARequest(
    capability_name="send_expense_notification",
    parameters={
        "to": "employee@company.com",
        "expense_id": "exp_123",
        "status": "approved",
        "amount": 125.50,
        "category": "Meals",
        "decision_reason": "R1: Receipt valid, within policy"
    }
)

# Send via A2A
message = create_a2a_message(
    sender_id="expense_agent",
    recipient_id="email_agent",
    message_type="request",
    payload=request.model_dump()
)

response = await email_agent.process_message(message, context={})
```

### Send Generic Email

```python
request = A2ARequest(
    capability_name="send_email",
    parameters={
        "to": "user@company.com",
        "subject": "Welcome to ExpenseSense",
        "body": "Welcome! Your account is ready."
    }
)
```

### Through Orchestrator (Natural Language)

```python
from services.agents.orchestrator_agent import orchestrator_agent

result = await orchestrator_agent.process_query(
    query="Send an email to john@company.com about his approved expense",
    user_id="admin_123",
    role="admin"
)
```

## 4. Automatic Notifications

Email notifications are sent automatically when expenses are reviewed:

```python
from services.agents.expense_agent_service import evaluate_and_maybe_auto_approve

# This automatically sends email notification
await evaluate_and_maybe_auto_approve(expense_id)
```

## 5. Check Agent Status

```python
from services.agents.a2a_protocol import agent_registry

# List all agents
agents = agent_registry.list_agents()
for agent in agents:
    print(f"- {agent.name} ({agent.agent_id})")

# Get email agent card
card = agent_registry.get_agent_card("email_agent")
print(f"\nEmail Agent Capabilities:")
for cap in card.capabilities:
    print(f"  - {cap.name}: {cap.description}")
```

## 6. Integration Points

### In Expense Review Workflow

The email agent is automatically called when an expense is reviewed:

```
Expense Submitted → AI Review → Decision Made → Email Sent
```

### In Orchestrator

The orchestrator can call the email agent for any email-related queries:

```
User Query → Orchestrator → Email Agent → Email Sent
```

## 7. Configuration

### Current Setup (Mock Email)

By default, emails are logged but not actually sent:

```python
# backend/infrastructure/email_client.py
def send_email(to, subject, body):
    print(f"Sending email to {to} ...")
    return {"status": "sent", "to": to}
```

### Enable Gmail (Optional)

To send real emails via Gmail:

1. Set up OAuth2 credentials
2. Configure environment variables:
   ```bash
   export GMAIL_CREDENTIALS_FILE=gmail_oauth_credentials.json
   export GMAIL_TOKEN_FILE=token.json
   ```
3. Update `_get_email_service()` in `email_agent_service.py`

## 8. Common Use Cases

### Expense Approval Notification

```python
# Automatically sent by expense agent
{
    "to": "employee@company.com",
    "expense_id": "exp_123",
    "status": "approved",
    "amount": 89.99,
    "category": "Meals",
    "decision_reason": "R1: Receipt valid, within policy limits"
}
```

### Expense Rejection Notification

```python
{
    "to": "employee@company.com",
    "expense_id": "exp_456",
    "status": "rejected",
    "amount": 250.00,
    "category": "Entertainment",
    "decision_reason": "R4: Receipt missing or unreadable"
}
```

### Manual Review Required

```python
{
    "to": "employee@company.com",
    "expense_id": "exp_789",
    "status": "admin_review",
    "amount": 550.00,
    "category": "Travel",
    "decision_reason": "R3: Amount exceeds $500, requires manual review"
}
```

### Generic Notification

```python
{
    "to": "team@company.com",
    "subject": "New Expense Policy",
    "body": "Please review the updated expense policy..."
}
```

## 9. Monitoring

### Check Email Logs

```bash
# View email agent logs
grep "email_agent" backend/logs/*.log

# View recent emails sent
grep "Sending email" backend/logs/*.log
```

### Check Audit Trail

```python
from services.audit_log_service import get_audit_logs

# Get inter-agent messages
logs = get_audit_logs(event_type="inter_agent_message")
email_logs = [l for l in logs if "email_agent" in str(l)]
```

## 10. Troubleshooting

### Email Not Sending

1. Check agent is registered:
   ```python
   from services.agents.a2a_protocol import agent_registry
   agents = agent_registry.list_agents()
   print([a.agent_id for a in agents])
   # Should include 'email_agent'
   ```

2. Check logs for errors:
   ```bash
   grep "ERROR.*email" backend/logs/*.log
   ```

3. Test direct communication:
   ```bash
   python test_email_agent.py
   ```

### A2A Communication Failing

1. Verify message format:
   ```python
   # Must include all required fields
   request = A2ARequest(
       capability_name="send_email",
       parameters={
           "to": "...",      # Required
           "subject": "...", # Required
           "body": "..."     # Required
       }
   )
   ```

2. Check response type:
   ```python
   if response.message_type == "error":
       print(f"Error: {response.payload.get('error')}")
   ```

### Orchestrator Not Calling Email Agent

1. Verify tool is registered:
   ```python
   # Check orchestrator has call_email_agent tool
   from services.agents.orchestrator_agent import orchestrator_agent
   # Tool should be in pydantic_agent.tools
   ```

2. Test with explicit query:
   ```python
   result = await orchestrator_agent.process_query(
       query="Send an email to test@example.com with subject 'Test' and body 'Hello'",
       user_id="admin",
       role="admin"
   )
   ```

## 11. Next Steps

### For Development

1. Review `backend/EMAIL_AGENT_INTEGRATION.md` for detailed docs
2. Check `backend/examples/email_agent_examples.py` for more examples
3. Explore `backend/services/agents/README.md` for architecture

### For Production

1. Set up Gmail OAuth2 credentials
2. Configure email templates
3. Set up email monitoring
4. Configure rate limiting
5. Add email delivery tracking

## 12. API Reference

### Email Agent Capabilities

| Capability | Description | Required Params |
|------------|-------------|-----------------|
| `send_expense_notification` | Send expense decision email | to, expense_id, status, amount |
| `send_email` | Send generic email | to, subject, body |
| `search_emails` | Search inbox (Gmail) | query |

### Response Format

```python
# Success
{
    "success": True,
    "sent": True,
    "message_id": "msg_123",
    "to": "recipient@example.com",
    "subject": "Email Subject"
}

# Error
{
    "success": False,
    "error": "Error message"
}
```

## 13. Support

For help:
1. Check documentation: `backend/EMAIL_AGENT_INTEGRATION.md`
2. Run tests: `python test_email_agent.py`
3. Review examples: `backend/examples/email_agent_examples.py`
4. Check logs: `grep "email_agent" backend/logs/*.log`

## 14. Summary

✅ Email Agent is installed and working
✅ Integrated with A2A protocol
✅ Automatic expense notifications enabled
✅ Orchestrator can send emails via natural language
✅ All tests passing
✅ Ready for production (with Gmail setup)

**Start using it now:**

```python
from services.agents.orchestrator_agent import orchestrator_agent

result = await orchestrator_agent.process_query(
    query="Send a welcome email to new.employee@company.com",
    user_id="admin",
    role="admin"
)
```

That's it! The Email Agent is ready to use. 🎉
