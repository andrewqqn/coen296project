# API Routing Guide

## Current Routing Architecture

### Query Processing Endpoints

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                 │
└────────────┬────────────────────────────────┬───────────────────┘
             │                                │
             │ POST /orchestrator             │ POST /agents/query
             │ (Legacy - Maintained)          │ (New - Recommended)
             │                                │
┌────────────▼────────────────┐  ┌───────────▼──────────────────┐
│  orchestrator_router.py     │  │  agents_router.py            │
│  (Legacy Endpoint)          │  │  (New Endpoint)              │
└────────────┬────────────────┘  └───────────┬──────────────────┘
             │                                │
             │ Redirects to                   │ Direct call
             │                                │
             └────────────┬───────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────────┐
         │  multi_agent_orchestrator.py           │
         │  process_query_with_agents()           │
         └────────────────┬───────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────────┐
         │  orchestrator_agent.py                 │
         │  OrchestratorAgent                     │
         │  (Coordinates specialized agents)      │
         └────────────────┬───────────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
    ┌─────────────────┐     ┌─────────────────┐
    │ expense_agent   │     │ document_agent  │
    └─────────────────┘     └─────────────────┘
```

## Endpoint Comparison

| Feature | `/orchestrator` (Legacy) | `/agents/query` (New) |
|---------|-------------------------|----------------------|
| **Status** | ✅ Active (redirects) | ✅ Active (recommended) |
| **Backend** | Multi-agent system | Multi-agent system |
| **Response Format** | `tools_used` | `agents_used` |
| **Use Case** | Existing integrations | New development |
| **Deprecated?** | Endpoint maintained, implementation replaced | No |

## What Changed?

### Before Migration

```
POST /orchestrator
    ↓
orchestrator_router.py
    ↓
orchestrator_service.py (OLD IMPLEMENTATION)
    ↓
Direct tool calls to services
```

### After Migration

```
POST /orchestrator (Legacy)          POST /agents/query (New)
    ↓                                      ↓
orchestrator_router.py               agents_router.py
    ↓                                      ↓
    └──────────────┬───────────────────────┘
                   ↓
    multi_agent_orchestrator.py
                   ↓
    orchestrator_agent.py (A2A Protocol)
                   ↓
    Specialized Agents (expense_agent, document_agent)
```

## File Status

### ✅ Active Files (In Use)

| File | Purpose | Status |
|------|---------|--------|
| `controller/orchestrator_router.py` | Legacy endpoint (redirects) | ✅ Active |
| `controller/agents_router.py` | New multi-agent endpoints | ✅ Active |
| `services/multi_agent_orchestrator.py` | Service layer for agents | ✅ Active |
| `services/agents/orchestrator_agent.py` | Main orchestrator agent | ✅ Active |
| `services/agents/expense_agent_service.py` | Expense review agent | ✅ Active |
| `services/agents/document_agent_service.py` | Document processing agent | ✅ Active |
| `services/agents/a2a_protocol.py` | A2A protocol implementation | ✅ Active |
| `services/agents/base_agent.py` | Base agent class | ✅ Active |

### ⚠️ Deprecated Files (Not Used)

| File | Purpose | Status |
|------|---------|--------|
| `services/orchestrator_service.py` | Old orchestrator implementation | ⚠️ Deprecated (kept for reference) |

## API Endpoints

### Multi-Agent System (Recommended)

```bash
# List all agents
GET /agents/registry

# Get specific agent card
GET /agents/registry/{agent_id}

# Process query
POST /agents/query
{
  "query": "Review expense exp_123",
  "message_history": [...]  # Optional
}

# Process query with files
POST /agents/query-with-files
FormData:
  query: "Extract info from this receipt"
  files: [receipt.pdf]
```

### Legacy Endpoint (Backward Compatible)

```bash
# Process query (redirects to multi-agent system)
POST /orchestrator
{
  "query": "Show me all employees"
}
```

## Response Format Mapping

### Legacy `/orchestrator` Response
```json
{
  "success": true,
  "response": "Here are the results...",
  "tools_used": ["expense_agent", "document_agent"],
  "query": "Review expense exp_123"
}
```

### New `/agents/query` Response
```json
{
  "success": true,
  "response": "Here are the results...",
  "agents_used": ["expense_agent", "document_agent"],
  "query": "Review expense exp_123"
}
```

**Note**: The legacy endpoint maps `agents_used` → `tools_used` for compatibility.

## Migration Recommendations

### For Existing Code
✅ **No changes required!** The `/orchestrator` endpoint continues to work.

### For New Code
✅ **Use `/agents/query`** for clarity and to access new features:
- Agent discovery via `/agents/registry`
- Explicit agent card inspection
- File upload support via `/agents/query-with-files`

### Example Migration

**Before (Legacy):**
```javascript
const response = await fetch('/orchestrator', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ query: 'Review expense exp_123' })
});
```

**After (New):**
```javascript
const response = await fetch('/agents/query', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ query: 'Review expense exp_123' })
});
```

## Benefits of New System

1. **Agent Discovery**: Can query `/agents/registry` to see available agents
2. **Capability Inspection**: Each agent advertises its capabilities via agent cards
3. **Standardized Protocol**: A2A messages provide consistent communication
4. **Modularity**: Easy to add new agents without changing existing code
5. **Better Monitoring**: Track which agents were used for each query

## Testing Both Endpoints

```bash
# Test legacy endpoint
curl -X POST http://localhost:8000/orchestrator \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{"query": "What agents are available?"}'

# Test new endpoint
curl -X POST http://localhost:8000/agents/query \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{"query": "What agents are available?"}'

# Both should return similar results!
```

## Summary

- ✅ **Legacy `/orchestrator` endpoint**: Still works, now uses multi-agent system internally
- ✅ **New `/agents/query` endpoint**: Recommended for new development
- ✅ **Backward compatibility**: Existing frontend code works without changes
- ✅ **orchestrator_service.py**: Deprecated, no longer used
- ✅ **All queries**: Now benefit from multi-agent architecture

The system provides a smooth migration path while maintaining full backward compatibility.
