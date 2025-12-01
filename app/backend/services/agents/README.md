# ExpenseSense Multi-Agent System

## Overview

The ExpenseSense multi-agent system uses the A2A (Agent-to-Agent) protocol to coordinate specialized agents that handle different aspects of expense management.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                        │
│  (Coordinates all agents, processes natural language)        │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Expense    │    │   Document   │    │    Email     │
│    Agent     │    │    Agent     │    │    Agent     │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  AI Review   │    │ PDF Extract  │    │ Notifications│
│  Policy      │    │ OCR Vision   │    │ Gmail        │
│  Rules       │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Agents

### 1. Orchestrator Agent (`orchestrator_agent.py`)

**Purpose:** High-level coordinator that processes natural language queries and delegates to specialized agents.

**Capabilities:**
- `process_user_query` - Process natural language and coordinate agents

**Key Features:**
- Natural language understanding
- Tool-based agent coordination
- RBAC enforcement
- Context management

**Model:** GPT-4o

### 2. Expense Agent (`expense_agent_service.py`)

**Purpose:** Reviews expenses, applies policy rules, validates receipts using AI vision.

**Capabilities:**
- `review_expense` - AI-powered expense review with receipt analysis
- `apply_static_rules` - Apply static policy rules (R1-R4)

**Key Features:**
- Multi-phase review (planner → tools → judgment)
- OCR receipt validation
- Policy compliance checking
- Automatic email notifications
- Bank account updates on approval

**Model:** GPT-4o-mini

**Rules:**
- R1: Auto-approve (≤$500, first request, valid receipt)
- R2: Manual review (multiple requests same day)
- R3: Manual review (>$500)
- R4: Auto-reject (invalid/missing receipt)

### 3. Document Agent (`document_agent_service.py`)

**Purpose:** Processes PDF receipts and extracts structured information.

**Capabilities:**
- `extract_receipt_info` - Extract structured data from receipt PDFs
- `convert_pdf_to_images` - Convert PDFs to base64 images

**Key Features:**
- PDF to image conversion
- AI vision-based extraction
- Structured data output
- Error handling for corrupted files

**Model:** GPT-4o-mini

### 4. Email Agent (`email_agent_service.py`)

**Purpose:** Sends email notifications for expense decisions and system events.

**Capabilities:**
- `send_expense_notification` - Send formatted expense decision emails
- `send_email` - Send generic emails
- `search_emails` - Search inbox (requires Gmail setup)

**Key Features:**
- Professional email formatting
- Status-based templates
- Non-blocking operation
- Gmail integration ready

**Backend:** Mock (upgradeable to Gmail)

## A2A Protocol

All agents communicate using the A2A (Agent-to-Agent) protocol defined in `a2a_protocol.py`.

### Message Flow

```python
# 1. Create request
request = A2ARequest(
    capability_name="review_expense",
    parameters={"expense_id": "exp_123"},
    context={"user_id": "user_123", "role": "employee"}
)

# 2. Create A2A message
message = create_a2a_message(
    sender_id="orchestrator",
    recipient_id="expense_agent",
    message_type="request",
    payload=request.model_dump(),
    capability_name="review_expense"
)

# 3. Process message
response = await expense_agent.process_message(message, context={})

# 4. Handle response
if response.message_type == "response":
    result = response.payload.get("result")
else:
    error = response.payload.get("error")
```

### Agent Registry

All agents register themselves on import:

```python
from services.agents.a2a_protocol import agent_registry

# List all agents
agents = agent_registry.list_agents()

# Get specific agent
card = agent_registry.get_agent_card("expense_agent")
```

## Usage Examples

### 1. Direct Agent Communication

```python
from services.agents.expense_agent_service import expense_agent
from services.agents.a2a_protocol import A2ARequest, create_a2a_message

# Review an expense
request = A2ARequest(
    capability_name="review_expense",
    parameters={"expense_id": "exp_123"}
)

message = create_a2a_message(
    sender_id="system",
    recipient_id="expense_agent",
    message_type="request",
    payload=request.model_dump()
)

response = await expense_agent.process_message(message, context={})
```

### 2. Through Orchestrator (Recommended)

```python
from services.agents.orchestrator_agent import orchestrator_agent

# Natural language query
result = await orchestrator_agent.process_query(
    query="Review expense exp_123 and send notification",
    user_id="user_123",
    role="employee"
)
```

### 3. Multi-Agent Orchestrator Service

```python
from services.multi_agent_orchestrator import process_query_with_agents

# High-level API with file upload support
result = await process_query_with_agents(
    query="Create an expense from this receipt",
    employee_id="emp_123",
    role="employee",
    files=[receipt_file]
)
```

## Workflows

### Expense Submission with Receipt

```
1. User uploads receipt PDF
   ↓
2. Document Agent extracts info
   ↓
3. Orchestrator creates expense
   ↓
4. Expense Agent reviews automatically
   ↓
5. Email Agent sends notification
   ↓
6. Bank account updated (if approved)
```

