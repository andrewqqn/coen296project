# services/vector_db_service.py
from typing import List
from infrastructure.chroma_client import init_chroma_policy_client

def query_vector_db(query: str, top_k: int = 3) -> List[str]:
    client = init_chroma_policy_client()
    col = client._get_or_create_collection()

    # embed query
    try:
        emb = client.embeddings.embed_query(query)
    except Exception:
        emb = None

    # vector search
    resp = (
        col.query(query_embeddings=[emb], n_results=top_k, include=["documents"])
        if emb is not None
        else col.query(query_texts=[query], n_results=top_k, include=["documents"])
    )

    docs = resp.get("documents") or [[]]
    docs = docs[0] if isinstance(docs[0], list) else docs

    return docs[:top_k]
