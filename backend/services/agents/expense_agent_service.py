import json
import base64
import logging
from io import BytesIO
from datetime import datetime, timezone
from typing import Optional, Literal, List, Any, Dict, cast

from pdf2image import convert_from_bytes
from dateutil import parser
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from openai import AsyncOpenAI
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds

import domain.repositories.expense_repo as expense_repo
from services.document_service import download_receipt
from services.vector_db_service import query_vector_db
from services.audit_log_service import create_log
from services.employee_service import get_employee
from services.agents.base_agent import BaseAgent
from services.agents.a2a_protocol import (
    AgentCard,
    AgentCapability,
    A2ARequest,
    A2AResponse
)

# ============================================================
# Logger
# ============================================================
logger = logging.getLogger("expense_agent")
logger.setLevel(logging.INFO)

client = AsyncOpenAI()


# ============================================================
# JSON Safe Conversion
# ============================================================
def to_json_safe(obj):
    """Recursively convert objects to JSON-safe formats."""
    if isinstance(obj, (datetime, DatetimeWithNanoseconds)):
        return obj.isoformat()

    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("utf-8")

    if isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [to_json_safe(v) for v in obj]

    return obj

# ============================================================
# Date Normalization
# ============================================================

def normalize_date_only(value):
    if not value:
        return value
    try:
        dt = parser.parse(value)
        return dt.strftime("%Y-%m-%d")
    except:
        return value


# ============================================================
# Decision Schema
# ============================================================
class ExpenseDecision(BaseModel):
    decision: Literal["APPROVE", "REJECT", "MANUAL"]
    rule: Optional[str] = ""
    reason: str = ""
    confidence: float = 0.0

    merchant_name: Optional[str] = ""
    date_of_expense: Optional[str] = ""
    total_amount: Optional[str] = ""
    subtotal: Optional[str] = ""
    tax: Optional[str] = ""
    payment_method: Optional[str] = ""



parser = JsonOutputParser(pydantic_object=ExpenseDecision)
format_instructions = parser.get_format_instructions()


# ============================================================
# Convert PDF → [JPEG] → [base64] List
# ============================================================
def pdf_to_base64(pdf_bytes: bytes) -> Optional[List[str]]:
    base64_images = []

    try:
        pages = convert_from_bytes(pdf_bytes, dpi=100)

        for i, img in enumerate(pages):
            buf = BytesIO()
            img.save(buf, format="JPEG")
            jpeg_bytes = buf.getvalue()

            base64_str = base64.b64encode(jpeg_bytes).decode("utf-8")
            base64_images.append(base64_str)

        if not base64_images:
            logger.error("[PDF] PDF converted to zero pages.")
            return None

        return base64_images

    except Exception as e:
        error_message = str(e)
        logger.error(f"[PDF] PDF→JPEG conversion failed: {error_message}")
        return None

def save_base64_to_jpeg(base64_str: str, output_path: str):
    """
    Convert a base64 JPEG string back into an image file for manual inspection.
    """
    img_bytes = base64.b64decode(base64_str)
    with open(output_path, "wb") as f:
        f.write(img_bytes)

# ============================================================
# Static rules R1–R4
# ============================================================
def apply_static_rules(expense, receipt_summary):
    amount = float(expense["amount"])
    today = datetime.now(timezone.utc).date()

    all_exp = expense_repo.get_by_employee(expense["employee_id"])
    all_exp = to_json_safe(all_exp)

    # Build today_exp defensively: ensure each entry is a dict with a string 'submitted_at'
    today_exp = []
    for item in all_exp:
        try:
            if not isinstance(item, dict):
                continue
            submitted_at = item.get("submitted_at")
            if not isinstance(submitted_at, str):
                continue
            if datetime.fromisoformat(submitted_at).date() == today:
                today_exp.append(item)
        except Exception:
            # If parsing fails for any entry, skip it
            continue

    # R4 – Missing or unreadable receipt → REJECT
    if "no receipt" in receipt_summary.lower():
        return "R4", "REJECT"

    # R3 – >$500, always MANUAL
    if amount >= 500:
        return "R3", "MANUAL"

    # R2 – already submitted today → MANUAL
    if amount <= 500 and len(today_exp) >= 1:
        return "R2", "MANUAL"

    # R1 – safe approve
    return "R1", "APPROVE"

# ============================================================
# AI Review Logic
# ============================================================

