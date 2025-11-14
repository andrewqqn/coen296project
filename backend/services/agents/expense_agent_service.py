from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from typing import TypedDict, Optional
import base64


class ExpenseState(TypedDict):
    expense: dict
    file_bytes: bytes
    policy: str
    decision: Optional[dict]


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def extract_and_decide(state: ExpenseState):
    file_b64 = base64.b64encode(state["file_bytes"]).decode("utf-8")

    prompt = f"""
You are an Expense Review AI Agent.
Analyze the receipt and expense, then return strict JSON:
{{
  "decision": "approve" | "reject" | "manual_review",
  "reason": "...",
  "confidence": 0-1
}}
"""

    msg = [
        ("human", [
            {"type": "text", "text": prompt},
            {"type": "text", "text": f"Expense: {state['expense']}"},
            {"type": "text", "text": f"Policy: {state['policy']}"},
            {"type": "input_image", "image_url": f"data:image/png;base64,{file_b64}"}
        ])
    ]

    result = llm.invoke(msg)
    return {"decision": result.content}


def write_to_backend(state: ExpenseState):
    print("Writing decision to backend:", state["decision"])
    return {}
