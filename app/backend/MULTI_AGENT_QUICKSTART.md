# Multi-Agent System Quick Start Guide

This guide will help you get started with the multi-agent system in ExpenseSense.

## What Changed?

The backend has been transformed from a monolithic orchestrator into a **multi-agent system** using:
- **Pydantic AI**: For agent implementation and tool calling
- **Google's A2A Protocol**: For agent-to-agent communication
- **Agent Cards**: For capability advertisement and discovery

## Architecture

```
User Request
     ↓
Orchestrator Agent (GPT-4o)
     ↓
  ┌──┴──┐
  ↓     ↓
Expense  Document
Agent    Agent
(GPT-4o-mini)
```

## Quick Test

### 1. Start the Backend

```bash
cd backend
python app.py
```

You should see:
```
✓ Multi-agent system initialized with 3 agents:
  - Orchestrator Agent (orchestrator): 1 capabilities
  - Expense Review Agent (expense_agent): 2 capabilities
  - Document Processing Agent (document_agent): 2 capabilities
```

### 2. Test Agent Registry

```bash
curl -X GET http://localhost:8000/agents/registry \
  -H "Authorization: Bearer test-token" | jq
```

This returns all registered agents and their capabilities.

### 3. Test a Query

```bash
curl -X POST http://localhost:8000/agents/query \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What agents are available?"
  }' | jq
```

### 4. Run Test Suite

```bash
cd backend
python test_multi_agent.py
```

This runs a comprehensive test of all agents and the A2A protocol.

## API Endpoints

### New Multi-Agent Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents/registry` | GET | List all agents and capabilities |
| `/agents/registry/{agent_id}` | GET | Get specific agent card |
| `/agents/query` | POST | Process query with multi-agent system |
| `/agents/query-with-files` | POST | Process query with file uploads |

### Legacy Endpoints (Still Work)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/orchestrator` | POST | Original orchestrator (uses old system) |
| `/expenses` | GET/POST | Direct expense CRUD |
| `/employees` | GET/POST | Direct employee CRUD |

## Example Queries

### 1. List Available Agents

```json
{
  "query": "What agents are available in the system?"
}
```

Response:
```json
{
  "success": true,
  "response": "The system has 2 specialized agents:\n1. Expense Review Agent - Reviews expenses and applies policy rules\n2. Document Processing Agent - Processes PDF receipts and extracts information",
  "agents_used": [],
  "query": "What agents are available in the system?"
}
```

### 2. Review an Expense

```json
{
  "query": "Review expense exp_abc123"
}
```

The orchestrator will:
1. Call `expense_agent.review_expense(expense_id="exp_abc123")`
2. Expense agent will analyze the receipt and apply rules
3. Return the decision (APPROVE/REJECT/MANUAL)

### 3. Process a Receipt

```bash
curl -X POST http://localhost:8000/agents/query-with-files \
  -H "Authorization: Bearer test-token" \
  -F "query=Extract information from this receipt" \
  -F "files=@receipt.pdf"
```

The orchestrator will:
1. Upload the PDF
2. Call `document_agent.extract_receipt_info(file_path="...")`
3. Return extracted vendor, amount, date, category

## Agent Capabilities

### Orchestrator Agent
- **ID**: `orchestrator`
- **Model**: GPT-4o
- **Capabilities**:
  - `process_user_query`: Understand intent and coordinate agents

### Expense Agent
- **ID**: `expense_agent`
- **Model**: GPT-4o-mini (with vision)
- **Capabilities**:
  - `review_expense`: AI-powered expense review
  - `apply_static_rules`: Apply policy rules (R1-R4)

### Document Agent
- **ID**: `document_agent`
- **Model**: GPT-4o-mini (with vision)
- **Capabilities**:
  - `extract_receipt_info`: Extract structured data from PDFs
  - `convert_pdf_to_images`: Convert PDF to base64 images

## How It Works

### A2A Protocol Flow

1. **User sends query** → Orchestrator Agent
2. **Orchestrator analyzes** query and determines which agents to call
3. **Orchestrator creates A2A message**:
   ```python
   A2AMessage(
       sender_agent_id="orchestrator",
       recipient_agent_id="expense_agent",
       message_type="request",
       capability_name="review_expense",
       payload={...}
   )
   ```