async def evaluate_and_maybe_auto_approve(expense_id: str):
    logger.info(f"[AI] Reviewing expense_id={expense_id}")

    # -------- Load expense ----------
    expense = expense_repo.get(expense_id)
    expense = to_json_safe(expense)

    # -------- Load & process receipt ----------
    base64_img_list = None
    receipt_summary = "(no receipt provided)"

    try:
        if expense.get("receipt_path"):
            pdf_bytes = download_receipt(expense["receipt_path"])
            base64_img_list = pdf_to_base64(pdf_bytes)

            if base64_img_list:
                receipt_summary = "receipt_image_attached"
                logger.info(f"[AI] Successfully prepared {len(base64_img_list)} image(s) for AI review")
            else:
                receipt_summary = "(receipt unreadable)"
        else:
            receipt_summary = "(no receipt provided)"
    except Exception as e:
        logger.error(f"[AI] Receipt processing failed: {e}", exc_info=True)
        receipt_summary = f"(download failed: {e})"

    # -------- Static Rules ----------
    rule, static_decision = apply_static_rules(expense, receipt_summary)

    # ============================================================
    #  PHASE 1: Agent Planner — Decide tool usage
    # ============================================================

    planner_prompt = """
    You are the TOOL SELECTION PLANNER for the ExpenseSense Review System.

    Your ONLY task is to decide which optional data sources must be retrieved
    BEFORE the final expense decision agent is invoked.

    You MUST comply with ALL requirements below.

    ===============================================================================
    OUTPUT FORMAT (MANDATORY — STRICT JSON ONLY)
    ===============================================================================
    You MUST respond with ONLY valid JSON:
    - No prose
    - No markdown
    - No explanations
    - No commentary
    - No backticks
    - No code fences
    - No surrounding text
    - No trailing commas
    - No extra whitespace before/after

    Your output MUST match this schema EXACTLY:

    {
      "vector_db": true or false,
      "employee_profile": true or false,
      "expense_history": true or false,
      "reason": "<ONE short sentence explaining why>"
    }

    Field rules:
    - "vector_db": true if policy lookup may be helpful (ambiguous category, limit checks).
    - "employee_profile": true if employee role/department/status may affect interpretation.
    - "expense_history": true if pattern analysis (duplicates, frequency, split receipts) may matter.
    - If uncertain → MUST return true.
    - "reason": concise one-sentence justification. No commas at the end.

    ===============================================================================
    PLANNER DECISION RULES (STRICT)
    ===============================================================================

    1. WHEN TO USE vector_db:
       - Category potentially triggers limits (meals, lodging, supplies).
       - The expense description is ambiguous.
       - Business justification is unclear.
       - When in doubt → TRUE.

    2. WHEN TO USE employee_profile:
       - Business purpose may depend on role, department, seniority.
       - Travel-related expenses.
       - Ambiguous merchant × category mapping.
       - When in doubt → TRUE.

    3. WHEN TO USE expense_history:
       - Checking for repeated submissions today.
       - Detecting split receipts.
       - Past submission pattern may affect reasonableness.
       - When in doubt → TRUE.

    ===============================================================================
    FAIL-SAFE MODE (NO GUESSING)
    ===============================================================================
    If ANY uncertainty occurs, you MUST output:
    {
      "vector_db": true,
      "employee_profile": true,
      "expense_history": true,
      "reason": "Defaulted to all tools due to uncertainty"
    }

    ===============================================================================
    OUTPUT EXAMPLES (DO NOT COPY LITERALLY)
    ===============================================================================
    Example 1:
    {
      "vector_db": true,
      "employee_profile": false,
      "expense_history": true,
      "reason": "Category requires limit validation and repeated submissions may matter"
    }

    Example 2:
    {
      "vector_db": true,
      "employee_profile": true,
      "expense_history": true,
      "reason": "Ambiguous expense details; all tools are required"
    }
    ===============================================================================
    """

    planner_inputs = [
        {"role": "system", "content": [{"type": "input_text", "text": planner_prompt}]},
        {"role": "user", "content": [
            {"type": "input_text",
             "text": json.dumps({"expense": expense, "receipt_summary": receipt_summary,
                                 "static_rule": rule, "static_decision": static_decision})}
        ]}
    ]

    try:
        planner_response = await client.responses.create(
            model="gpt-4o",
            input=planner_inputs
        )
        plan_raw = planner_response.output_text
        plan = json.loads(plan_raw)

        need_vdb = bool(plan.get("vector_db", True))
        need_profile = bool(plan.get("employee_profile", True))
        need_history = bool(plan.get("expense_history", True))

    except Exception as e:
        logger.error(f"[Planner] Failed → default: call everything. Error: {e}")
        need_vdb = need_profile = need_history = True

    # ============================================================
    # PHASE 2: Execute tools based on plan
    # ============================================================
    tools_results = {}

    # Vector DB
    if need_vdb:
        try:
            q = f"{expense['business_justification']} | {expense['category']} | {expense['amount']}"
            tools_results["policy_snippets"] = to_json_safe(query_vector_db(q, top_k=3))
        except Exception as e:
            tools_results["policy_snippets"] = {"error": str(e)}

    # Employee Profile
    if need_profile:
        try:
            from services.employee_service import get_employee
            tools_results["employee_profile"] = to_json_safe(
                get_employee(expense["employee_id"])
            )
        except Exception as e:
            tools_results["employee_profile"] = {"error": str(e)}

    # Expense History
    if need_history:
        try:
            tools_results["expense_history"] = to_json_safe(
                expense_repo.get_by_employee(expense["employee_id"])
            )
        except Exception as e:
            tools_results["expense_history"] = {"error": str(e)}

    # Normalize date
    expense_date = expense.get("date_of_expense")
    expense["date_of_expense"] = normalize_date_only(expense_date)

    # ============================================================
    # PHASE 3: Final Judgment LLM
    # ============================================================
    final_payload = {
        "expense": expense,
        "receipt_summary": receipt_summary,
        "static_rule": rule,
        "static_decision": static_decision,
        "tools_results": tools_results
    }

    final_prompt = f"""
You are the FINAL DECISION AGENT for the ExpenseSense system.

Your ONLY task is to analyze:
- the uploaded receipt image(s)
- submitted expense metadata
- static rules R1–R4
- optional tool results (policy_snippets, employee_profile, expense_history)

You MUST produce a STRICT JSON response that matches the required schema exactly.

You MUST follow ALL instructions below without exception.

===============================================================================
OUTPUT FORMAT (MANDATORY — STRICT JSON ONLY)
===============================================================================
You MUST respond with ONLY valid JSON:
- No prose
- No markdown
- No explanations
- No commentary
- No backticks
- No code fences
- No surrounding text
- No trailing commas
- No extra whitespace before or after

Your output MUST match this schema exactly:

Schema (ExpenseDecision):
{format_instructions}

Field rules:
- "decision": must be one of "APPROVE", "REJECT", or "MANUAL"
- "rule": a short identifier ("R1", "R2", "R3", "R4", "CONFLICT", "OCR") or null
- "reason": must be a concise human-readable explanation (1–2 short sentences)
- "confidence": float in [0, 1]

Additionally, the following optional fields MUST be included if available:
- merchant_name
- date_of_expense
- total_amount
- subtotal
- tax
- payment_method

===============================================================================
INFORMATION PROVIDED TO YOU
===============================================================================
Below is the data you will receive (as a Python dict):
- "expense": submitted metadata
- "receipt_summary": status of receipt extraction
- "static_rule" and "static_decision": results from rules R1–R4
- "tools_results": may contain:
      * "policy_snippets"
      * "employee_profile"
      * "expense_history"

You MUST use all available evidence.

===============================================================================
REIMBURSEMENT POLICY RULES (STRICT)
===============================================================================

----------------------------------------
1. Mandatory Receipt Requirements
----------------------------------------
A valid receipt MUST clearly show:
- vendor name 
- date
- itemized list of charges
- total amount
- taxes/fees if applicable
- must be readable and not cropped

If the receipt is missing essential fields, unreadable, corrupted, or contradicts 
the form:
→ decision = "REJECT", rule = "R4", confidence ≤ 0.75

You must check consistency between OCR-extracted fields and the submitted metadata:

- OCR total amount MUST match submitted total amount  
- OCR date MUST match submitted date (same day)
- OCR vendor name MUST logically match submitted merchant

If OCR cannot confidently extract these fields OR values appear ambiguous:
→ you MUST output:

→ decision = "REJECT", rule = "R4", confidence ≤ 0.75


----------------------------------------
2. Eligible Categories
----------------------------------------
- Travel (airfare, hotel, transportation, parking, tolls)
- Meals (business or travel meals)
- Conference (registration fees)
- Other (must be business-related)

----------------------------------------
3. Category Limits
----------------------------------------
- Meals: ≤ $120/day  
- Supplies: ≤ $200 per item  
- Hotels: ≤ $500/day  
- Conference: no limit
- Weekly total should not exceed $2,500 without manager review

If amounts exceed limits → MANUAL or REJECT

----------------------------------------
5. Rule R1 — Automatic Approval (≤ $500, First Request of Day)
----------------------------------------
Auto-approval ONLY IF ALL conditions hold:
1. Amount ≤ $500
2. First submission of employee on that calendar day
3. Receipt readable + valid
4. OCR matches metadata
5. Category is reimbursable
6. Policy retrieval shows no conflict
7. Expense appears reasonable

Reasonableness criteria:
- merchant matches category (e.g., Uber → travel)
- amount normal for category
- not unusually high or suspicious
- consistent with employee history

If borderline or uncertain → decision = "MANUAL"

----------------------------------------
6. Rule R2 — Frequency Violation (≤ $500 but NOT first request today)
----------------------------------------
If employee already submitted ANY request today:
→ additional ≤ $500 requests = REJECT or MANUAL
→ rule = "R2"

Detect patterns:
- repeated amounts
- repeated merchants
- back-to-back submissions
- possible “split receipts”

----------------------------------------
7. Rule R3 — Large Amount (> $500)
----------------------------------------
Any amount > $500:
→ ALWAYS MANUAL REVIEW
→ rule = "R3"

----------------------------------------
8. Rule R4 — Invalid Documentation
----------------------------------------
Missing or unreadable receipt, OCR mismatch:
→ REJECT
→ rule = "R4"

Note:
- R4 Date Mismatch Rule:
    * A mismatch between transaction_date, date_of_expense and reported_date is NOT grounds for rejection.
    * Reject ONLY IF:
         - the receipt date is missing.

When dates or amounts mismatch, you MUST explicitly state both values in the "reason".
For example:
"The amount 500.0 does not match the reported expense amount 390.0."

Do NOT use vague descriptions like "date mismatch" or "receipt inconsistent".
Always show the exact conflicting fields.

----------------------------------------
9. Conflict Resolution
----------------------------------------
If receipt contradicts metadata:
- trust the receipt image first
- set rule = "CONFLICT"
- decision = "MANUAL" or "REJECT" depending on severity

----------------------------------------
10. Fail-Safe (NO Hallucination)
----------------------------------------
If ANY uncertainty arises:
- DO NOT guess totals, vendors, or dates
- DO NOT infer absent information
- Prefer MANUAL instead of hallucinating
- confidence ≤ 0.75

===============================================================================
EXAMPLE VALID OUTPUT for REJECT (DO NOT COPY LITERALLY):
{{
  "decision": "REJECT",
  "rule": "R4",
  "reason": "Amount mismatch: submitted_amount=390.0, receipt_amount=10.0.",
  "confidence": "0.91",
  "merchant_name": "Starbucks",
  "date_of_expense": "2025-01-08",
  "total_amount": "12.45",
  "subtotal": "11.00",
  "tax": "1.45",
  "payment_method": "Visa 9264"
}}

EXAMPLE VALID OUTPUT for APPROVE (DO NOT COPY LITERALLY):
{{
  "decision": "APPROVE",
  "rule": "R1",
  "reason": "Receipt is valid and matches the submitted details (merchant, date, amount). The expense amount is within policy limits and the charge is reasonable for the stated business purpose, with no conflicting rules triggered."
  "confidence": 1.0,
  "merchant_name": "The American Society of Mechanical Engineers",
  "date_of_expense": "2025-04-22",
  "total_amount": "390.00",
  "subtotal": "390.00",
  "tax": "0.00",
  "payment_method": "Visa 9240"
}}
===============================================================================
    """

    # Prepare image
    image_b64 = None
    if isinstance(base64_img_list, list) and base64_img_list:
        image_b64 = base64_img_list[0]
    elif isinstance(base64_img_list, str):
        image_b64 = base64_img_list

    llm_inputs = [
        {"role": "system", "content": [{"type": "input_text", "text": final_prompt}]},
        {"role": "user", "content": [
            {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_b64}"},
            {"type": "input_text", "text": json.dumps(final_payload, indent=2)}
        ]}
    ]

    # -------- Call the LLM --------
    try:
        final_response = await client.responses.create(
            model="gpt-4o",
            input=llm_inputs
        )

        raw_str = final_response.output_text
        raw_dict = json.loads(raw_str)
        parsed = ExpenseDecision(**raw_dict)

    except Exception as e:
        logger.error(f"[Final Agent] JSON parse fail → fallback MANUAL. Error: {e}")

        parsed = ExpenseDecision(
            decision="MANUAL",
            rule="AI_PARSE_FAIL",
            reason=str(e),
            confidence=0
        )

    # ============================================================
    # Map to DB
    # ============================================================
    status_map = {
        "APPROVE": "approved",
        "REJECT": "rejected",
        "MANUAL": "admin_review"
    }
    status = status_map[parsed.decision]

    # Get old status before update
    old_status = expense.get("status", "pending")
    
    expense_repo.update(expense_id, {
        "status": status,
        "decision_actor": "AI",
        "decision_reason": f"{parsed.rule}: {parsed.reason}",
    })

    # Audit Log - status change
    from services.audit_log_service import log_expense_status_change
    log_expense_status_change(
        actor="AI",
        expense_id=expense_id,
        old_status=old_status,
        new_status=status,
        reason=f"{parsed.rule}: {parsed.reason}"
    )
    logger.info(f"[AI] Decision: {parsed.decision}, rule={parsed.rule}, reason={parsed.reason}")
    
    # ============================================================
    # Send Email Notification
    # ============================================================
    try:
        from services.employee_service import get_employee
        from services.agents.email_agent_service import email_agent
        from services.agents.a2a_protocol import A2ARequest, create_a2a_message
        
        # Get employee email
        emp_id = expense.get('employee_id')
        employee_data = get_employee(emp_id)
        
        if employee_data and employee_data.get('email'):
            employee_email = employee_data['email']
            
            # Create email notification request
            email_request = A2ARequest(
                capability_name="send_expense_notification",
                parameters={
                    "to": employee_email,
                    "expense_id": expense_id,
                    "status": status,
                    "amount": float(expense.get('amount', 0)),
                    "category": expense.get('category', 'N/A'),
                    "decision_reason": f"{parsed.rule}: {parsed.reason}"
                },
                context={"user_id": "system", "role": "system"}
            )
            
            # Send via A2A protocol
            message = create_a2a_message(
                sender_id="expense_agent",
                recipient_id="email_agent",
                message_type="request",
                payload=email_request.dict(),
                capability_name="send_expense_notification"
            )
            
            # Send email notification (await since we're in async context)
            response = await email_agent.process_message(
                message, 
                context={"user_id": "system", "role": "system"}
            )
            
            if response.message_type == "response":
                logger.info(f"[EMAIL] Notification sent successfully to {employee_email} for expense {expense_id}")
            else:
                logger.warning(f"[EMAIL] Notification failed: {response.payload.get('error')}")
        else:
            logger.warning(f"[EMAIL] Could not send notification - employee {emp_id} has no email")
            
    except Exception as e:
        # Don't fail the expense review if email fails
        logger.error(f"[EMAIL] Failed to send notification: {str(e)}", exc_info=True)
    
    # ============================================================
    # Update Bank Account Balance if Approved
    # ============================================================
    if status == "approved":
        try:
            from services import financial_service
            from services.audit_log_service import log_payment_event
            
            # Get employee to find their bank account
            emp_id = expense.get('employee_id')
            employee_data = get_employee(emp_id)
            
            if employee_data and employee_data.get('bank_account_id'):
                bank_account_id = employee_data['bank_account_id']
                expense_amount = float(expense.get('amount', 0))
                
                # Get current balance
                current_balance = financial_service.get_account_balance(bank_account_id)
                if current_balance is not None:
                    # Add expense amount to balance
                    new_balance = current_balance + expense_amount
                    financial_service.update_account_balance(bank_account_id, new_balance)
                    logger.info(f"[PAYMENT] Updated bank account {bank_account_id} balance: ${current_balance} -> ${new_balance} for expense {expense_id}")
                    
                    # Log payment event
                    log_payment_event(
                        expense_id=expense_id,
                        employee_id=emp_id,
                        amount=expense_amount,
                        bank_account_id=bank_account_id,
                        old_balance=current_balance,
                        new_balance=new_balance
                    )
                else:
                    logger.warning(f"[PAYMENT] Could not retrieve balance for bank account {bank_account_id}")
            else:
                logger.warning(f"[PAYMENT] Employee {emp_id} does not have a bank_account_id")
        except Exception as e:
            logger.error(f"[PAYMENT] Failed to update bank account balance: {str(e)}", exc_info=True)

    return parsed


