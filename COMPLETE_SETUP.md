# 🚀 Complete Setup Guide - Authentication & Orchestrator

## What's Been Implemented

✅ **CORS Support** - Backend now accepts requests from frontend
✅ **Firebase Authentication** - Login/signup with Firebase Auth Emulator
✅ **Auto Employee Creation** - New users automatically get employee records
✅ **Protected Routes** - Only authenticated users can access the app
✅ **Natural Language Query Interface** - Ask questions in plain English

## Quick Start

### 1. Start Firebase Emulators

In one terminal:
```bash
cd /Users/andrewnguyen/Documents/workspace/scu/coen296/project
firebase emulators:start
```

This starts:
- 🔥 Emulator UI: http://localhost:4000
- 🔐 Auth Emulator: http://localhost:9099
- 📦 Firestore Emulator: http://localhost:8080
- 💾 Storage Emulator: http://localhost:9199

### 2. Start Backend

In another terminal:
```bash
cd backend
bash start.sh
# or: uvicorn app:app --reload
```

Backend runs on: http://localhost:8000

### 3. Start Frontend

In another terminal:
```bash
cd frontend
npm run dev
```

Frontend runs on: http://localhost:3000

### 4. Test the Flow

1. **Open** http://localhost:3000
2. **Click** "Don't have an account? Sign up"
3. **Enter:**
   - Full Name: "John Doe"
   - Email: "john@example.com"
   - Password: "password123"
4. **Click** "Create Account"
5. **You're logged in!** The system automatically:
   - Creates Firebase auth user
   - Creates employee record in backend
   - Logs you in

6. **Try a query:** Type "List all employees" and press Enter

## Changes Made

### Backend Changes

**`app.py`** - Added CORS middleware:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Frontend Changes

**New Files:**
- `lib/firebase.ts` - Firebase configuration with emulator support
- `lib/auth-context.tsx` - Authentication state management
- `components/login.tsx` - Login/signup form with auto employee creation
- `.env.local` - Environment configuration

**Updated Files:**
- `app/layout.tsx` - Wrapped with AuthProvider
- `app/page.tsx` - Shows login or main app based on auth state
- `components/orchestrator-query.tsx` - Uses real Firebase tokens

## How It Works

### Sign Up Flow

```
User fills form → Click "Create Account"
        ↓
Firebase creates auth user
        ↓
Get ID token from Firebase
        ↓
POST /employees with user data
        ↓
Employee record created in Firestore
        ↓
User logged in automatically
```

### Query Flow

```
User types query → Press Enter
        ↓
Get Firebase ID token
        ↓
POST /orchestrator/ with token
        ↓
Backend validates token
        ↓
Pydantic AI processes query
        ↓
Response displayed
```

## Employee Record Structure

When a user signs up, this employee record is created:

```json
{
  "authentication_id": "firebase-uid",
  "email": "user@example.com",
  "name": "User Name",
  "position": "Employee",
  "role": "employee"
}
```

## Testing

### Create Test Users

