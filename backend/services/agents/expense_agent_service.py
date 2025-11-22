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

    # -------- Query Vector DB --------
    q = f"{expense['business_justification']} | {expense['category']} | {expense['amount']}"
    snippets = to_json_safe(query_vector_db(q, top_k=3))

    # -------- Prompt Payload --------
    expense_date = expense.get('date_of_expense')
    expense['date_of_expense'] = normalize_date_only(expense_date)

    payload = to_json_safe({
        "expense": expense,
        "receipt_summary": receipt_summary,
        "policy_snippets": snippets,
        "static_rule": rule,
        "static_decision": static_decision
    })

    system_prompt = f"""
You are an AI Expense Reviewer for the ExpenseSense system. 

Your ONLY task is to analyze the uploaded receipt image(s), compare them with the 
submitted expense metadata and policy rules, and produce a STRICT JSON response 
that matches the required schema exactly.

You MUST follow ALL instructions below.

===============================================================================
OUTPUT FORMAT (MANDATORY)
===============================================================================
You MUST respond with ONLY valid JSON:
- No prose
- No markdown
- No explanations
- No commentary
- No backticks
- No extra whitespace before/after
- No unexpected keys
- No trailing commas

Your output MUST match this schema exactly:

Schema (ExpenseDecision):
{format_instructions}

Field rules:
- "decision": one of "APPROVE", "REJECT", "MANUAL"
- "rule": a short string identifier (e.g., "R1", "R2", "R3", "R4", "CONFLICT") or null
- "reason": concise human-readable explanation (1–2 short sentences max)
- "confidence": float in [0, 1]

===============================================================================
REIMBURSEMENT POLICY SUMMARY (STRICT RULES TO FOLLOW)
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

    # -------- AI Call --------
    try:
        # If pdf_to_base64 returned a list of page images, use the first page only
        image_b64 = None
        if isinstance(base64_img_list, list) and len(base64_img_list) > 0:
            image_b64 = base64_img_list[0]
            save_base64_to_jpeg(image_b64, "page1.jpg")
        elif isinstance(base64_img_list, str):
            image_b64 = base64_img_list

        # Build the user message with the payload as compact JSON
        expense_prompt = f"""
        The receipt image(s) for this expense are provided separately above as input_image content.

        Below are the structured details of the expense, extracted metadata,
        policy retrieval context, and pre-evaluated static rules:

        Expense details (JSON-safe structure):
        {json.dumps(payload, indent=2)}
        """

        inputs = [
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": [
                {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_b64}"},
                {"type": "input_text", "text": expense_prompt},
            ]}
        ]
        response = client.responses.create(
            model="gpt-4o-mini",
            input=inputs
        )

        print(response.output_text)
        raw_str = response.output_text
        raw_dict = json.loads(raw_str)
        parsed = ExpenseDecision(**raw_dict)

    except Exception as e:
        logger.error(f"[AI] JSON parse failed → fallback to MANUAL. Error: {e}")

        parsed = ExpenseDecision(
            decision="MANUAL",
            rule="AI_PARSE_FAIL",
            reason=str(e),
            confidence=0
        )

    # -------- Map Decision → DB Status --------
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

    # -------- Audit Log --------
    create_log({
        "actor": "AI",
        "expense_id": expense_id,
        "log": f"{parsed.decision}, rule={parsed.rule}, reason={parsed.reason}",
    })

    return parsed



# ============================================================
# Hook
# ============================================================
def auto_review_on_create(expense_id: str):
    try:
        evaluate_and_maybe_auto_approve(expense_id)
    except Exception as e:
        logger.error(f"[AUTO_REVIEW_ERROR] {e}")
