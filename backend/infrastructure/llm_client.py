import os, openai
from utils.logger import get_logger
logger = get_logger(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY", "")

def run_llm_prompt(prompt: str):
    if not openai.api_key:
        return f"[Mock] Reviewed: {prompt[:80]}..."
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content

def run_llm_prompt_with_cheap_model(prompt: str):
    if not openai.api_key:
        return f"[Mock] Reviewed: {prompt[:80]}..."
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content

def run_llm_prompt_with_expensive_model(prompt: str):
    if not openai.api_key:
        return f"[Mock] Reviewed: {prompt[:80]}..."
    resp = openai.chat.completions.create(
        model="gpt-5o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content
