"""
Document Management Agent
Capabilities:
1. Drive API Integration
2. File Retrieval and Upload
3. File Searching and Filtering
4. Vector DB Integration (RAG)
"""

import os
import time
import uuid
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


#Data model
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

#Drive Adapter
class DriveAdapter:
    """Abstract adapter to connect with Google Drive / OneDrive"""
    def list_files(self, query: Optional[str] = None, max_results: int = 10) -> List[Document]:
        raise NotImplementedError

    def get_file(self, file_id: str) -> Document:
        raise NotImplementedError

    def download_file(self, file_id: str, destination: str) -> None:
        raise NotImplementedError

    def upload_file(self, file_path: str, folder_id: Optional[str] = None) -> Document:
        raise NotImplementedError


#Mock placeholder (needs updating for final)
class MockDriveAdapter(DriveAdapter):
    #Simulated Drive adapter for testing
    def __init__(self):
        self.files: Dict[str, Document] = {}

    def list_files(self, query: Optional[str] = None, max_results: int = 10) -> List[Document]:
        files = list(self.files.values())
        if query:
            files = [f for f in files if query.lower() in f.name.lower()]
        return files[:max_results]

    def get_file(self, file_id: str) -> Document:
        return self.files.get(file_id)

    def download_file(self, file_id: str, destination: str) -> None:
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
            drive_url=f"https://drive.google.com/file/d/{doc_id}"
        )
        self.files[doc_id] = doc
        return doc


#Vector Database
class VectorDBAdapter:
    """Stores embeddings for RAG-style search"""
    def __init__(self):
        self.index: Dict[str, Dict[str, Any]] = {}

    def index_document(self, doc: Document, embedding: List[float]):
        self.index[doc.id] = {"metadata": doc, "embedding": embedding}

    def search_similar(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.index:
            return []
        # sort by cosine similarity
        results = sorted(
            self.index.values(),
            key=lambda d: -self._cosine_similarity(d["embedding"], query_embedding)
        )
        return results[:top_k]

    def _cosine_similarity(self, a, b):
        dot = sum(x*y for x, y in zip(a,b))
        norm_a = sum(x*x for x in a) ** 0.5
        norm_b = sum(y*y for y in b) ** 0.5
        return dot / (norm_a*norm_b + 1e-9)


#Document Agent
class DocumentAgent:
    #Fullfills all required functionalities
    def __init__(self, drive_adapter: DriveAdapter, vector_db: VectorDBAdapter):
        self.drive_adapter = drive_adapter
        self.vector_db = vector_db

    # File operations
    def upload_file(self, file_path: str, folder_id: Optional[str] = None) -> Document:
        doc = self.drive_adapter.upload_file(file_path, folder_id)
        # placeholder embedding
        self.vector_db.index_document(doc, [0.1, 0.2, 0.3])
        return doc

    def download_file(self, file_id: str, destination: str):
        self.drive_adapter.download_file(file_id, destination)

    # File searching
    def keyword_search(self, query: str, max_results: int = 5) -> List[Document]:
        return self.drive_adapter.list_files(query, max_results)

    def semantic_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        return self.vector_db.search_similar(query_embedding, top_k)
