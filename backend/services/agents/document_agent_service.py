from infrastructure.llm_client import run_llm_prompt

def extract_receipt_info(receipt_text: str):
    prompt = f"Extract vendor, total, date from this receipt text:\n{receipt_text}"
    parsed = run_llm_prompt(prompt)
    return {"parsed_info": parsed}
