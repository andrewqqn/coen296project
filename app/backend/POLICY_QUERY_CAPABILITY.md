# Policy Query Capability

## Overview
The orchestrator agent can now answer questions about expense reimbursement policies using the vector database (ChromaDB) that contains the policy document.

## Changes Made

### 1. Enhanced Orchestrator System Prompt
**File**: `backend/services/agents/orchestrator_agent.py`

Added explicit guidance for handling policy questions:
- ALWAYS use the `query_policies` tool for policy-related questions
- Present information clearly with specific amounts, limits, and rules
- Reference approval rules (R1-R4) when relevant

### 2. Improved Workflow Documentation
Added detailed guidance in the system prompt:
```
- Query policies → Use query_policies tool (e.g., "meal limits", "travel policy", "receipt requirements")
  * For policy questions, ALWAYS use query_policies to get accurate information from the policy database
  * Common policy queries: "reimbursement policies", "expense limits", "approval rules", "receipt requirements", "category limits"
  * Present policy information clearly with specific limits and rules
```

## How It Works

### Architecture
1. **Policy Source**: `backend/static/ExpenSense_Reimbursement_Policy.pdf`
2. **Vector Database**: ChromaDB with persistent storage in `.chroma_store`
3. **Embeddings**: Free HuggingFace model `sentence-transformers/all-mpnet-base-v2`
4. **Query Tool**: `query_policies` tool in orchestrator agent

### Query Flow
```
User Query → Orchestrator Agent → query_policies tool → Vector DB → Policy Snippets → LLM Response
```

### Existing Tool: `query_policies`
Already implemented in the orchestrator:
```python
@self.pydantic_agent.tool
def query_policies(
    ctx: RunContext[OrchestratorContext],
    query: str = "reimbursement policies"
) -> List[Dict[str, Any]]:
    """
    Query the reimbursement policy database to find relevant policy information.
    
    Args:
        query: Search query for policies (e.g., "meal limits", "travel policy", "receipt requirements")
    
    Returns:
        List of relevant policy snippets with their content
    """
```

## Example Queries

Users can now ask:
- "What are the reimbursement policies?"
- "What are the expense limits for meals?"
- "What are the approval rules?"
- "Tell me about receipt requirements"
- "What happens if I submit multiple expenses in one day?"
- "What's the limit for hotel expenses?"
- "What categories are eligible for reimbursement?"

## Policy Content

The policy PDF contains information about:
- **Approval Rules (R1-R4)**
  - R1: Auto-approve (≤$500, first request of day)
  - R2: Manual review (multiple requests same day)
  - R3: Manual review (>$500)
  - R4: Auto-reject (invalid/missing receipt)

- **Category Limits**
  - Meals: ≤ $120/day
  - Supplies: ≤ $200/item
  - Hotels: ≤ $500/day
  - Conference: No limit
  - Weekly total: ≤ $2,500

- **Receipt Requirements**
  - Vendor name
  - Date of transaction
  - Itemized charges
  - Total amount
  - Taxes/fees
  - Payment method

- **Eligible Categories**
  - Travel (airfare, hotel, transportation, parking, tolls)
  - Meals (business or travel meals)
  - Conference (registration fees)
  - Other (must be business-related)

## Testing

### Test Script
Created `backend/test_policy_query.py` to verify functionality:
```bash
cd backend
python test_policy_query.py
```

### Manual Testing
Use the frontend Query tab or API:
```bash
curl -X POST http://localhost:8080/api/orchestrator/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "What are the reimbursement policies?"}'
```

## Frontend Integration

The frontend already supports policy queries:
- **Query Tab**: Natural language interface
- **Example Query**: "What are the reimbursement policies?" is shown as an example
- **Policies Tab**: Static display of all policies (newly added)

## Technical Details

### Vector Database Setup
- **Storage**: Persistent ChromaDB in `backend/.chroma_store`
- **Collection**: `reimbursement_policy`
- **Chunk Size**: 800 characters with 150 character overlap
- **Auto-population**: If collection is empty, automatically loads from PDF on first query

### Embedding Model
- **Model**: `sentence-transformers/all-mpnet-base-v2`
- **Type**: Free, high-quality semantic embeddings
- **Device**: CPU (Cloud Run safe)
- **Normalization**: Enabled for better similarity matching

### Query Parameters
- **Default top_k**: 5 snippets (configurable)
- **Includes**: Documents, metadata, distances
- **Metadata**: Source file, page number, chunk index

## Benefits

1. **Accurate Information**: Queries the actual policy document, not hallucinated
2. **Always Up-to-date**: Update the PDF to update all policy responses
3. **Semantic Search**: Finds relevant policies even with different wording
4. **No API Costs**: Uses free HuggingFace embeddings
5. **Persistent**: ChromaDB stores embeddings on disk
6. **Automatic**: Auto-populates from PDF if collection is empty

## Maintenance

### Updating Policies
1. Update `backend/static/ExpenSense_Reimbursement_Policy.pdf`
2. Delete the ChromaDB collection or `.chroma_store` directory
3. Restart the backend - it will auto-populate on first query

### Monitoring
- Check logs for `[VectorDB]` entries
- Monitor query performance and relevance
- Review user queries to improve policy document structure

## No Code Complexity Added

The implementation leverages existing infrastructure:
- ✅ `query_policies` tool already existed
- ✅ Vector database already set up
- ✅ Policy PDF already in place
- ✅ Only enhanced system prompt for better guidance
- ✅ No new dependencies or services required

This is the simplest possible implementation - just improved prompting to use existing capabilities!
