import json
import base64
import logging
from io import BytesIO
from datetime import datetime, timezone
from typing import Optional, Literal, List, Any, cast

from pdf2image import convert_from_bytes
from dateutil import parser
from pydantic import BaseModel
from langchain_core.output_parsers import JsonOutputParser
from openai import OpenAI
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds

import domain.repositories.expense_repo as expense_repo
from services.document_service import download_receipt
from services.vector_db_service import query_vector_db
from services.audit_log_service import create_log
from services.employee_service import get_employee
# ============================================================
# Logger
# ============================================================
logger = logging.getLogger("expense_agent")
logger.setLevel(logging.INFO)

client = OpenAI()


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
    if amount > 500:
        return "R3", "MANUAL"

    # R2 – already submitted today → MANUAL
    if amount <= 500 and len(today_exp) > 1:
        return "R2", "MANUAL"

    # R1 – safe approve
    return "R1", "APPROVE"

# ============================================================
# AI Review Logic
# ============================================================

def evaluate_and_maybe_auto_approve(expense_id: str):
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
        planner_response = client.responses.create(
            model="gpt-4o-mini",
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
1. Receipt Requirements
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

OCR consistency checks:
- OCR amount MUST match submitted amount
If these cannot be confidently extracted:
→ decision = "MANUAL", rule = "OCR"

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
        save_base64_to_jpeg(image_b64, "page1.jpg")
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
        final_response = client.responses.create(
            model="gpt-4o-mini",
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
        "MANUAL": "admin-review"
    }
    status = status_map[parsed.decision]

    expense_repo.update(expense_id, {
        "status": status,
        "decision_actor": "AI",
        "decision_reason": f"{parsed.rule}: {parsed.reason}",
    })

    # Audit Log
    create_log({
        "actor": "AI",
        "expense_id": expense_id,
        "log": f"{parsed.decision}, rule={parsed.rule}, reason={parsed.reason}",
    })
    logger.info(f"[AI] Decision: {parsed.decision}, rule={parsed.rule}, reason={parsed.reason}")

    return parsed


# ============================================================
# Hook
# ============================================================
def auto_review_on_create(expense_id: str):
    try:
        evaluate_and_maybe_auto_approve(expense_id)
    except Exception as e:
        logger.error(f"[AUTO_REVIEW_ERROR] {e}")

if __name__ == "__main__":
    evaluate_and_maybe_auto_approve("8fN76XaPhspd7KeaTum2")