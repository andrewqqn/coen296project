# Policies Tab Feature

## Overview
Added a new "Policies" tab to the frontend that displays static expense policies and approval decision-making rules.

## Changes Made

### 1. New Component: `frontend/components/policies.tsx`
Created a comprehensive Policies component that displays:

#### Automated Approval Rules
- **R1: Auto-Approve** - Automatic approval for expenses ≤ $500 (first request of day)
- **R2: Manual Review** - Frequency violation (multiple requests same day)
- **R3: Manual Review** - Large amounts (> $500)
- **R4: Auto-Reject** - Invalid documentation

#### Receipt Requirements
- Vendor/merchant name
- Date of transaction
- Itemized list of charges
- Total amount
- Taxes and fees
- Payment method

#### Eligible Categories & Limits
- Meals: ≤ $120/day
- Supplies: ≤ $200/item
- Hotels: ≤ $500/day
- Travel: Varies
- Conference: No limit
- Other: Case-by-case
- Weekly total: ≤ $2,500

#### AI-Powered Review Process
5-step process visualization:
1. Receipt Processing (PDF → images → AI vision)
2. Static Rules Check (R1-R4)
3. Context Gathering (policies, profile, history)
4. Final Decision (APPROVE/REJECT/MANUAL)
5. Payment Processing (auto-update bank balance)

#### Conflict Resolution
- Receipt image is primary source of truth
- Conflicts flagged with "CONFLICT" rule
- Manual review or rejection based on severity

### 2. Updated: `frontend/app/page.tsx`
- Added "policies" to View type
- Imported Policies component and FileText icon
- Added Policies tab to navigation (between Submit Expense and Account)
- Added Policies view rendering with proper header and description

## UI Components Used
- Card, CardContent, CardDescription, CardHeader, CardTitle
- Badge (with outline variant and custom colors)
- Lucide icons: CheckCircle2, XCircle, AlertCircle, FileText, DollarSign, Receipt

## Design Features
- Color-coded rule badges (green for approve, orange/blue for manual, red for reject)
- Clear visual hierarchy with icons
- Numbered steps for AI review process
- Organized sections with proper spacing
- Responsive layout using Tailwind CSS

## User Experience
Users can now:
- View all expense policies in one place
- Understand the automated approval rules
- See category limits and requirements
- Learn about the AI review process
- Know what makes a valid receipt
- Understand conflict resolution procedures

## Technical Notes
- Component is client-side rendered ("use client")
- No API calls required (static content)
- Fully typed with TypeScript
- Follows existing design system patterns
- Accessible with proper semantic HTML