4. **Target agent processes** the message
5. **Target agent returns** A2A response message
6. **Orchestrator aggregates** results and responds to user

### Agent Card Example

```python
AgentCard(
    agent_id="expense_agent",
    name="Expense Review Agent",
    description="AI-powered expense review",
    capabilities=[
        AgentCapability(
            name="review_expense",
            description="Review an expense submission",
            input_schema={
                "type": "object",
                "properties": {
                    "expense_id": {"type": "string"}
                },
                "required": ["expense_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "decision": {"type": "string"},
                    "reason": {"type": "string"}
                }
            }
        )
    ]
)
```

## Adding a New Agent

To add a new agent (e.g., Email Agent):

### 1. Create the Agent Class

```python
# backend/services/agents/email_agent_service.py
from services.agents.base_agent import BaseAgent
from services.agents.a2a_protocol import AgentCard, AgentCapability, A2ARequest, A2AResponse

class EmailAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="email_agent",
            name="Email Agent",
            description="Sends email notifications"
        )
    
    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            agent_id=self.agent_id,
            name=self.name,
            description=self.description,
            capabilities=[
                AgentCapability(
                    name="send_notification",
                    description="Send email notification",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "to": {"type": "string"},
                            "subject": {"type": "string"},
                            "body": {"type": "string"}
                        },
                        "required": ["to", "subject", "body"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "sent": {"type": "boolean"},
                            "message_id": {"type": "string"}
                        }
                    }
                )
            ]
        )
    
    async def handle_request(self, request: A2ARequest, context: dict) -> A2AResponse:
        if request.capability_name == "send_notification":
            # Send email logic here
            return A2AResponse(
                success=True,
                result={"sent": True, "message_id": "msg_123"}
            )
        
        return A2AResponse(success=False, error="Unknown capability")

# Register the agent
email_agent = EmailAgent()
email_agent.register()
```

### 2. Add Tool to Orchestrator

```python
# In orchestrator_agent.py, add a new tool:

@self.pydantic_agent.tool
async def call_email_agent(
    ctx: RunContext[OrchestratorContext],
    capability: str,
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Call the Email Agent to send notifications."""
    from services.agents.email_agent_service import email_agent
    
    request = A2ARequest(
        capability_name=capability,
        parameters=parameters,
        context={"user_id": ctx.deps.user_id}
    )
    
    message = create_a2a_message(
        sender_id=self.agent_id,
        recipient_id="email_agent",
        message_type="request",
        payload=request.dict(),
        capability_name=capability
    )
    
    response_message = await email_agent.process_message(message, context={})
    return response_message.payload.get("result", {})
```

### 3. Import in __init__.py

```python
# backend/services/agents/__init__.py
from .email_agent_service import EmailAgent, email_agent

__all__ = [..., "EmailAgent", "email_agent"]
```

### 4. Test It

```bash
curl -X POST http://localhost:8000/agents/query \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Send an email to user@example.com about expense approval"
  }'
```

## Benefits

1. **Modularity**: Each agent is independent and focused
2. **Scalability**: Easy to add new agents without changing existing code
3. **Discoverability**: Agent cards make capabilities explicit
4. **Testability**: Agents can be tested in isolation
5. **Flexibility**: Orchestrator dynamically routes to appropriate agents
6. **Standardization**: A2A protocol provides consistent communication

## Troubleshooting

### Agents Not Registered

If you see "0 agents registered", check:
1. Import statements in `app.py`
2. Agent `register()` calls are executed
3. No import errors in agent files

### Agent Not Found

If orchestrator can't find an agent:
1. Check agent is registered: `agent_registry.list_agents()`
2. Verify agent_id matches in tool calls
3. Check imports in orchestrator_agent.py

### Tool Not Called

If orchestrator doesn't call the right tool:
1. Check tool description is clear
2. Verify system prompt guides the model
3. Test with more explicit queries

## Next Steps

1. Read [MULTI_AGENT_SYSTEM.md](./MULTI_AGENT_SYSTEM.md) for detailed architecture
2. Run `python test_multi_agent.py` to verify setup
3. Try the API endpoints with Postman or curl
4. Add your own custom agents!

## Support

For questions or issues:
1. Check the logs in `backend/logs/app.log`
2. Review agent registration output on startup
3. Test individual agents with `test_multi_agent.py`
