from pathlib import Path
from typing import List, Optional
import logging
from uuid import uuid4

try:
    import chromadb
except Exception:
    chromadb = None  # allow static analysis and import-time safety

from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader

logger = logging.getLogger(__name__)

# Default PDF path (absolute to the workspace) — will be used when callers don't pass one.
DEFAULT_PDF_PATH = Path("/Users/yulinzeng/PycharmProjects/coen296project/backend/static/ExpenSense_Reimbursement_Policy_.pdf")


def _chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 150) -> List[str]:
    """Simple text chunker with overlap."""
    if not text:
        return []
    step = max(1, chunk_size - chunk_overlap)
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), step)]
    return chunks


class ChromaPolicyClient:
    """Client to store and query the reimbursement policy in a Chroma collection.

    This class will:
    - create or get a Chroma collection named `reimbursement_policy`
    - extract text from the policy PDF
    - chunk the text into pieces
    - compute embeddings via OpenAIEmbeddings
    - add the documents, metadatas, and embeddings to the Chroma collection
    """

    def __init__(
        self,
        collection_name: str = "reimbursement_policy",
        pdf_path: Optional[Path] = None,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
    ):
        self.collection_name = collection_name
        self.chunk_size = int(chunk_size)
        self.chunk_overlap = int(chunk_overlap)
        self.pdf_path = Path(pdf_path) if pdf_path is not None else DEFAULT_PDF_PATH

        # embedding model
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        # chromadb client and collection are created lazily
        self.client = None
        self.collection = None

    def _ensure_client(self):
        if self.client is not None:
            return
        if chromadb is None:
            raise RuntimeError("chromadb package is not available. Install chromadb to use ChromaPolicyClient.")

        # create a chromadb client
        try:
            self.client = chromadb.Client()
        except TypeError:
            # Different versions of chromadb may require config; try default constructor
            self.client = chromadb.Client()

    def _get_or_create_collection(self):
        if self.collection is not None:
            return self.collection

        self._ensure_client()

        # try create_collection with get_or_create flag if available
        try:
            # some chromadb versions support get_or_create parameter
            self.collection = self.client.create_collection(name=self.collection_name, get_or_create=True)
            return self.collection
        except TypeError:
            # signature doesn't accept get_or_create
            pass
        except Exception:
            # fall through to other attempts
            pass

        # try to get existing collection
        try:
            self.collection = self.client.get_collection(self.collection_name)
            return self.collection
        except Exception:
            pass

        # fallback: create collection without get_or_create
        try:
            self.collection = self.client.create_collection(name=self.collection_name)
            return self.collection
        except Exception as e:
            raise RuntimeError(f"Failed to create or get Chroma collection '{self.collection_name}': {e}")

    def store_policy_pdf(self) -> int:
        """Load the policy PDF, chunk it, embed the chunks, and insert into Chroma.

        Returns the number of chunks added.
        """
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"Policy PDF not found at {self.pdf_path}")

        # load pdf pages into Document-like objects using LangChain's loader
        loader = PyPDFLoader(str(self.pdf_path))
        documents = loader.load()

        # collect chunks and metadatas
        chunks: List[str] = []
        metadatas: List[dict] = []

        for page_idx, doc in enumerate(documents):
            text = getattr(doc, "page_content", "") or ""
            page_chunks = _chunk_text(text, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
            for i, chunk in enumerate(page_chunks):
                chunks.append(chunk)
                metadatas.append({"source": str(self.pdf_path), "page": page_idx + 1, "chunk_index": i})

        if not chunks:
            logger.info("No text chunks were extracted from the PDF.")
            return 0

        # compute embeddings for chunks
        try:
            embeddings = self.embeddings.embed_documents(chunks)
        except AttributeError:
            # Some embedding clients expose a different method name; try embed_texts
            embeddings = getattr(self.embeddings, "embed_texts", lambda x: None)(chunks)

        # ensure collection exists
        collection = self._get_or_create_collection()

        # prepare ids
        ids = [str(uuid4()) for _ in chunks]

        # The Chroma collection.add signature varies between versions. Try the common forms.
        try:
            # preferred: provide embeddings explicitly
            collection.add(ids=ids, documents=chunks, metadatas=metadatas, embeddings=embeddings)
        except TypeError:
            # some versions use 'documents' named arg only
            try:
                collection.add(documents=chunks, metadatas=metadatas, ids=ids)
            except Exception as e:
                raise RuntimeError(f"Failed to add documents to Chroma collection: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to add documents to Chroma collection: {e}")

        logger.info(f"Inserted {len(chunks)} chunks into Chroma collection '{self.collection_name}'")
        return len(chunks)


# module-level helper functions for convenience
_default_client: Optional[ChromaPolicyClient] = None


def init_chroma_policy_client(pdf_path: Optional[str] = None) -> ChromaPolicyClient:
    global _default_client
    if _default_client is None:
        _default_client = ChromaPolicyClient(pdf_path=Path(pdf_path) if pdf_path else DEFAULT_PDF_PATH)
    return _default_client


def store_policy_to_chroma(pdf_path: Optional[str] = None) -> int:
    """Convenience function to store the configured policy PDF into the collection."""
    client = init_chroma_policy_client(pdf_path)
    return client.store_policy_pdf()