### Policy Query

```
1. User asks about policy
   ↓
2. Orchestrator queries vector DB
   ↓
3. Returns policy information
```

### Employee Management (Admin)

```
1. Admin requests employee list
   ↓
2. Orchestrator checks RBAC
   ↓
3. Returns filtered results
```

## Testing

### Run All Tests

```bash
# Email agent tests
python test_email_agent.py

# Complete workflow test
python test_complete_email_workflow.py

# Examples
python examples/email_agent_examples.py
python examples/orchestrator_examples.py
```

### Test Coverage

- ✅ Agent registration
- ✅ A2A protocol communication
- ✅ Capability invocation
- ✅ Error handling
- ✅ Orchestrator coordination
- ✅ RBAC enforcement
- ✅ Audit logging

## Configuration

### Environment Variables

```bash
# OpenAI API
OPENAI_API_KEY=your_key_here

# Firebase (optional for emulator)
USE_FIRESTORE_EMULATOR=true

# Gmail (optional)
GMAIL_CREDENTIALS_FILE=gmail_oauth_credentials.json
GMAIL_TOKEN_FILE=token.json
```

### Agent Models

Configure in each agent's `__init__`:

```python
self.pydantic_agent = self.create_pydantic_agent(
    system_prompt,
    model="gpt-4o"  # or "gpt-4o-mini"
)
```

## Security

### RBAC (Role-Based Access Control)

All orchestrator tools enforce RBAC:

```python
@self.pydantic_agent.tool
@require_role("admin")
def admin_only_function(ctx: RunContext[OrchestratorContext]):
    # Only admins can call this
    pass
```

### Ownership Checks

Employees can only access their own data:

```python
# Automatic filtering
expenses = filter_by_ownership(ctx, all_expenses, owner_field="employee_id")

# Manual check
if not check_ownership(ctx, expense, owner_field="employee_id"):
    raise PermissionError()
```

### Audit Logging

All inter-agent communication is logged:

```python
log_inter_agent_message(
    from_agent="orchestrator",
    to_agent="expense_agent",
    capability="review_expense",
    parameters={"expense_id": "exp_123"},
    success=True
)
```

## Monitoring

### Agent Health

```python
from services.agents.a2a_protocol import agent_registry

# Check registered agents
agents = agent_registry.list_agents()
print(f"Active agents: {len(agents)}")

for agent in agents:
    card = agent_registry.get_agent_card(agent.agent_id)
    print(f"{card.name}: {len(card.capabilities)} capabilities")
```

### Performance Metrics

- Agent response times
- Success/failure rates
- Token usage
- Error patterns

## Extending the System

### Adding a New Agent

1. Create agent class extending `BaseAgent`:

```python
from services.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="my_agent",
            name="My Agent",
            description="Does something useful"
        )
    
    def get_agent_card(self) -> AgentCard:
        # Define capabilities
        pass
    
    async def handle_request(self, request: A2ARequest, context: Dict) -> A2AResponse:
        # Handle requests
        pass

# Register
my_agent = MyAgent()
my_agent.register()
```

2. Add to orchestrator tools:

```python
@self.pydantic_agent.tool
async def call_my_agent(ctx, capability, parameters):
    # Call your agent
    pass
```

3. Update system prompt to include new agent

4. Import in `app.py` to ensure registration

### Adding a New Capability

1. Add to agent's `get_agent_card()`:

```python
AgentCapability(
    name="new_capability",
    description="Does something new",
    input_schema={...},
    output_schema={...}
)
```

2. Handle in `handle_request()`:

```python
if capability == "new_capability":
    result = await self._new_capability(params)
    return A2AResponse(success=True, result=result)
```

## Troubleshooting

### Agent Not Found

```python
# Check if agent is registered
from services.agents.a2a_protocol import agent_registry
agents = agent_registry.list_agents()
print([a.agent_id for a in agents])
```

### A2A Communication Failing

1. Check message format matches schema
2. Verify both agents are registered
3. Check audit logs for errors
4. Test direct communication first

### Orchestrator Not Calling Agent

1. Verify tool is registered
2. Check system prompt includes agent
3. Test with explicit tool call
4. Check RBAC permissions

## Documentation

- **A2A Protocol:** `a2a_protocol.py`
- **Base Agent:** `base_agent.py`
- **Email Integration:** `EMAIL_AGENT_INTEGRATION.md`
- **Examples:** `examples/`
- **Tests:** `test_*.py`

## Future Enhancements

1. **Agent Marketplace** - Discover and install new agents
2. **Agent Versioning** - Support multiple versions
3. **Agent Monitoring Dashboard** - Real-time health monitoring
4. **Agent Composition** - Chain multiple agents
5. **Agent Learning** - Improve from feedback
6. **Agent Scheduling** - Cron-like agent execution

## Support

For issues or questions:
1. Check documentation in this directory
2. Review examples in `examples/`
3. Run tests to verify setup
4. Check audit logs for errors

## License

Part of the ExpenseSense project.
