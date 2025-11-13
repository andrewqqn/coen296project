from infrastructure.llm_client import run_llm_prompt

def ai_review_expense(expense_data: dict):
    prompt = f"Analyze this expense and decide if it should be approved:\n{expense_data}"
    result = run_llm_prompt(prompt)
    return {"decision": "approved" if "approve" in result.lower() else "flagged", "ai_reason": result}
