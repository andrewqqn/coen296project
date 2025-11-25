"""
Chroma Policy Vector DB Client (Production Grade)
-------------------------------------------------

Features:
- FREE embedding using sentence-transformers/all-mpnet-base-v2
- Persistent ChromaDB store (Cloud Run / local 都稳定)
- 自动维度检查 & 维度不一致时重建 collection
- 将 PDF policy 切 chunk 后写入向量库
- 对外提供 query() 返回 top-k 相关 policy 片段
"""

import logging
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

import chromadb
from chromadb.config import Settings

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PDF_PATH = BASE_DIR / "static" / "ExpenSense_Reimbursement_Policy.pdf"


# -----------------------------------------------------------
# Utility: Simple chunker with overlap
# -----------------------------------------------------------
def _chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 150) -> List[str]:
    if not text:
        return []
    step = max(1, chunk_size - chunk_overlap)
    return [text[i : i + chunk_size] for i in range(0, len(text), step)]


# -----------------------------------------------------------
# Main Client
# -----------------------------------------------------------
class ChromaPolicyClient:

    def __init__(
        self,
        collection_name: str = "reimbursement_policy",
        pdf_path: Optional[Path] = None,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        persist_dir: str = ".chroma_store",  # persistent directory
    ):
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.pdf_path = Path(pdf_path) if pdf_path else DEFAULT_PDF_PATH

        # FREE, high-quality semantic embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={"device": "cpu"},  # Cloud Run safe
            encode_kwargs={"normalize_embeddings": True},
        )

        # Persistent Chroma
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(allow_reset=True),
        )

        self.collection = None

    # -------------------------------------------------------
    # Get or create collection (with auto dimension check)
    # -------------------------------------------------------
    def get_or_create_collection(self):
        if self.collection is not None:
            return self.collection

        # 先拿 / 创建 collection
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception:
            self.collection = self.client.create_collection(name=self.collection_name)

        try:
            existing = self.collection.get(include=["embeddings"])
            embs = existing.get("embeddings") if isinstance(existing, dict) else None

            # embs 的形状为 List[List[float]] 或 None
            if embs is not None and len(embs) > 0:
                stored_dim = len(embs[0])
                current_vec = self.embeddings.embed_query("dimension check")
                current_dim = len(current_vec)

                if stored_dim != current_dim:
                    print("⚠ Dimension mismatch detected → resetting collection…")
                    self.client.delete_collection(self.collection_name)
                    self.collection = self.client.create_collection(
                        name=self.collection_name
                    )
        except Exception as e:
            print("⚠ Warning during dimension check:", e)

        return self.collection

    # -------------------------------------------------------
    # Store PDF into ChromaDB
    # -------------------------------------------------------
    def store_policy_pdf(self) -> int:
        """
        读取 reimbursement policy PDF，切 chunk 后写入 Chroma。
        返回写入的 chunk 数量。
        """
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"Policy PDF not found: {self.pdf_path}")

        loader = PyPDFLoader(str(self.pdf_path))
        docs = loader.load()

        chunks: List[str] = []
        metadatas: List[dict] = []

        for page_idx, doc in enumerate(docs):
            text = getattr(doc, "page_content", "") or ""
            page_chunks = _chunk_text(text, self.chunk_size, self.chunk_overlap)

            for i, chunk in enumerate(page_chunks):
                chunks.append(chunk)
                metadatas.append(
                    {
                        "source": str(self.pdf_path),
                        "page": page_idx + 1,
                        "chunk_index": i,
                    }
                )

        if not chunks:
            logger.warning("No chunks extracted from PDF")
            return 0

        # Compute embeddings
        embeddings = self.embeddings.embed_documents(chunks)

        # Save to Chroma
        collection = self.get_or_create_collection()
        ids = [str(uuid4()) for _ in chunks]

        collection.add(
            ids=ids,
            documents=chunks,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        logger.info(f"Inserted {len(chunks)} chunks into '{self.collection_name}'")
        return len(chunks)

    # -------------------------------------------------------
    # Query top-k snippets
    # -------------------------------------------------------
    def query(self, text: str, top_k: int = 3):
        collection = self.get_or_create_collection()
        query_embedding = self.embeddings.embed_query(text)

        return collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )


# -----------------------------------------------------------
# Module-level helper (singleton client)
# -----------------------------------------------------------
_default_client: Optional[ChromaPolicyClient] = None


def init_chroma_policy_client(pdf_path: Optional[Path] = None) -> ChromaPolicyClient:
    global _default_client
    if _default_client is None:
        _default_client = ChromaPolicyClient(pdf_path=pdf_path)
    return _default_client


def store_policy_to_chroma(pdf_path: Optional[Path] = None) -> int:
    client = init_chroma_policy_client(pdf_path)
    return client.store_policy_pdf()
