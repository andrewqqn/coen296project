# Quick Start Guide - Orchestrator Endpoint

## What was set up?

✅ **Pydantic AI Integration** - AI-powered natural language query processing
✅ **GPT-4 Integration** - Using OpenAI's GPT-4 for intelligent tool selection  
✅ **New `/orchestrator` Endpoint** - Natural language API interface
✅ **16 AI Tools** - All CRUD operations exposed as AI-callable functions
✅ **Complete Documentation** - See ORCHESTRATOR_README.md for details

## Files Created/Modified

### New Files:
- `backend/domain/services/orchestrator_service.py` - Pydantic AI agent with tools
- `backend/application/orchestrator_router.py` - FastAPI endpoint
- `backend/test/test_orchestrator.py` - Test script
- `backend/ORCHESTRATOR_README.md` - Full documentation
- `backend/ORCHESTRATOR_QUICKSTART.md` - This file

### Modified Files:
- `backend/requirements.txt` - Added pydantic-ai dependencies
- `backend/app.py` - Registered orchestrator router
- `backend/application/__init__.py` - Exported orchestrator router

## Quick Test

### 1. Start the backend server:
```bash
cd backend
uvicorn app:app --reload
```

### 2. Make a test request:

Using curl:
```bash
curl -X POST "http://localhost:8000/orchestrator/" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "List all employees"}'
```

Using Python test script:
```bash
# Edit test/test_orchestrator.py with your Firebase token first
python test/test_orchestrator.py
```

Using FastAPI Swagger UI:
1. Open http://localhost:8000/docs
2. Click "Authorize" and enter your Firebase token
3. Find `/orchestrator/` endpoint
4. Click "Try it out"
5. Enter a query like: `"List all employees"`
6. Click "Execute"

### 3. Example Queries to Try:

**Employee queries:**
- "Show me all employees"
- "Get employee with ID emp123"
- "Create a new employee named John Doe"

**Expense queries:**
- "List all expenses"
- "Show me expense exp456"
- "What expenses do we have?"

**Policy queries:**
- "What are our reimbursement policies?"
- "Show me all policies"

**Audit queries:**
- "Show me recent audit logs"
- "List all system activity"

**Complex queries:**
- "Show me all employees and their expenses"
- "What's the total of all expenses?"

## Architecture

```
User Query
    ↓
/orchestrator/ endpoint (FastAPI)
    ↓
orchestrator_service.py (Pydantic AI Agent)
    ↓
GPT-4 analyzes query → Selects tools
    ↓
Tools call domain services
    ↓
Results returned to AI
    ↓
AI formats natural language response
    ↓
Response sent to user
```

## Environment Setup

Make sure your `.env` file has:
```env
OPENAI_API_KEY=sk-your-openai-key-here
USE_FIRESTORE_EMULATOR=true  # or false for production
FIREBASE_PROJECT_ID=your-project-id
```

## Available Tools (AI Functions)

The AI agent has access to:

**Employee Tools:**
- list_all_employees
- get_employee_by_id
- create_new_employee
- update_existing_employee
- delete_existing_employee

**Expense Tools:**
- list_all_expenses
- get_expense_by_id
- create_new_expense
- update_existing_expense
- delete_existing_expense

**Policy Tools:**
- list_all_policies
- create_new_policy
- update_existing_policy
- delete_existing_policy

**Audit Tools:**
- list_all_audit_logs
- create_audit_log

## How It Works

1. **You send a natural language query** (in plain English)
2. **GPT-4 understands your intent** and decides which tools to use
3. **Tools are called automatically** to fetch/modify data
4. **AI synthesizes the response** in natural language
5. **You get a human-readable answer** with metadata

## Benefits

✨ **Natural Language Interface** - No need to learn API endpoints
🤖 **Intelligent Routing** - AI picks the right tools automatically
🔧 **Multi-Tool Execution** - Can call multiple functions for complex queries
📊 **Rich Responses** - Natural language explanations of data
🔍 **Transparent** - See which tools were used in the response

## Next Steps

1. Test with various queries
2. Check logs to see tool execution
3. Modify system prompt in `orchestrator_service.py` to customize behavior
4. Add more tools as you expand the service layer
5. Consider adding conversation history for multi-turn interactions

## Troubleshooting

**Import errors?**
- Make sure dependencies are installed: `pip install pydantic-ai 'pydantic-ai-slim[openai]'`

**"No OPENAI_API_KEY set"?**
- Add your OpenAI API key to `.env` file

**Auth errors?**
- Make sure you're sending a valid Firebase token
- Check if emulator is running if USE_FIRESTORE_EMULATOR=true

**Agent not working?**
- Check backend logs for errors
- Verify OpenAI API key is valid
- Make sure the server restarted after installing dependencies

## Cost Note

Each query to the orchestrator uses OpenAI API credits. Monitor your usage at:
https://platform.openai.com/usage

The model is currently set to `gpt-4o`. You can change it to `gpt-4o-mini` in `orchestrator_service.py` for lower costs:

```python
The orchestrator uses GPT-4 by default. To use GPT-4-mini (cheaper), edit `orchestrator_service.py` line 16:
```python
model = OpenAIModel('gpt-4o-mini')
```
```

## Documentation

For complete documentation, see: `ORCHESTRATOR_README.md`

## Support

If you encounter issues:
1. Check the backend logs
2. Verify environment variables
3. Test individual service functions first
4. Review the FastAPI docs at http://localhost:8000/docs
