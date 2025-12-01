# Frontend Update for Multi-Agent System

## Summary

The frontend `orchestrator-query.tsx` component has been updated to use the new multi-agent system endpoints.

## Changes Made

### 1. Endpoint Updates

**Before:**
```typescript
// Old endpoint
POST /orchestrator/
```

**After:**
```typescript
// New endpoints
POST /agents/query              // For text queries
POST /agents/query-with-files   // For queries with file uploads
```

### 2. Response Interface

**Before:**
```typescript
interface OrchestratorResponse {
  success: boolean;
  response: string | null;
  tools_used: string[];  // Old field name
  query: string;
  error: string | null;
}
```

**After:**
```typescript
interface AgentQueryResponse {
  success: boolean;
  response: string | null;
  agents_used: string[];  // New field name
  query: string;
  error: string | null;
}
```

### 3. New Features

#### Agent Usage Indicator
The component now displays which agents were used to process the query:

```tsx
{lastAgentsUsed.length > 0 && (
  <div className="flex items-center gap-2">
    <span>Agents Used:</span>
    {lastAgentsUsed.map(agentId => (
      <span className="badge">{formatAgentName(agentId)}</span>
    ))}
  </div>
)}
```

#### Agent Name Formatting
Friendly names for agents:
- `expense_agent` → "Expense Agent"
- `document_agent` → "Document Agent"
- `orchestrator` → "Orchestrator"

## Code Changes

### State Management

```typescript
// Added new state for tracking agents
const [lastAgentsUsed, setLastAgentsUsed] = useState<string[]>([]);

// Store agents used after successful query
if (data.agents_used && data.agents_used.length > 0) {
  setLastAgentsUsed(data.agents_used);
}
```

### API Calls

```typescript
// Text query
const response = await fetch(`${backendUrl}/agents/query`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`,
  },
  body: JSON.stringify({ 
    query: currentQuery,
    message_history: conversationHistory
  }),
});

// Query with files
const response = await fetch(`${backendUrl}/agents/query-with-files`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
  },
  body: formData,
});
```

## Backward Compatibility

✅ **The component is fully backward compatible!**

The backend's `/orchestrator` endpoint has been updated to redirect to the multi-agent system, so:
- Old frontend code using `/orchestrator` still works
- New frontend code using `/agents/query` gets the same functionality
- Response format is compatible (agents_used vs tools_used)

## Visual Changes

### Before
```
[User Input]
[Conversation History]
```

### After
```
[Agents Used: Expense Agent, Document Agent]  ← NEW
[User Input]
[Conversation History]
```

## Testing

### Test Text Query
```bash
# Start frontend
cd frontend
npm run dev

# Navigate to the orchestrator page
# Type: "What agents are available?"
# Should see: "Agents Used: [none or orchestrator]"
```

### Test File Upload
```bash
# Upload a PDF receipt
# Type: "Extract information from this receipt"
# Should see: "Agents Used: Document Agent"
```

### Test Expense Review
```bash
# Type: "Review expense exp_123"
# Should see: "Agents Used: Expense Agent"
```

## Benefits

1. ✅ **Clear Agent Visibility**: Users can see which agents processed their query
2. ✅ **Better UX**: Visual feedback on system activity
3. ✅ **Modern Architecture**: Uses new multi-agent endpoints
4. ✅ **Backward Compatible**: Works with both old and new backend
5. ✅ **Type Safe**: Updated TypeScript interfaces

## Migration Notes

### For Developers

If you have other components using the orchestrator:

1. **Update the endpoint**:
   ```typescript
   // Old
   fetch('/orchestrator/', ...)
   
   // New
   fetch('/agents/query', ...)
   ```

2. **Update the response interface**:
   ```typescript
   // Old
   tools_used: string[]
   
   // New
   agents_used: string[]
   ```

3. **Optional: Add agent display**:
   ```typescript
   {data.agents_used?.map(agent => (
     <span>{formatAgentName(agent)}</span>
   ))}
   ```

### For Users

No changes needed! The interface looks and works the same, with the addition of showing which agents were used.

## File Location

```
frontend/
└── components/
    └── orchestrator-query.tsx  ← Updated
```

## Related Documentation

- Backend: `backend/ROUTING_GUIDE.md`
- Backend: `backend/MULTI_AGENT_SYSTEM.md`
- Backend: `backend/MULTI_AGENT_QUICKSTART.md`

## Summary

The frontend now uses the new multi-agent system while maintaining full backward compatibility. Users get better visibility into which agents processed their queries, and the code is cleaner and more maintainable.
