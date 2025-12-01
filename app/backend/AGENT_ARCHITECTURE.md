# Multi-Agent System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend / API Client                        │
│                    (React, Postman, curl, etc.)                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP POST /agents/query
                             │ Authorization: Bearer <token>
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      FastAPI Backend (app.py)                        │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Agent Registry (Singleton)                      │   │
│  │  - Maintains all agent cards                                 │   │
│  │  - Enables agent discovery                                   │   │
│  │  - Routes A2A messages                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │         Multi-Agent Orchestrator Service                     │   │
│  │  - Receives user queries                                     │   │
│  │  - Handles file uploads                                      │   │
│  │  - Delegates to orchestrator agent                           │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                              │                                        │
└──────────────────────────────┼────────────────────────────────────────┘
                               │
                               │
┌──────────────────────────────▼────────────────────────────────────────┐
│                      ORCHESTRATOR AGENT                                │
│                         (GPT-4o)                                       │
│                                                                        │
│  System Prompt:                                                       │
│  "You are an intelligent orchestrator. Coordinate with specialized    │
│   agents to fulfill user requests."                                   │
│                                                                        │
│  Tools:                                                               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ • call_expense_agent(capability, parameters)                  │   │
│  │ • call_document_agent(capability, parameters)                 │   │
│  │ • list_available_agents()                                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  Decision Logic:                                                      │
│  - Analyzes user query                                                │
│  - Determines which agents to call                                    │
│  - Sequences agent calls if needed                                    │
│  - Aggregates results                                                 │
│  - Formats response for user                                          │
└────────────┬───────────────────────────────────┬─────────────────────┘
             │                                   │
             │ A2A Protocol                      │ A2A Protocol
             │                                   │
┌────────────▼──────────────┐     ┌─────────────▼──────────────┐
│    EXPENSE AGENT          │     │    DOCUMENT AGENT          │
│    (GPT-4o-mini + Vision) │     │    (GPT-4o-mini + Vision)  │
│                           │     │                            │
│  Capabilities:            │     │  Capabilities:             │
│  ┌─────────────────────┐ │     │  ┌──────────────────────┐ │
│  │ review_expense      │ │     │  │ extract_receipt_info │ │
│  │ - Load expense      │ │     │  │ - Read PDF           │ │
│  │ - Download receipt  │ │     │  │ - Convert to images  │ │
│  │ - Convert PDF       │ │     │  │ - AI vision extract  │ │
│  │ - AI vision analyze │ │     │  │ - Return JSON        │ │
│  │ - Apply rules       │ │     │  └──────────────────────┘ │
│  │ - Return decision   │ │     │                            │
│  └─────────────────────┘ │     │  ┌──────────────────────┐ │
│                           │     │  │ convert_pdf_to_images│ │
│  ┌─────────────────────┐ │     │  │ - Read PDF           │ │
│  │ apply_static_rules  │ │     │  │ - Convert pages      │ │
│  │ - R1: Auto-approve  │ │     │  │ - Return base64      │ │
│  │ - R2: Frequency     │ │     │  └──────────────────────┘ │
│  │ - R3: Large amount  │ │     │                            │
│  │ - R4: Invalid doc   │ │     │  Dependencies:             │
│  └─────────────────────┘ │     │  - pdf2image               │
│                           │     │  - OpenAI API              │
│  Dependencies:            │     │  - PIL/Pillow              │
│  - expense_repo           │     │                            │
│  - vector_db_service      │     │                            │
│  - document_service       │     │                            │
│  - audit_log_service      │     │                            │
│  - pdf2image              │     │                            │
│  - OpenAI API             │     │                            │
└───────────────────────────┘     └────────────────────────────┘
```

## A2A Protocol Message Flow

### Example: "Review expense exp_123"

```
┌──────────┐                                    ┌──────────────┐
│   User   │                                    │ Orchestrator │
└────┬─────┘                                    └──────┬───────┘
     │                                                  │
     │ POST /agents/query                              │
     │ {"query": "Review expense exp_123"}             │
     ├─────────────────────────────────────────────────>
     │                                                  │
     │                                                  │ 1. Parse query
     │                                                  │ 2. Identify intent: review expense
     │                                                  │ 3. Select tool: call_expense_agent
     │                                                  │
     │                                                  │ A2AMessage
     │                                                  │ ┌─────────────────────────┐
     │                                                  │ │ sender: orchestrator    │
     │                                                  │ │ recipient: expense_agent│
     │                                                  │ │ type: request           │
     │                                                  │ │ capability: review_exp  │
     │                                                  │ │ payload: {              │
     │                                                  │ │   expense_id: "exp_123" │
     │                                                  │ │ }                       │
     │                                                  │ └─────────────────────────┘
     │                                                  │
     │                                    ┌─────────────▼──────────┐
     │                                    │    Expense Agent       │
     │                                    └─────────────┬──────────┘
     │                                                  │
     │                                                  │ 1. Load expense from DB
     │                                                  │ 2. Download receipt PDF
     │                                                  │ 3. Convert PDF to images
     │                                                  │ 4. Call OpenAI vision API
     │                                                  │ 5. Apply static rules
     │                                                  │ 6. Update expense status
     │                                                  │ 7. Create audit log
     │                                                  │
     │                                                  │ A2AMessage
     │                                                  │ ┌─────────────────────────┐
     │                                                  │ │ sender: expense_agent   │
     │                                    ┌─────────────┤ │ recipient: orchestrator │
     │                                    │             │ │ type: response          │
     │                                    │             │ │ payload: {              │
     │                                    │             │ │   decision: "APPROVE"   │
     │                                    │             │ │   rule: "R1"            │
     │                                    │             │ │   reason: "..."         │
     │                                    │             │ │   confidence: 0.95      │
     │                                    │             │ │ }                       │
     │                                    │             │ └─────────────────────────┘
     │                                    │             │
     │                                    └─────────────▼
     │                                                  │
     │                                                  │ 1. Receive response
     │                                                  │ 2. Format for user
     │                                                  │ 3. Add context
     │                                                  │
     │ Response:                                        │
     │ {                                                │
     │   "success": true,                               │
     │   "response": "Expense exp_123 has been         │
     │                approved. The receipt is valid   │
     │                and matches policy rules.",       │
     │   "agents_used": ["expense_agent"]               │
     │ }                                                │
     <─────────────────────────────────────────────────┤
     │                                                  │
