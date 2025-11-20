import json
import logging
from datetime import datetime, timezone
from typing import Optional, Literal
from io import BytesIO

from pdf2image import convert_from_bytes
from PIL import Image

from pydantic import BaseModel
from langchain_core.output_parsers import JsonOutputParser
from openai import OpenAI
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds

from repositories import expense_repo, audit_log_repo
from services.document_service import download_receipt
from services.vector_db_service import query_vector_db


# ============================================================
# Logger
# ============================================================
logger = logging.getLogger("expense_agent")
logger.setLevel(logging.INFO)

client = OpenAI()


# ============================================================
# JSON-safe converter
# ============================================================
def to_json_safe(obj):
    if isinstance(obj, (datetime, DatetimeWithNanoseconds)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_json_safe(v) for v in obj]
    return obj


# ============================================================
# Decision Schema
# ============================================================
class ExpenseDecision(BaseModel):
    decision: Literal["APPROVE", "REJECT", "MANUAL"]
    rule: Optional[str] = None
    reason: str
    confidence: float


parser = JsonOutputParser(pydantic_object=ExpenseDecision)
format_instructions = parser.get_format_instructions()


# ============================================================
# Convert PDF to JPEG for OpenAI
# ============================================================
def pdf_to_jpeg_bytes(pdf_bytes: bytes) -> bytes:
    try:
        pages = convert_from_bytes(pdf_bytes, dpi=150)
        img = pages[0]  # only first page
        buf = BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()
    except Exception as e:
        logger.error(f"PDF → JPEG conversion failed: {e}")
        return None


# ============================================================
# Static rules R1–R4
# ============================================================
def apply_static_rules(expense, receipt_summary):
    amount = float(expense["amount"])
    today = datetime.now(timezone.utc).date()

    all_exp = expense_repo.get_by_employee(expense["employee_id"])
    all_exp = to_json_safe(all_exp)

    today_exp = [
        e for e in all_exp
        if datetime.fromisoformat(e["submitted_at"]).date() == today
    ]

    if "no receipt" in receipt_summary.lower():
        return "R4", "REJECT"

    if amount > 500:
        return "R3", "MANUAL"

    if amount <= 500 and len(today_exp) >= 1:
        return "R2", "REJECT"

    return "R1", "APPROVE"


# ============================================================
# AI Review Logic
# ============================================================
def evaluate_and_maybe_auto_approve(expense_id: str):
    logger.info(f"[AI] Reviewing expense_id={expense_id}")

    expense = expense_repo.get(expense_id)
    expense = to_json_safe(expense)

    # ----------- Load receipt -------------
    jpeg_bytes = None
    receipt_summary = "(no receipt provided)"

    try:
        if expense.get("receipt_path"):
            pdf_bytes = download_receipt(expense["receipt_path"])
            jpeg_bytes = pdf_to_jpeg_bytes(pdf_bytes)

            if jpeg_bytes:
                receipt_summary = "receipt_image_attached"
            else:
                receipt_summary = "(receipt unreadable)"
        else:
            receipt_summary = "(no receipt provided)"
    except Exception as e:
        receipt_summary = f"(download failed: {e})"

    # ----------- Static Rules ----------
    rule, static_decision = apply_static_rules(expense, receipt_summary)

    # ----------- Vector DB Policy -------
    q = f"{expense['business_justification']} | {expense['category']} | {expense['amount']}"
    snippets = query_vector_db(q)

    # ----------- LLM prompt ----------
    messages = [
        {
            "role": "system",
            "content": f"""
You are an AI Expense Reviewer.
Return ONLY JSON:
{format_instructions}

StaticRule={rule}
        """
        }
    ]

    if jpeg_bytes:
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "input_image",
                    "image": jpeg_bytes
                },
                {
                    "type": "text",
                    "text": json.dumps({
                        "expense": expense,
                        "receipt_summary": receipt_summary,
                        "policy_snippets": snippets
                    })
                }
            ]
        })
    else:
        messages.append({
            "role": "user",
            "content": json.dumps({
                "expense": expense,
                "receipt_summary": receipt_summary,
                "policy_snippets": snippets
            })
        })

    # ----------- AI Call --------------
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",   # use a JSON-capable model
            messages=messages
        )

        raw = response.choices[0].message.content
        parsed = parser.parse(raw)

    except Exception as e:
        logger.error(f"[AI] JSON parse failed → manual. Error: {e}")
        parsed = ExpenseDecision(
            decision="MANUAL",
            rule="AI_PARSE_FAIL",
            reason=str(e),
            confidence=0
        )

    # ----------- Update DB ----------
    status_map = {
        "APPROVE": "approved",
        "REJECT": "rejected",
        "MANUAL": "admin-review"
    }

    status = status_map[parsed.decision]

    update_data = {
        "status": status,
        "decision_actor": "AI",
        "decision_reason": f"{parsed.rule}: {parsed.reason}",
        "updated_at": datetime.utcnow().isoformat()
    }

    expense_repo.update(expense_id, update_data)

    # ----------- Audit Log ----------
    audit_log_repo.create({
        "actor": "AI",
        "expense_id": expense_id,
        "log": f"{parsed.decision}, rule={parsed.rule}, reason={parsed.reason}",
        "timestamp": datetime.utcnow().isoformat()
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

if __name__ == "__main__":
    auto_review_on_create("123456789")