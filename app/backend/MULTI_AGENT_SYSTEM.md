# Multi-Agent System with A2A Protocol

This document describes the multi-agent architecture implemented in the ExpenseSense backend using Pydantic AI and Google's Agent-to-Agent (A2A) protocol.

## Architecture Overview

The system consists of three main agents that communicate using the A2A protocol:

```
┌─────────────────────────────────────────────────────────────┐
│                     Orchestrator Agent                       │
│  (Coordinates between specialized agents)                    │
│  - Understands user intent                                   │
│  - Routes requests to appropriate agents                     │
│  - Aggregates results                                        │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
             │ A2A Protocol                   │ A2A Protocol
             │                                │
    ┌────────▼────────┐              ┌───────▼────────┐
    │ Expense Agent   │              │ Document Agent │
    │                 │              │                │
    │ - Review        │              │ - Extract info │
    │   expenses      │              │   from PDFs    │
    │ - Apply policy  │              │ - Convert PDFs │
    │   rules         │              │   to images    │
    │ - Validate      │              │ - OCR text     │
    │   receipts      │              │                │
    └─────────────────┘              └────────────────┘
```

## A2A Protocol

The Agent-to-Agent (A2A) protocol is based on Google's specification for agent communication. It provides:

### 1. Agent Cards

Each agent advertises its capabilities through an "Agent Card" (similar to OpenAPI specs):

```python
AgentCard(
    agent_id="expense_agent",
    name="Expense Review Agent",
    description="AI-powered expense review and approval",
    capabilities=[
        AgentCapability(
            name="review_expense",
            description="Review an expense with AI",
            input_schema={...},
            output_schema={...}
        )
    ]
)
```

### 2. A2A Messages

Agents communicate using structured messages:

```python
A2AMessage(
    sender_agent_id="orchestrator",
    recipient_agent_id="expense_agent",
    message_type="request",
    capability_name="review_expense",
    payload={
        "capability_name": "review_expense",
        "parameters": {"expense_id": "exp_123"}
    }
)
```

### 3. Agent Registry

A central registry maintains all agent cards and enables discovery:

```python
# Register an agent
agent_registry.register_agent(agent_card)

# Find agents by capability
agents = agent_registry.find_agents_by_capability("review_expense")

# List all agents
all_agents = agent_registry.list_agents()
```

## Agents

### 1. Orchestrator Agent

**Agent ID:** `orchestrator`  
**Model:** GPT-4o  
**Purpose:** High-level coordinator that understands user intent and delegates to specialized agents

**Capabilities:**
- `process_user_query`: Process natural language queries and coordinate with other agents

**Tools:**
- `call_expense_agent`: Invoke expense agent capabilities
- `call_document_agent`: Invoke document agent capabilities
- `list_available_agents`: Discover available agents

### 2. Expense Agent

**Agent ID:** `expense_agent`  
**Model:** GPT-4o-mini (with vision)  
**Purpose:** AI-powered expense review and policy validation

**Capabilities:**
- `review_expense`: Review an expense submission with receipt analysis
  - Validates receipts using AI vision
  - Applies policy rules (R1-R4)
  - Returns APPROVE/REJECT/MANUAL decision
  
- `apply_static_rules`: Apply static policy rules
  - R1: Auto-approve (≤$500, first request)
  - R2: Frequency violation
  - R3: Large amount (>$500)
  - R4: Invalid documentation

**Features:**
- OCR receipt validation
- Policy rule enforcement
- Confidence scoring
- Merchant/date/amount extraction

### 3. Document Agent

**Agent ID:** `document_agent`  
**Model:** GPT-4o-mini (with vision)  
**Purpose:** Document processing and information extraction

**Capabilities:**
- `extract_receipt_info`: Extract structured data from receipt PDFs
  - Vendor name
  - Amount
  - Date
  - Category
  - Description
  
- `convert_pdf_to_images`: Convert PDF pages to base64 JPEG images

**Features:**
- PDF to image conversion
- AI vision-based extraction
- Structured JSON output
- Multi-page support

## API Endpoints

### List All Agents

```http
GET /agents/registry
Authorization: Bearer <firebase-token>
```

