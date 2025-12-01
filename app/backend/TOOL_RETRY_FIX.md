# Tool Retry Configuration Fix

## Problem

When the document agent encountered an error (e.g., file not found), Pydantic AI would automatically retry the tool call, leading to:

```
Error processing query: Tool 'call_document_agent' exceeded max retries count of 1
```

This happened because:
1. Pydantic AI has default retry behavior for tools
2. When a tool fails, it retries automatically
3. If the underlying issue isn't transient (e.g., file doesn't exist), retries fail too
4. User sees confusing "exceeded max retries" error instead of the actual problem

## Solution

### 1. Never Raise Exceptions from Tools

Changed all tools to catch exceptions and return error dictionaries:

```python
@self.pydantic_agent.tool  # Use default retries
async def call_document_agent(...):
    try:
        # Do work
        return {"success": True, ...}
    except Exception as e:
        # Never raise - return error dict
        return {"success": False, "error": str(e)}
```

**Why?**
- Tools never raise exceptions to Pydantic AI
- All errors are returned as `{"success": False, "error": "..."}`
- Pydantic AI won't retry because the tool "succeeded" (returned a value)
- LLM sees the error in the response and can explain it to the user
- No confusing "exceeded retries" messages

### 2. Improved Error Handling

Wrapped all tool calls in try-catch blocks:

```python
@self.pydantic_agent.tool(retries=0)
async def call_document_agent(...):
    try:
        # Validate parameters
        if not parameters.get("file_path"):
            return {"success": False, "error": "Missing required parameter: file_path"}
        
        # Call agent
        response = await document_agent.process_message(...)
        
        # Check for errors
        if response.message_type == "error":
            return {"success": False, "error": response.payload.get("error")}
        
        # Return success
        return {"success": True, **result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Benefits:**
- Consistent error format: `{"success": False, "error": "..."}`
- No unhandled exceptions
- Clear error messages
- LLM can understand and explain errors to user

### 3. Enhanced Logging

Added detailed logging to document agent's file reading:

```python
def _read_file(self, file_path: str) -> bytes:
    logger.info(f"Reading file: {file_path}")
    logger.info(f"Resolved to full path: {full_path}")
    
    if not os.path.exists(full_path):
        logger.error(f"File not found: {full_path}")
        # Log directory contents for debugging
        if os.path.exists(dir_path):
            logger.info(f"Files in directory: {os.listdir(dir_path)}")
        raise FileNotFoundError(error_msg)
    
    logger.info(f"File exists, size: {os.path.getsize(full_path)} bytes")
```

**Benefits:**
- Easy to debug file path issues
- Can see exactly what's happening
- Helps identify if file upload worked correctly

### 4. Updated System Prompt

Added error handling instructions:

```
ERROR HANDLING:
If a tool returns {"success": False, "error": "..."}, explain the error to the user clearly.
Common errors:
- File not found: Ask user to verify the file was uploaded correctly
- PDF processing error: The file may be corrupted or not a valid PDF
- Permission denied: User may not have access to this resource
```

**Benefits:**
- LLM knows how to handle errors
- Provides helpful messages to users
- Doesn't retry automatically

## Before vs After

### Before
```
User: "Create expense from receipt"
  ↓
Document agent fails (file not found)
  ↓
Pydantic AI retries automatically
  ↓
Still fails
  ↓
User sees: "Tool 'call_document_agent' exceeded max retries count of 1"
  ↓
User confused: "What does that mean?" 😕
```

### After
```
User: "Create expense from receipt"
  ↓
Document agent fails (file not found)
  ↓
Returns: {"success": False, "error": "File not found: /path/to/file.pdf"}
  ↓
LLM explains: "I couldn't find the receipt file. Please verify it was uploaded correctly."
  ↓
User understands the issue 😊
```

## Common Errors and Solutions

### Error: File Not Found

**Cause:** File path in query doesn't match actual uploaded file

**Solution:**
1. Check backend logs for actual file path
2. Verify file was uploaded successfully
3. Check `uploads/receipts/` directory

**Example Log:**
```
INFO: File saved locally: /path/to/backend/uploads/receipts/user123/abc.pdf
INFO: Enhanced query with file info: local://uploads/receipts/user123/abc.pdf
ERROR: File not found: /path/to/backend/uploads/receipts/user123/abc.pdf
```

### Error: PDF Processing Failed

**Cause:** File is corrupted or not a valid PDF

**Solution:**
1. Verify file is a valid PDF
2. Try opening the file manually
3. Re-upload the file

### Error: Permission Denied

**Cause:** Backend doesn't have permission to read the file

**Solution:**
1. Check file permissions
2. Verify backend process has read access
3. Check directory permissions

## Testing

### Test 1: Valid File Upload

```bash
# Upload a valid PDF receipt
# Query: "Create expense from this receipt"

# Expected:
✅ File found and processed
✅ Receipt info extracted
✅ Expense created
```

### Test 2: Missing File

```bash
# Query with non-existent file path
# Query: "Process receipt at local://uploads/receipts/missing.pdf"

# Expected:
❌ Clear error: "File not found: ..."
❌ No retry attempts
✅ User gets helpful message
```

### Test 3: Invalid PDF

```bash
# Upload a non-PDF file as PDF
# Query: "Create expense from this receipt"

# Expected:
❌ Clear error: "PDF processing failed: ..."
❌ No retry attempts
✅ User gets helpful message
```

## Configuration

### Retry Settings

**IMPORTANT:** We use default retries but catch ALL exceptions and return error dicts.

```python
# Correct approach - catch exceptions, return error dicts
@agent.tool  # Uses default retries
async def my_tool(...):
    try:
        # Do work
        return {"success": True, "result": ...}
    except Exception as e:
        # Return error dict instead of raising
        return {"success": False, "error": str(e)}

# WRONG - Don't use retries=0, it causes issues
@agent.tool(retries=0)  # ❌ Don't do this!
async def my_tool(...):
    ...
```

**Why not `retries=0`?**
- Setting `retries=0` means "no retries allowed"
- If tool raises ANY exception, Pydantic AI treats it as "exceeded retries"
- Better to catch exceptions and return error dicts
- Let Pydantic AI handle retries naturally (it won't retry if we return success=False)
```

### When to Use Retries

**Use retries (retries > 0) for:**
- Network requests that might timeout
- Database operations that might have transient failures
- External API calls that might be rate-limited

**Don't use retries (retries = 0) for:**
- File operations (file not found won't fix itself)
- Validation errors (invalid input won't become valid)
- Permission errors (access won't be granted automatically)
- Logic errors (bugs won't fix themselves)

## Summary

The retry fix ensures:
1. ✅ No automatic retries for non-transient errors
2. ✅ Clear error messages to users
3. ✅ Better logging for debugging
4. ✅ LLM can explain errors helpfully
5. ✅ Faster failure (no wasted retry attempts)

Users now get clear, actionable error messages instead of confusing "exceeded max retries" errors!