# ============================================================
# Hook
# ============================================================
def auto_review_on_create(expense_id: str):
    """
    Synchronous wrapper that schedules async review in background.
    This is called from synchronous code paths.
    """
    import asyncio
    try:
        # Try to get the current event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an async context, create a task
            loop.create_task(evaluate_and_maybe_auto_approve(expense_id))
        except RuntimeError:
            # No event loop running, create a new one
            asyncio.run(evaluate_and_maybe_auto_approve(expense_id))
    except Exception as e:
        logger.error(f"[AUTO_REVIEW_ERROR] {e}", exc_info=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(evaluate_and_maybe_auto_approve("8fN76XaPhspd7KeaTum2"))

# ============================================================
# A2A Agent Implementation
# ============================================================
class ExpenseAgent(BaseAgent):
    """
    Expense Agent - Handles expense review and approval using AI
    """
    
    def __init__(self):
        super().__init__(
            agent_id="expense_agent",
            name="Expense Review Agent",
            description="AI-powered expense review and approval agent that validates receipts and applies policy rules"
        )
    
    def get_agent_card(self) -> AgentCard:
        """Return the agent's capability card"""
        return AgentCard(
            agent_id=self.agent_id,
            name=self.name,
            description=self.description,
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="review_expense",
                    description="Review an expense submission with AI-powered receipt analysis and policy validation",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "expense_id": {
                                "type": "string",
                                "description": "The ID of the expense to review"
                            }
                        },
                        "required": ["expense_id"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "decision": {
                                "type": "string",
                                "enum": ["APPROVE", "REJECT", "MANUAL"],
                                "description": "The review decision"
                            },
                            "rule": {
                                "type": "string",
                                "description": "The rule that was applied"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Explanation for the decision"
                            },
                            "confidence": {
                                "type": "number",
                                "description": "Confidence score (0-1)"
                            },
                            "merchant_name": {"type": "string"},
                            "date_of_expense": {"type": "string"},
                            "total_amount": {"type": "string"},
                            "subtotal": {"type": "string"},
                            "tax": {"type": "string"},
                            "payment_method": {"type": "string"}
                        }
                    }
                ),
                AgentCapability(
                    name="apply_static_rules",
                    description="Apply static policy rules to an expense (R1-R4)",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "expense": {
                                "type": "object",
                                "description": "The expense data"
                            },
                            "receipt_summary": {
                                "type": "string",
                                "description": "Summary of receipt status"
                            }
                        },
                        "required": ["expense", "receipt_summary"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "rule": {"type": "string"},
                            "decision": {"type": "string"}
                        }
                    }
                )
            ],
            metadata={
                "model": "gpt-4o",
                "supports_vision": True,
                "max_amount": 500,
                "policy_rules": ["R1", "R2", "R3", "R4"]
            }
        )
    
    async def handle_request(self, request: A2ARequest, context: Dict[str, Any]) -> A2AResponse:
        """Handle incoming A2A requests"""
        try:
            capability = request.capability_name
            params = request.parameters
            
            if capability == "review_expense":
                expense_id = params.get("expense_id")
                if not expense_id:
                    return A2AResponse(
                        success=False,
                        error="Missing required parameter: expense_id"
                    )
                
                # Run the expense review
                result = await evaluate_and_maybe_auto_approve(expense_id)
                
                return A2AResponse(
                    success=True,
                    result=result.dict(),
                    metadata={"expense_id": expense_id}
                )
            
            elif capability == "apply_static_rules":
                expense = params.get("expense")
                receipt_summary = params.get("receipt_summary")
                
                if not expense or not receipt_summary:
                    return A2AResponse(
                        success=False,
                        error="Missing required parameters: expense and receipt_summary"
                    )
                
                rule, decision = apply_static_rules(expense, receipt_summary)
                
                return A2AResponse(
                    success=True,
                    result={"rule": rule, "decision": decision}
                )
            
            else:
                return A2AResponse(
                    success=False,
                    error=f"Unknown capability: {capability}"
                )
                
        except Exception as e:
            logger.error(f"Error handling request in ExpenseAgent: {str(e)}", exc_info=True)
            return A2AResponse(
                success=False,
                error=str(e)
            )


# Create and register the expense agent
expense_agent = ExpenseAgent()
expense_agent.register()