```

## Agent Card Structure

Each agent advertises its capabilities through an Agent Card:

```
┌─────────────────────────────────────────────────────────────┐
│                      AGENT CARD                              │
├─────────────────────────────────────────────────────────────┤
│ agent_id: "expense_agent"                                    │
│ name: "Expense Review Agent"                                 │
│ description: "AI-powered expense review and approval"        │
│ version: "1.0.0"                                             │
│                                                              │
│ capabilities:                                                │
│   ┌──────────────────────────────────────────────────────┐ │
│   │ Capability 1: review_expense                         │ │
│   │ ─────────────────────────────────────────────────    │ │
│   │ description: "Review an expense submission"          │ │
│   │                                                       │ │
│   │ input_schema:                                        │ │
│   │   {                                                  │ │
│   │     "type": "object",                                │ │
│   │     "properties": {                                  │ │
│   │       "expense_id": {"type": "string"}              │ │
│   │     },                                               │ │
│   │     "required": ["expense_id"]                       │ │
│   │   }                                                  │ │
│   │                                                       │ │
│   │ output_schema:                                       │ │
│   │   {                                                  │ │
│   │     "type": "object",                                │ │
│   │     "properties": {                                  │ │
│   │       "decision": {"type": "string"},               │ │
│   │       "rule": {"type": "string"},                   │ │
│   │       "reason": {"type": "string"},                 │ │
│   │       "confidence": {"type": "number"}              │ │
│   │     }                                                │ │
│   │   }                                                  │ │
│   └──────────────────────────────────────────────────────┘ │
│                                                              │
│   ┌──────────────────────────────────────────────────────┐ │
│   │ Capability 2: apply_static_rules                     │ │
│   │ ─────────────────────────────────────────────────    │ │
│   │ description: "Apply policy rules R1-R4"              │ │
│   │ input_schema: {...}                                  │ │
│   │ output_schema: {...}                                 │ │
│   └──────────────────────────────────────────────────────┘ │
│                                                              │
│ metadata:                                                    │
│   {                                                          │
│     "model": "gpt-4o-mini",                                 │
│     "supports_vision": true,                                │
│     "max_amount": 500,                                      │
│     "policy_rules": ["R1", "R2", "R3", "R4"]               │
│   }                                                          │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow: Receipt Processing