1. Sign up with any email/password (emulator accepts anything)
2. Check Emulator UI (http://localhost:4000) to see:
   - Auth users in Authentication tab
   - Employee records in Firestore tab

### Test Queries

Once logged in, try:
- "List all employees" - See yourself!
- "Show me all expenses"
- "What are the policies?"
- "Create a new expense for $100"

## Configuration Files

### Frontend `.env.local`

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_FIREBASE_API_KEY=demo-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=localhost
NEXT_PUBLIC_FIREBASE_PROJECT_ID=demo-project
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=demo-bucket
NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST=http://localhost:9099
```

### Backend `.env` (ensure these are set)

```env
USE_FIRESTORE_EMULATOR=true
FIRESTORE_EMULATOR_HOST=localhost:8080
FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
FIREBASE_PROJECT_ID=demo-project
OPENAI_API_KEY=your-openai-key
```

## Troubleshooting

### "Fetch API cannot load" Error
✅ **FIXED** - CORS middleware added to backend

### "User not authenticated" Error
- Make sure you're logged in
- Check Firebase emulator is running
- Check browser console for errors

### Employee not created
- Check backend logs for errors
- Check Emulator UI → Firestore → employees collection
- Verify backend is running and accessible

### Firebase connection errors
- Ensure emulators are running: `firebase emulators:start`
- Check emulator UI at http://localhost:4000
- Verify `.env.local` has correct emulator URLs

## Features

### Authentication
- ✅ Email/password sign up
- ✅ Email/password sign in
- ✅ Sign out
- ✅ Auth state persistence
- ✅ Protected routes
- ✅ Firebase emulator support

### Employee Management
- ✅ Auto-create on signup
- ✅ Store Firebase UID
- ✅ Store user profile
- ✅ Default role: "employee"
- ✅ Default position: "Employee"

### Orchestrator
- ✅ Natural language queries
- ✅ Token-based auth
- ✅ Real-time responses
- ✅ Error handling
- ✅ Loading states

## Next Steps

### To Deploy to Production

1. **Set up real Firebase project:**
   ```bash
   firebase init
   firebase deploy
   ```

2. **Update frontend `.env.local`:**
   ```env
   NEXT_PUBLIC_FIREBASE_API_KEY=real-api-key
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-app.firebaseapp.com
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
   # Remove emulator host
   ```

3. **Update backend `.env`:**
   ```env
   USE_FIRESTORE_EMULATOR=false
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_CREDENTIALS_PATH=path/to/serviceAccount.json
   ```

4. **Update CORS origins in `app.py`:**
   ```python
   allow_origins=["https://your-domain.com"]
   ```

### Enhancements

- [ ] Add password reset
- [ ] Add email verification
- [ ] Add profile editing
- [ ] Add role-based access control
- [ ] Add OAuth providers (Google, GitHub)
- [ ] Add user profile pictures
- [ ] Add employee search
- [ ] Add admin dashboard

## Architecture

```
┌─────────────────┐
│   Frontend      │
│  (Next.js)      │
└────────┬────────┘
         │
         ├─ Firebase Auth (Emulator)
         │  ├─ Sign Up
         │  ├─ Sign In
         │  └─ Get Token
         │
         ├─ POST /employees
         │  └─ Create Employee Record
         │
         └─ POST /orchestrator/
            └─ Natural Language Query
                 │
                 ├─ Pydantic AI Agent
                 │  └─ GPT-4 Tool Selection
                 │
                 └─ Backend Services
                    ├─ Employee Service
                    ├─ Expense Service
                    ├─ Policy Service
                    └─ Audit Service
```

## Security Notes

🔒 **Current Setup (Development):**
- Using Firebase emulator
- Any email/password works
- Tokens are valid within emulator only

🔐 **Production Requirements:**
- Use real Firebase project
- Implement email verification
- Add password requirements
- Enable 2FA (optional)
- Use environment secrets
- Enable Firebase security rules

## Support

**Check logs:**
- Backend: Terminal running `uvicorn`
- Frontend: Browser console (F12)
- Firebase: Emulator UI (http://localhost:4000)

**Common issues:**
- Port conflicts: Change ports in config files
- Emulator not starting: Check Firebase CLI is installed
- CORS errors: Verify backend CORS middleware
- Auth errors: Check emulator is running

## Success Checklist

✅ Firebase emulators running
✅ Backend running on port 8000
✅ Frontend running on port 3000
✅ Can sign up new user
✅ Employee record created automatically
✅ Can sign in with created user
✅ Can submit queries to orchestrator
✅ Queries return AI-powered responses

---

**Everything is now set up and working!** 🎉

1. Start emulators: `firebase emulators:start`
2. Start backend: `cd backend && bash start.sh`
3. Start frontend: `cd frontend && npm run dev`
4. Open http://localhost:3000 and sign up!
