# Email Agent A2A Integration

## Overview

The Email Agent has been successfully integrated into the ExpenseSense multi-agent system using the A2A (Agent-to-Agent) protocol. This agent handles all email notifications and communication within the system.

## Architecture

### Components

1. **Email Agent Service** (`backend/services/agents/email_agent_service.py`)
   - Implements the `BaseAgent` interface
   - Registers with the agent registry
   - Handles A2A protocol messages
   - Provides email capabilities

2. **Orchestrator Integration** (`backend/services/agents/orchestrator_agent.py`)
   - Added `call_email_agent` tool for orchestrator
   - Updated system prompt to include email agent
   - Automatic email notifications on expense decisions

3. **Expense Agent Integration** (`backend/services/agents/expense_agent_service.py`)
   - Automatically sends email notifications after expense review
   - Uses A2A protocol to communicate with email agent
   - Non-blocking email sending (doesn't fail expense review if email fails)

## Capabilities

The Email Agent provides three main capabilities:

### 1. send_expense_notification

Sends formatted email notifications about expense decisions.

**Input Schema:**
```json
{
  "to": "employee@example.com",
  "expense_id": "exp_123",
  "status": "approved|rejected|admin_review|pending",
  "amount": 125.50,
  "category": "Meals",
  "decision_reason": "R1: Receipt valid, within policy limits"
}
```

**Output:**
```json
{
  "sent": true,
  "message_id": "msg_123",
  "to": "employee@example.com",
  "subject": "Expense Request #exp_123 - APPROVED"
}
```

**Email Format:**
- Professional formatting with status emoji (✅ ❌ ⏳ 🔄)
- Clear expense details section
- Decision reason explanation
- Next steps based on status
- Timestamp

### 2. send_email

Sends generic emails with custom subject and body.

**Input Schema:**
```json
{
  "to": "recipient@example.com",
  "subject": "Email Subject",
  "body": "Email body content"
}
```

**Output:**
```json
{
  "sent": true,
  "message_id": "msg_123",
  "to": "recipient@example.com",
  "subject": "Email Subject"
}
```

### 3. search_emails

Searches emails in inbox (requires Gmail integration).

**Input Schema:**
```json
{
  "query": "from:user@example.com",
  "max_results": 50
}
```

**Output:**
```json
{
  "messages": [],
  "count": 0,
  "note": "Gmail integration not configured. This is a mock response."
}
```

## Usage Examples

### Direct A2A Communication

```python
from services.agents.email_agent_service import email_agent
from services.agents.a2a_protocol import A2ARequest, create_a2a_message

# Create request
request = A2ARequest(
    capability_name="send_expense_notification",
    parameters={
        "to": "employee@example.com",
        "expense_id": "exp_123",
        "status": "approved",
        "amount": 125.50,
        "category": "Meals",
        "decision_reason": "R1: Receipt valid"
    },
    context={"user_id": "system", "role": "system"}
)

# Create A2A message
message = create_a2a_message(
    sender_id="expense_agent",
    recipient_id="email_agent",
    message_type="request",
    payload=request.dict(),
    capability_name="send_expense_notification"
)

# Send message
response = await email_agent.process_message(message, context={})
```

### Through Orchestrator

```python
from services.agents.orchestrator_agent import orchestrator_agent

# Natural language query
result = await orchestrator_agent.process_query(
    query="Send an email to john@example.com about his approved expense",
    user_id="admin_123",
    role="admin"
)
```

### Automatic Notifications

The Expense Agent automatically sends email notifications when reviewing expenses:

```python
# When expense is reviewed, email is automatically sent
await evaluate_and_maybe_auto_approve(expense_id)
# → Email notification sent to employee
```

## Integration Points

### 1. Expense Review Workflow

```
Expense Submitted
    ↓
Expense Agent Reviews
    ↓
Decision Made (Approve/Reject/Manual)
    ↓
Email Agent Notified (A2A)
    ↓
Email Sent to Employee
```

### 2. Orchestrator Workflow

```
User Query
    ↓
Orchestrator Analyzes
    ↓
Calls Email Agent Tool
    ↓
A2A Message Sent
    ↓
Email Agent Processes
    ↓
Response Returned
```

## Email Backend

Currently uses a mock email service (`backend/infrastructure/email_client.py`):

```python
def send_email(to, subject, body):
    print(f"Sending email to {to} ...")
    return {"status": "sent", "to": to}
```

### Gmail Integration (Optional)

To enable real Gmail sending, the agent can use the existing Gmail client from `app/email_agent/`:

1. Configure OAuth2 credentials
2. Set environment variables:
   - `GMAIL_CREDENTIALS_FILE`
   - `GMAIL_TOKEN_FILE`
3. Update `_get_email_service()` in `email_agent_service.py`

## Testing

Run the test suite:

```bash
cd backend
python test_email_agent.py
```

**Test Coverage:**
- ✅ Agent card retrieval
- ✅ Send expense notification
- ✅ Send generic email
- ✅ Orchestrator integration
- ✅ A2A protocol communication

## Audit Logging

All email agent interactions are logged via the audit system:

```python
log_inter_agent_message(
    from_agent="orchestrator",
    to_agent="email_agent",
    capability="send_expense_notification",
    parameters={...},
    success=True
)
```

## Error Handling

The email agent follows robust error handling:

1. **Non-blocking**: Email failures don't break expense review
2. **Graceful degradation**: Falls back to mock service if Gmail unavailable
3. **Comprehensive logging**: All errors logged with stack traces
4. **A2A error responses**: Errors returned as A2A error messages

## Future Enhancements

1. **Gmail Integration**: Enable real Gmail sending
2. **Email Templates**: Rich HTML email templates
3. **Batch Notifications**: Send multiple emails efficiently
4. **Email Tracking**: Track email delivery and opens
5. **Scheduled Emails**: Queue emails for later delivery
6. **Email Preferences**: User preferences for notification types

## Agent Registry

The email agent is automatically registered on import:

```python
# In email_agent_service.py
email_agent = EmailAgent()
email_agent.register()
```

View all registered agents:

```python
from services.agents.a2a_protocol import agent_registry

agents = agent_registry.list_agents()
# Returns: [expense_agent, document_agent, orchestrator, email_agent]
```

## Configuration

No additional configuration required. The agent uses:

- Mock email service by default
- Can be upgraded to Gmail with OAuth2 setup
- Configurable via environment variables

## Security Considerations

1. **Email Validation**: Validates recipient email addresses
2. **Content Sanitization**: Sanitizes email content
3. **Rate Limiting**: Should implement rate limiting for production
4. **Authentication**: Uses A2A protocol context for authorization
5. **Audit Trail**: All emails logged in audit system

## Monitoring

Monitor email agent health:

```python
# Check agent status
card = email_agent.get_agent_card()
print(f"Agent: {card.name}, Version: {card.version}")

# Check capabilities
for cap in card.capabilities:
    print(f"  - {cap.name}")
```

## Troubleshooting

### Email not sending

1. Check logs: `grep "email_agent" backend/logs/*.log`
2. Verify agent is registered: `agent_registry.list_agents()`
3. Check email service configuration

### A2A communication failing

1. Verify message format matches schema
2. Check audit logs for inter-agent messages
3. Ensure both agents are registered

### Orchestrator not calling email agent

1. Check orchestrator system prompt includes email agent
2. Verify `call_email_agent` tool is registered
3. Test direct A2A communication first

## Summary

The Email Agent is now fully integrated into the ExpenseSense multi-agent system:

- ✅ Implements A2A protocol
- ✅ Registered with agent registry
- ✅ Integrated with orchestrator
- ✅ Automatic expense notifications
- ✅ Comprehensive testing
- ✅ Audit logging
- ✅ Error handling
- ✅ Documentation

The agent provides a clean, extensible interface for all email communication needs in the system.
