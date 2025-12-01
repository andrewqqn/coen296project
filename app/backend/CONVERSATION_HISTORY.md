# Conversation History Feature

## Overview

The orchestrator now supports conversation history, allowing the Pydantic AI agent to maintain context across multiple queries. This enables more natural, multi-turn conversations where the agent can reference previous questions and answers.

## Backend Implementation

### API Request Format

The orchestrator endpoint now accepts an optional `message_history` field:

```json
{
  "query": "Show me the first one",
  "message_history": [
    {
      "role": "user",
      "content": "List all employees"
    },
    {
      "role": "assistant",
      "content": "Here are all the employees: ..."
    },
    {
      "role": "user",
      "content": "How many are there?"
    },
    {
      "role": "assistant",
      "content": "There are 5 employees in the system."
    }
  ]
}
```

### Message Format

Each message in the history should have:
- `role`: Either `"user"` or `"assistant"`
- `content`: The message text

### Code Changes

1. **orchestrator_router.py**
   - Added `Message` Pydantic model
   - Updated `QueryRequest` to include optional `message_history` field
   - Converts Pydantic messages to dict format before passing to service

2. **orchestrator_service.py**
   - Updated `process_query()` to accept `message_history` parameter
   - Converts history to Pydantic AI's `ModelMessage` format
   - Uses `ModelRequest` for user messages and `ModelResponse` for assistant messages
   - Passes history to `agent.run()` via `message_history` parameter

## Frontend Implementation

### Features

The React component (`orchestrator-query.tsx`) now includes:

1. **Conversation Display**
   - Shows all previous messages in the conversation
   - Differentiates between user and assistant messages with styling
   - Scrollable history view with max height

2. **History Management**
   - Automatically maintains conversation state
   - "Clear" button to reset the conversation
   - Shows message count

3. **API Integration**
   - Automatically sends conversation history with each query
   - Adds new user/assistant exchanges to history
   - Only sends history if messages exist (omits empty array)

## Usage Examples

### Basic Conversation Flow

```
User: "List all employees"
Assistant: "Here are all employees: John, Jane, Bob"

User: "How many are there?"
Assistant: "There are 3 employees."

User: "Tell me about the first one"
Assistant: "John is an employee in the Engineering department..."
```

### API Examples

**First query (no history):**
```bash
curl -X POST http://localhost:8000/orchestrator/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query": "List all employees"}'
```

**Follow-up query (with history):**
```bash
curl -X POST http://localhost:8000/orchestrator/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "How many are there?",
    "message_history": [
      {"role": "user", "content": "List all employees"},
      {"role": "assistant", "content": "Here are all employees..."}
    ]
  }'
```

## Testing

Run the test script to see conversation history in action:

```bash
cd backend
python test/test_conversation_history.py
```

This will demonstrate:
1. Initial query without history
2. Follow-up question using context from first query
3. Third query building on full conversation

## Benefits

1. **Natural Conversations**: Users can ask follow-up questions without repeating context
2. **Better UX**: More natural interaction pattern, similar to ChatGPT
3. **Context Awareness**: Agent understands references to previous answers
4. **Efficiency**: No need to repeat information in each query

## Implementation Notes

- History is stored client-side (in React state)
- Each API call is stateless but includes full history
- History can be cleared at any time
- No server-side session management required
- Pydantic AI handles the message format internally

## Future Enhancements

Possible improvements:
- Persist conversation history to database
- Support multiple conversation threads
- Add conversation summaries for long histories
- Implement message editing/deletion
- Add export conversation feature
