# services/vector_db_service.py
from typing import List
import logging

from infrastructure.chroma_client import init_chroma_policy_client

logger = logging.getLogger(__name__)

def query_vector_db(query: str, top_k: int = 3) -> List[str]:
    if not query:
        return []

    client = init_chroma_policy_client()

    # Try query, if empty try to populate the collection from PDF and retry once
    for attempt in range(2):
        try:
            resp = client.query(query, top_k=top_k)
        except Exception as e:
            logger.warning(f"[VectorDB] Query failed, returning empty list. Error: {e}")
            return []

        # Chroma returns documents as a list-of-lists when querying a single embedding
        docs = resp.get("documents") if isinstance(resp, dict) else resp or []
        if not docs:
            docs = []

        # Normalize to a single list of documents
        rows = []
        if docs:
            first = docs[0]
            if isinstance(first, list):
                rows = first
            elif isinstance(docs, list):
                # docs may already be a flat list
                rows = docs

        if rows:
            snippets: List[str] = [str(d) for d in rows[:top_k] if d]
            return snippets

        # If no rows and this is the first attempt, try to populate the collection and retry
        if attempt == 0:
            try:
                inserted = client.store_policy_pdf()
                logger.info(f"[VectorDB] Collection was empty — inserted {inserted} chunks and will retry query")
            except Exception as e:
                logger.warning(f"[VectorDB] Failed to populate collection: {e}")
                break

    return []
