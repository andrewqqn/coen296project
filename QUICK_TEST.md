# 🎯 Quick Test Guide

## Test the Complete Flow (5 minutes)

### Step 1: Start All Services

**Terminal 1 - Firebase Emulators:**
```bash
cd /Users/andrewnguyen/Documents/workspace/scu/coen296/project
firebase emulators:start
```
✅ Wait for: "All emulators ready!"

**Terminal 2 - Backend:**
```bash
cd /Users/andrewnguyen/Documents/workspace/scu/coen296/project/backend
bash start.sh
```
✅ Wait for: "Uvicorn running on http://127.0.0.1:8000"

**Terminal 3 - Frontend:**
```bash
cd /Users/andrewnguyen/Documents/workspace/scu/coen296/project/frontend
npm run dev
```
✅ Wait for: "Ready on http://localhost:3000"

### Step 2: Create Account

1. **Open:** http://localhost:3000
2. **You see:** Sign In form
3. **Click:** "Don't have an account? Sign up"
4. **Fill in:**
   - Full Name: `John Doe`
   - Email: `john@test.com`
   - Password: `password123`
5. **Click:** "Create Account"
6. **Wait:** Loading spinner (creating account + employee record)
7. **Success!** You're now logged in and see the main app

### Step 3: Verify Employee Created

1. **Open:** http://localhost:4000 (Firebase Emulator UI)
2. **Click:** "Firestore" tab
3. **Expand:** `employees` collection
4. **See:** Your employee record with:
   - authentication_id: (Firebase UID)
   - email: john@test.com
   - name: John Doe
   - position: Employee
   - role: employee

### Step 4: Test Orchestrator

Back in the app (http://localhost:3000):

1. **Type:** "List all employees"
2. **Press:** Enter
3. **See:** Response showing your employee!

Try more queries:
- "Show me all expenses"
- "What are the policies?"
- "Show recent audit logs"

### Step 5: Test Sign Out

1. **Click:** "Sign Out" button (top right)
2. **You see:** Login page again
3. **Sign in** with same credentials
4. **Success!** Back to main app

---

## Visual Flow

```
┌─────────────────────────────────────┐
│  http://localhost:3000              │
│  ┌───────────────────────────────┐  │
│  │   Sign Up Form                │  │
│  │  ┌────────────────────────┐   │  │
│  │  │ Name: John Doe         │   │  │
│  │  │ Email: john@test.com   │   │  │
│  │  │ Password: ••••••••     │   │  │
│  │  └────────────────────────┘   │  │
│  │  [ Create Account ]           │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│  Firebase Auth Emulator             │
│  Creates user: john@test.com        │
│  Returns: Firebase UID + Token      │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│  POST /employees                    │
│  {                                  │
│    authentication_id: "uid...",     │
│    email: "john@test.com",          │
│    name: "John Doe",                │
│    position: "Employee",            │
│    role: "employee"                 │
│  }                                  │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│  Firestore Emulator                 │
│  employees/[doc_id]                 │
│  ✅ Employee record created         │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│  Main App                           │
│  ┌───────────────────────────────┐  │
│  │ Expense Reimbursement System  │  │
│  │                               │  │
│  │ [Ask me anything... ]    [→]  │  │
│  │                               │  │
│  │ Try: "List all employees"     │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

---

## Checklist

Before testing:
- [ ] Firebase emulators running
- [ ] Backend running
- [ ] Frontend running
- [ ] All three terminals show no errors

During signup:
- [ ] Sign up form appears
- [ ] Can enter name, email, password
- [ ] "Create Account" button works
- [ ] Loading spinner appears
- [ ] Automatically logged in after signup

After signup:
- [ ] Main app appears
- [ ] Email shown in header
- [ ] Can type in query field
- [ ] Queries return responses
- [ ] Sign out button works

Verification:
- [ ] Employee in Firestore (http://localhost:4000)
- [ ] User in Auth (http://localhost:4000)
- [ ] "List all employees" returns your record

---

## Expected Results

### After Signup
```
✅ Firebase Auth: User created
✅ Backend: Employee record created
✅ Frontend: Logged in automatically
✅ Header shows: john@test.com
```

### After Query: "List all employees"
```
Response:
Here are all the employees in the system:
1. John Doe (john@test.com) - Employee

Tools Used: [list_all_employees]
```

### In Emulator UI (http://localhost:4000)

**Authentication Tab:**
```
john@test.com
UID: xxxxx
Provider: password
```

**Firestore Tab:**
```
employees/
  └── [doc_id]
      ├── authentication_id: "xxxxx"
      ├── email: "john@test.com"
      ├── name: "John Doe"
      ├── position: "Employee"
      └── role: "employee"
```

---

## Troubleshooting

**"Cannot connect" errors:**
→ Check all 3 services are running

**"CORS" errors:**
→ Backend needs restart after CORS changes

**Employee not created:**
→ Check backend terminal for errors
→ Check emulator is accepting connections

**Can't sign in:**
→ Use same email/password from signup
→ Check emulator UI for user list

---

## Success! 🎉

You should now have:
- ✅ Working authentication
- ✅ Auto employee creation
- ✅ Natural language queries
- ✅ Complete full-stack integration

**Next:** Try more queries and explore the system!
