import logging
from typing import List
import openai
import os
logger = logging.getLogger("vector_db")



def query_vector_db(query: str, top_k: int = 3) -> List[str]:
    """
    Equivalent behavior to the old Chroma version, but using
    OpenAI Vector Store /search endpoint.

    Returns List[str]: top-k text chunks.
    """
    client = openai.OpenAI()
    VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID")

    if not query:
        return []

    try:
        resp = client.vector_stores.search(
            vector_store_id=VECTOR_STORE_ID,
            query=query,
            max_num_results=top_k,
            rewrite_query=False,
        )
    except Exception as e:
        logger.warning(f"[VectorDB] OpenAI search failed: {e}")
        return []

    if not resp or not getattr(resp, "data", None):
        return []

    snippets: List[str] = []

    for item in resp.data[:top_k]:
        for block in item.content:
            if block.type == "text" and block.text:
                snippets.append(block.text)
                break
    return snippets