Returns all registered agents and their capabilities.

### Get Agent Card

```http
GET /agents/registry/{agent_id}
Authorization: Bearer <firebase-token>
```

Returns the capability card for a specific agent.

### Process Query

```http
POST /agents/query
Authorization: Bearer <firebase-token>
Content-Type: application/json

{
  "query": "Review expense exp_123",
  "message_history": [...]
}
```

Process a natural language query using the multi-agent system.

### Process Query with Files

```http
POST /agents/query-with-files
Authorization: Bearer <firebase-token>
Content-Type: multipart/form-data

query: "Extract information from this receipt"
files: [receipt.pdf]
```

Process a query with file uploads (e.g., PDF receipts).

## Usage Examples

### Example 1: Review an Expense

```python
# User query
"Review expense exp_123"

# Flow:
1. Orchestrator receives query
2. Orchestrator calls expense_agent.review_expense(expense_id="exp_123")
3. Expense agent:
   - Loads expense data
   - Downloads receipt
   - Converts PDF to images
   - Analyzes with AI vision
   - Applies policy rules
   - Returns decision
4. Orchestrator returns formatted response to user
```

### Example 2: Process Receipt and Create Expense

```python
# User query with file upload
"Extract information from this receipt and create an expense"

# Flow:
1. System uploads receipt PDF to storage
2. Orchestrator receives query with file path
3. Orchestrator calls document_agent.extract_receipt_info(file_path="...")
4. Document agent:
   - Reads PDF
   - Converts to images
   - Extracts structured data (vendor, amount, date, etc.)
   - Returns JSON
5. Orchestrator uses extracted data to create expense
6. Orchestrator calls expense_agent.review_expense(expense_id="...")
7. Returns complete result to user
```

### Example 3: List Available Agents

```python
# User query
"What agents are available?"

# Flow:
1. Orchestrator calls list_available_agents tool
2. Returns list of all registered agents with capabilities
```

## Implementation Details

### Base Agent Class

All agents inherit from `BaseAgent`:

```python
class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str, description: str)
    
    @abstractmethod
    def get_agent_card(self) -> AgentCard
    
    @abstractmethod
    async def handle_request(self, request: A2ARequest, context: Dict) -> A2AResponse
    
    async def process_message(self, message: A2AMessage, context: Dict) -> A2AMessage
    
    def register(self)
```

### Creating a New Agent

To add a new agent:

1. Create a class that inherits from `BaseAgent`
2. Implement `get_agent_card()` to define capabilities
3. Implement `handle_request()` to handle incoming requests
4. Register the agent: `agent.register()`
5. Add tools to orchestrator to call the new agent

Example:

```python
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
                    name="send_email",
                    description="Send an email",
                    input_schema={...},
                    output_schema={...}
                )
            ]
        )
    
    async def handle_request(self, request: A2ARequest, context: Dict) -> A2AResponse:
        if request.capability_name == "send_email":
            # Send email logic
            return A2AResponse(success=True, result={...})

# Register
email_agent = EmailAgent()
email_agent.register()
```

## Benefits

1. **Modularity**: Each agent is self-contained and focused on specific tasks
2. **Discoverability**: Agent cards make capabilities explicit and discoverable
3. **Scalability**: Easy to add new agents without modifying existing ones
4. **Testability**: Agents can be tested independently
5. **Flexibility**: Orchestrator can dynamically route to appropriate agents
6. **Standardization**: A2A protocol provides consistent communication pattern

## Testing

Test the multi-agent system:

```bash
# Start the backend
cd backend
python app.py

# Test agent registry
curl -X GET http://localhost:8000/agents/registry \
  -H "Authorization: Bearer test-token"

# Test query processing
curl -X POST http://localhost:8000/agents/query \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{"query": "Review expense exp_123"}'
```

## Future Enhancements

1. **Email Agent**: Send notifications for expense approvals/rejections
2. **Analytics Agent**: Generate reports and insights
3. **Policy Agent**: Manage and update reimbursement policies
4. **Approval Agent**: Handle multi-level approval workflows
5. **Integration Agent**: Connect with external systems (accounting, HR, etc.)
