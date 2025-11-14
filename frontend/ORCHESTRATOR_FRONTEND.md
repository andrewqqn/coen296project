# Frontend Orchestrator Integration

## Overview

The frontend now includes a natural language query interface that connects to the `/orchestrator` backend endpoint. Users can type questions in plain English and get AI-powered responses.

## What Was Added

### Components

1. **`components/ui/input.tsx`** - shadcn Input component
2. **`components/orchestrator-query.tsx`** - Main orchestrator query interface
   - Text input field with Enter key support
   - Loading states with spinner
   - Response display with tool tracking
   - Error handling

### Updated Files

1. **`app/page.tsx`** - Updated home page with orchestrator interface
2. **`.env.local`** - Environment configuration

## Features

✨ **Natural Language Input** - Type questions in plain English
⌨️ **Enter Key Support** - Press Enter to submit query
🔄 **Loading States** - Visual feedback while processing
📊 **Response Display** - Shows AI response with tools used
❌ **Error Handling** - Clear error messages
🎨 **Responsive Design** - Works on all screen sizes

## Setup

### 1. Install Dependencies (Already Done)

The shadcn Input component has been installed.

### 2. Configure Environment

Edit `.env.local` to set your backend URL:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 3. Add Firebase Authentication (TODO)

Currently, the component uses a placeholder token. To implement real authentication:

1. Install Firebase:
```bash
npm install firebase
```

2. Create `lib/firebase.ts`:
```typescript
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  // ... other config
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
```

3. Update `components/orchestrator-query.tsx` to get the real token:
```typescript
import { auth } from '@/lib/firebase';

// In handleSubmit:
const user = auth.currentUser;
const token = await user?.getIdToken();
```

### 4. Run the Frontend

```bash
cd frontend
npm run dev
```

Open http://localhost:3000

## Usage

### Example Queries

Try these queries in the text field:

**Employee Queries:**
- "List all employees"
- "Show me employee with ID emp123"
- "Create a new employee named Jane Smith"

**Expense Queries:**
- "Show me all expenses"
- "What expenses do we have?"
- "Get expense details for exp456"

**Policy Queries:**
- "What are the reimbursement policies?"
- "Show me all policies"

**Audit Queries:**
- "Show me recent audit logs"
- "List all system activity"

## Component Structure

```typescript
<OrchestratorQuery />
  ├─ Input field (with Enter key handler)
  ├─ Submit button (with loading state)
  ├─ Error display (if error occurs)
  └─ Result display
      ├─ Success response with tools used
      └─ Error message if query failed
```

## API Integration

The component calls the backend endpoint:

```typescript
POST http://localhost:8000/orchestrator/
Headers:
  - Content-Type: application/json
  - Authorization: Bearer <firebase_token>
Body:
  {
    "query": "user's natural language query"
  }
```

## Customization

### Change Backend URL

Edit `.env.local`:
```env
NEXT_PUBLIC_BACKEND_URL=https://your-api.com
```

### Modify Styling

The component uses Tailwind CSS classes. Key classes:
- `bg-card` - Card background
- `text-foreground` - Primary text
- `text-muted-foreground` - Secondary text
- `border` - Border color

### Add History

To add query history, modify `orchestrator-query.tsx`:

```typescript
const [history, setHistory] = useState<OrchestratorResponse[]>([]);

// In handleSubmit after getting data:
setHistory([data, ...history]);

// Display history:
{history.map((item, idx) => (
  <div key={idx}>...</div>
))}
```

## Security Notes

⚠️ **Current Implementation:**
- Uses placeholder Firebase token
- Not production-ready

✅ **For Production:**
1. Implement Firebase Authentication
2. Protect routes with auth guards
3. Store tokens securely
4. Add CORS configuration on backend
5. Use environment variables for sensitive data

## Troubleshooting

**"Failed to fetch" error:**
- Make sure backend is running on http://localhost:8000
- Check CORS settings on backend
- Verify backend URL in `.env.local`

**"401 Unauthorized":**
- Firebase token is invalid or expired
- Implement proper Firebase authentication

**No response:**
- Check browser console for errors
- Verify backend endpoint is `/orchestrator/`
- Check network tab in browser DevTools

## Next Steps

1. ✅ Basic text input with Enter key - DONE
2. ✅ Backend API integration - DONE
3. ✅ Response display - DONE
4. ✅ Error handling - DONE
5. 🔲 Add Firebase authentication
6. 🔲 Add query history
7. 🔲 Add loading skeleton
8. 🔲 Add response formatting (markdown, etc.)
9. 🔲 Add voice input
10. 🔲 Add query suggestions

## File Structure

```
frontend/
├── components/
│   ├── ui/
│   │   ├── input.tsx          # shadcn Input component
│   │   └── button.tsx         # shadcn Button component
│   └── orchestrator-query.tsx # Main orchestrator interface
├── app/
│   └── page.tsx               # Home page with orchestrator
└── .env.local                 # Environment configuration
```