```
User uploads receipt.pdf
         │
         ▼
┌────────────────────┐
│  File Upload       │
│  - Save to storage │
│  - Get file path   │
└────────┬───────────┘
         │
         │ file_path: "local://uploads/receipts/user1/abc.pdf"
         │
         ▼
┌────────────────────────────────────────────────────────┐
│  Orchestrator Agent                                     │
│  Query: "Extract info from this receipt"               │
│                                                         │
│  Decision: Call document_agent.extract_receipt_info     │
└────────┬───────────────────────────────────────────────┘
         │
         │ A2A Request
         │ {
         │   capability: "extract_receipt_info",
         │   parameters: {
         │     file_path: "local://uploads/receipts/user1/abc.pdf"
         │   }
         │ }
         │
         ▼
┌────────────────────────────────────────────────────────┐
│  Document Agent                                         │
│                                                         │
│  1. Read PDF file                                       │
│     ├─ Handle local:// URLs                            │
│     └─ Read bytes from disk                            │
│                                                         │
│  2. Convert PDF to images                               │
│     ├─ Use pdf2image library                           │
│     ├─ Convert at 100 DPI                              │
│     └─ Get first page                                  │
│                                                         │
│  3. Convert to base64 JPEG                              │
│     ├─ Save as JPEG in memory                          │
│     └─ Encode as base64 string                         │
│                                                         │
│  4. Call OpenAI Vision API                              │
│     ├─ Send image + prompt                             │
│     ├─ Request: vendor, amount, date, category         │
│     └─ Receive JSON response                           │
│                                                         │
│  5. Parse and validate                                  │
│     ├─ Parse JSON                                      │
│     ├─ Validate fields                                 │
│     └─ Return structured data                          │
└────────┬───────────────────────────────────────────────┘
         │
         │ A2A Response
         │ {
         │   success: true,
         │   result: {
         │     vendor: "Starbucks",
         │     amount: 12.45,
         │     date: "2025-01-15",
         │     category: "meals",
         │     description: "Coffee meeting"
         │   }
         │ }
         │
         ▼
┌────────────────────────────────────────────────────────┐
│  Orchestrator Agent                                     │
│                                                         │
│  Formats response for user:                             │
│  "I extracted the following information from the        │
│   receipt:                                              │
│   - Vendor: Starbucks                                   │
│   - Amount: $12.45                                      │
│   - Date: 2025-01-15                                    │
│   - Category: Meals                                     │
│   - Description: Coffee meeting                         │
│                                                         │
│   Would you like me to create an expense with this      │
│   information?"                                         │
└────────┬───────────────────────────────────────────────┘
         │
         ▼
      User
```

## Component Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    Backend Components                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  FastAPI App (app.py)                              │    │
│  │  - CORS middleware                                 │    │
│  │  - Authentication                                  │    │
│  │  - Router registration                             │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          │ includes                          │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Routers (controller/)                             │    │
│  │  - agents_router.py (NEW)                          │    │
│  │  - orchestrator_router.py (legacy)                 │    │
│  │  - expense_router.py                               │    │
│  │  - employee_router.py                              │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          │ uses                              │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Services (services/)                              │    │
│  │  - multi_agent_orchestrator.py (NEW)               │    │
│  │  - orchestrator_service.py (legacy)                │    │
│  │  - expense_service.py                              │    │
│  │  - employee_service.py                             │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          │ uses                              │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Agents (services/agents/) (NEW)                   │    │
│  │  ┌──────────────────────────────────────────────┐ │    │
│  │  │  a2a_protocol.py                             │ │    │
│  │  │  - AgentCard, A2AMessage, AgentRegistry      │ │    │
│  │  └──────────────────────────────────────────────┘ │    │
│  │  ┌──────────────────────────────────────────────┐ │    │
│  │  │  base_agent.py                               │ │    │
│  │  │  - BaseAgent abstract class                  │ │    │
│  │  └──────────────────────────────────────────────┘ │    │
│  │  ┌──────────────────────────────────────────────┐ │    │
│  │  │  orchestrator_agent.py                       │ │    │
│  │  │  - OrchestratorAgent                         │ │    │
│  │  └──────────────────────────────────────────────┘ │    │
│  │  ┌──────────────────────────────────────────────┐ │    │
│  │  │  expense_agent_service.py                    │ │    │
│  │  │  - ExpenseAgent                              │ │    │
│  │  └──────────────────────────────────────────────┘ │    │
│  │  ┌──────────────────────────────────────────────┐ │    │
│  │  │  document_agent_service.py                   │ │    │
│  │  │  - DocumentAgent                             │ │    │
│  │  └──────────────────────────────────────────────┘ │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          │ uses                              │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Domain Layer (domain/)                            │    │
│  │  - repositories/                                   │    │
│  │  - models/                                         │    │
│  │  - schemas/                                        │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          │ uses                              │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Infrastructure (infrastructure/)                  │    │
│  │  - firebase_client.py                              │    │
│  │  - chroma_client.py                                │    │
│  │  - llm_client.py                                   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Why A2A Protocol?

- **Standardization**: Consistent communication pattern across all agents
- **Discoverability**: Agent cards make capabilities explicit
- **Flexibility**: Easy to add/remove agents without breaking system
- **Testability**: Agents can be tested independently with mock messages

### 2. Why Pydantic AI?

- **Type Safety**: Pydantic models ensure data validation
- **Tool Calling**: Built-in support for function calling
- **Async Support**: Native async/await for better performance
- **Integration**: Works seamlessly with OpenAI API

### 3. Why Separate Agents?

- **Single Responsibility**: Each agent has one clear purpose
- **Scalability**: Can scale agents independently
- **Maintainability**: Easier to update/debug individual agents
- **Reusability**: Agents can be used by multiple orchestrators

### 4. Why Keep Legacy Orchestrator?

- **Backward Compatibility**: Existing integrations continue to work
- **Gradual Migration**: Can migrate endpoints one at a time
- **Comparison**: Can compare old vs new approaches
- **Fallback**: If multi-agent has issues, legacy still works
