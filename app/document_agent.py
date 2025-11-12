"""
Document Management Agent
-------------------------
RAG-supported agent for searching and managing files in cloud storage.
Supports:
- Drive API integration (Google Drive, OneDrive)
- File retrieval and upload
- File searching and filtering
- Vector DB integration for semantic (RAG) search
"""

import os
import json
import time
import uuid
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Callable


# =====================================
# ========== DATA MODELS ==============
# =====================================

@dataclass
class Document:
    id: str
    name: str
    mime_type: str
    created_time: str
    modified_time: str
    size: Optional[int]
    drive_url: Optional[str]
    content_preview: Optional[str] = None


# =====================================
# ========== EVENT BUS ================
# =====================================

class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def subscribe(self, event_name: str, handler: Callable[[Dict[str, Any]], None]):
        self.subscribers.setdefault(event_name, []).append(handler)

    def publish(self, event_name: str, payload: Dict[str, Any]):
        print(f"[EventBus] Publishing: {event_name} -> {json.dumps(payload, default=str)}")
        handlers = self.subscribers.get(event_name, [])
        for h in handlers:
            try:
                h(payload)
            except Exception as e:
                print(f"[EventBus] Handler error for {event_name}: {e}")


# =====================================
# ===== DRIVE API INTEGRATION =========
# =====================================

class DriveAdapter:
    """
    Abstract adapter to connect with Google Drive, OneDrive, etc.
    """

    def list_files(self, query: Optional[str] = None, max_results: int = 10) -> List[Document]:
        raise NotImplementedError

    def get_file(self, file_id: str) -> Document:
        raise NotImplementedError

    def download_file(self, file_id: str, destination: str) -> None:
        raise NotImplementedError

    def upload_file(self, file_path: str, folder_id: Optional[str] = None) -> Document:
        raise NotImplementedError


# ---- PLACEHOLDER IMPLEMENTATION ----
class MockDriveAdapter(DriveAdapter):
    """
    Placeholder adapter until real Google Drive / OneDrive API is integrated.
    """

    def __init__(self):
        self.files: Dict[str, Document] = {}

    def list_files(self, query: Optional[str] = None, max_results: int = 10) -> List[Document]:
        print(f"[MockDriveAdapter] Listing files with query='{query}'")
        files = list(self.files.values())
        if query:
            files = [f for f in files if query.lower() in f.name.lower()]
        return files[:max_results]

    def get_file(self, file_id: str) -> Document:
        print(f"[MockDriveAdapter] Getting file {file_id}")
        return self.files.get(file_id)

    def download_file(self, file_id: str, destination: str) -> None:
        print(f"[MockDriveAdapter] Downloading file {file_id} to {destination}")
        # simulate writing content
        with open(destination, "w") as f:
            f.write("Simulated file content from Drive.\n")

    def upload_file(self, file_path: str, folder_id: Optional[str] = None) -> Document:
        doc_id = str(uuid.uuid4())
        name = os.path.basename(file_path)
        doc = Document(
            id=doc_id,
            name=name,
            mime_type="application/pdf",
            created_time=time.strftime("%Y-%m-%d %H:%M:%S"),
            modified_time=time.strftime("%Y-%m-%d %H:%M:%S"),
            size=1024,
            drive_url=f"https://drive.google.com/file/d/{doc_id}",
        )
        self.files[doc_id] = doc
        print(f"[MockDriveAdapter] Uploaded file: {name}")
        return doc


# =====================================
# ======= VECTOR DB INTEGRATION =======
# =====================================

class VectorDBAdapter:
    """
    Handles semantic indexing and retrieval for RAG-based search.
    """

    def __init__(self):
        self.index: Dict[str, Dict[str, Any]] = {}

    def index_document(self, doc: Document, embedding: List[float]):
        self.index[doc.id] = {"metadata": asdict(doc), "embedding": embedding}
        print(f"[VectorDB] Indexed document: {doc.name}")

    def search_similar(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.index:
            print("[VectorDB] No documents indexed.")
            return []
        results = sorted(
            self.index.values(),
            key=lambda d: -self._cosine_similarity(d["embedding"], query_embedding)
        )
        return results[:top_k]

    def _cosine_similarity(self, a, b):
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5
        return dot / (norm_a * norm_b + 1e-9)


# =====================================
# ======= DOCUMENT SEARCH ENGINE ======
# =====================================

class DocumentSearchEngine:
    def __init__(self, drive_adapter: DriveAdapter, vector_db: VectorDBAdapter):
        self.drive_adapter = drive_adapter
        self.vector_db = vector_db

    def keyword_search(self, keywords: str, max_results: int = 5) -> List[Document]:
        print(f"[DocSearch] Searching Drive for keywords: '{keywords}'")
        query = keywords
        return self.drive_adapter.list_files(query=query, max_results=max_results)

    def semantic_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        print(f"[DocSearch] Performing semantic search using vector DB...")
        return self.vector_db.search_similar(query_embedding, top_k=top_k)


# =====================================
# ========== MAIN AGENT ===============
# =====================================

class DocumentAgent:
    """
    Core agent that orchestrates file management and retrieval.
    Supports:
    - File upload/download
    - Keyword search
    - Semantic (RAG) search
    """

    def __init__(self, drive_adapter: DriveAdapter, vector_db: VectorDBAdapter, event_bus: EventBus):
        self.drive_adapter = drive_adapter
        self.vector_db = vector_db
        self.event_bus = event_bus
        self.search_engine = DocumentSearchEngine(drive_adapter, vector_db)

    # ---- File Operations ----

    def handle_upload(self, file_path: str, folder_id: Optional[str] = None):
        doc = self.drive_adapter.upload_file(file_path, folder_id)
        # TODO: Generate embedding when RAG integrated
        fake_embedding = [0.1, 0.2, 0.3]
        self.vector_db.index_document(doc, fake_embedding)
        self.event_bus.publish("document.uploaded", asdict(doc))
        return doc

    def handle_download(self, file_id: str, destination: str):
        self.drive_adapter.download_file(file_id, destination)
        self.event_bus.publish("document.downloaded", {"file_id": file_id, "destination": destination})

    # ---- Search Operations ----

    def handle_keyword_search(self, query: str, max_results: int = 5):
        results = self.search_engine.keyword_search(query, max_results)
        self.event_bus.publish("document.search.keyword", {"query": query, "results": [asdict(r) for r in results]})
        return results

    def handle_semantic_search(self, query_embedding: List[float], top_k: int = 5):
        results = self.search_engine.semantic_search(query_embedding, top_k)
        self.event_bus.publish("document.search.semantic", {"results": results})
        return results

    # ---- Indexing ----

    def index_new_document(self, doc: Document, embedding: List[float]):
        self.vector_db.index_document(doc, embedding)
        self.event_bus.publish("document.indexed", asdict(doc))

