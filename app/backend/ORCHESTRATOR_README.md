# Orchestrator Service Documentation

## Overview

The Orchestrator service uses **Pydantic AI** with **GPT-4** to provide a natural language interface for the Expense Reimbursement System. Users can interact with the system using plain English queries, and the AI agent will automatically determine which tools (functions) to call.

## Architecture

### Components

1. **Pydantic AI Agent** (`orchestrator_service.py`)
   - Powered by GPT-4
   - Configured with system prompt for expense system context
   - Equipped with 16 tools covering all CRUD operations

2. **Orchestrator Router** (`orchestrator_router.py`)
   - FastAPI endpoint at `/orchestrator`
   - Accepts POST requests with natural language queries
   - Protected by Firebase authentication

3. **Available Tools**
   - **Employee Management**: list, get, create, update, delete
   - **Expense Management**: list, get, create, update, delete
   - **Policy Management**: list, create, update, delete
   - **Audit Logs**: list, create

## API Endpoint

### POST /orchestrator/

Process a natural language query and route it to appropriate tools.

**Request:**
```json
{
  "query": "Show me all employees"
}
```

**Response:**
```json
{
  "success": true,
  "response": "Here are all the employees in the system: ...",
  "tools_used": ["list_all_employees"],
  "query": "Show me all employees",
  "error": null
}
```

**Authentication:**
- Requires Firebase ID token in `Authorization` header
- Format: `Bearer <token>`

## Example Queries

### Employee Operations
```
- "List all employees"
- "Show me employee with ID emp123"
- "Create a new employee named John Doe with email john@example.com"
- "Update employee emp456 to change their department to Engineering"
- "Delete employee emp789"
```

### Expense Operations
```
- "Show me all expenses"
- "Get expense details for exp123"
- "Create a new expense for $500 for office supplies"
- "Update expense exp456 to change amount to $600"
- "Delete expense exp789"
```

### Policy Operations
```
- "What are all the reimbursement policies?"
- "Show me the current policies"
- "Create a new policy for travel expenses"
- "Update policy pol123"
- "Delete policy pol456"
```

### Audit Operations
```
- "Show me recent audit logs"
- "List all audit logs"
- "Create an audit log for user action"
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

The key dependencies added:
- `pydantic-ai` - Core Pydantic AI framework
- `pydantic-ai-slim[openai]` - OpenAI integration

### 2. Configure Environment

## Configuration

Ensure your `.env` file has:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

The orchestrator uses GPT-4 by default. To use GPT-4-mini (cheaper), edit `orchestrator_service.py`:
```python
model = OpenAIModel('gpt-4o-mini')
```

### 3. Run the Application

```bash
cd backend
uvicorn app:app --reload
```

### 4. Test the Endpoint

Using curl:
```bash
curl -X POST "http://localhost:8000/orchestrator/" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "List all employees"}'
```

Using the FastAPI docs:
1. Navigate to `http://localhost:8000/docs`
2. Authorize with your Firebase token
3. Try the `/orchestrator/` endpoint

## How It Works

1. **User sends natural language query** to `/orchestrator/`
2. **Authentication middleware** verifies Firebase token
3. **Pydantic AI Agent** receives the query
4. **GPT-4 analyzes** the query and determines intent
5. **Agent calls appropriate tools** (can call multiple tools if needed)
6. **Tools execute** the actual service functions
7. **Agent synthesizes** the results into a natural language response
8. **Response returned** to user with metadata (tools used, success status)

## Advanced Features

### Multi-Tool Execution

The agent can call multiple tools in sequence to fulfill complex requests:

```json
{
  "query": "Show me all employees and all expenses"
}
```

The agent will call both `list_all_employees` and `list_all_expenses` and combine the results.

### Contextual Understanding

The agent understands context and variations:
- "employees" vs "staff" vs "workers"
- "expenses" vs "reimbursements" vs "costs"
- "policies" vs "rules" vs "guidelines"

### Error Handling

If a query cannot be fulfilled, the agent will explain why:
```json
{
  "success": false,
  "error": "Error description",
  "query": "original query"
}
```

## Logging

All orchestrator operations are logged with:
- User ID from Firebase token
- Query content
- Tools called
- Success/failure status

Check logs for debugging and audit trails.

## Future Enhancements

Potential improvements:
1. **Streaming responses** for real-time feedback
2. **Conversation history** for multi-turn interactions
3. **Custom result formatting** based on user preferences
4. **Rate limiting** to prevent abuse
5. **Query analytics** to improve tool descriptions

## Troubleshooting

### Common Issues

1. **"Import pydantic_ai could not be resolved"**
   - Solution: Run `pip install pydantic-ai pydantic-ai-slim[openai]`

2. **"No OPENAI_API_KEY set"**
   - Solution: Add `OPENAI_API_KEY` to your `.env` file

3. **"Invalid token" errors**
   - Solution: Ensure Firebase authentication is properly configured
   - Check if using emulator vs production settings

4. **Agent not calling tools**
   - Check tool docstrings are clear and descriptive
   - Verify the query is specific enough
   - Review agent logs for reasoning

## Cost Considerations

- Uses GPT-4 model (configurable to GPT-4-mini for lower cost)
- Each query costs based on:
  - Input tokens (query + system prompt + tool descriptions)
  - Output tokens (response + tool calls)
- Monitor usage via OpenAI dashboard
- Consider implementing caching for common queries

## Security

- All requests require Firebase authentication
- User context available in tools via `user_claims`
- Tools can be restricted based on user roles (future enhancement)
- Audit logs automatically track orchestrator usage
