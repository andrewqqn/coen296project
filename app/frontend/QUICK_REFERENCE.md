# 🎯 Quick Reference - Orchestrator Frontend

## To Test Right Now

### 1. Start Backend
```bash
cd backend
uvicorn app:app --reload
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Open Browser
http://localhost:3000

### 4. Try It
- Type: "List all employees"
- Press: **Enter**
- See: Response from AI!

## Key Files

```
frontend/
├── components/
│   ├── orchestrator-query.tsx    ← Main component
│   └── ui/input.tsx              ← shadcn input
├── app/page.tsx                  ← Home page
├── lib/firebase.ts               ← Auth helper
└── .env.local                    ← Config

backend/
├── domain/services/
│   └── orchestrator_service.py   ← AI agent with tools
└── application/
    └── orchestrator_router.py    ← API endpoint
```

## How It Works

1. **User types** in text field
2. **Presses Enter** (or clicks send button)
3. **Frontend calls** `POST /orchestrator/`
4. **Backend processes** with GPT-4 + Pydantic AI
5. **AI selects tools** and executes them
6. **Response displayed** in card below input

## Component API

```tsx
import { OrchestratorQuery } from "@/components/orchestrator-query";

<OrchestratorQuery />  // That's it!
```

## Configuration

**Backend URL:** Edit `.env.local`
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

**Auth Token:** Edit `lib/firebase.ts`
```typescript
export async function getAuthToken() {
  return "your_token_here";  // Replace later
}
```

## Example Queries

✅ "List all employees"
✅ "Show me all expenses"  
✅ "What are the policies?"
✅ "Show recent audit logs"
✅ "Get employee with ID emp123"
✅ "Create a new employee named John"

## Features

✨ Enter key to submit
✨ Loading spinner
✨ Response display
✨ Tool tracking
✨ Error handling
✨ Responsive design

## Next: Add Real Auth

1. Install Firebase:
```bash
npm install firebase
```

2. Uncomment code in `lib/firebase.ts`

3. Add Firebase config to `.env.local`:
```env
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_PROJECT_ID=...
```

4. Done! Auth will work automatically.

## Troubleshooting

**Q: "Failed to fetch"**
A: Backend not running? Start with `uvicorn app:app --reload`

**Q: "401 Unauthorized"**  
A: Expected - implement Firebase auth or update backend for testing

**Q: Blank screen**
A: Check console (F12) for errors

**Q: CORS error**
A: Add CORS middleware to FastAPI backend

## Support

📖 See `ORCHESTRATOR_FRONTEND.md` for full docs
📖 See `SETUP_COMPLETE.md` for setup guide
