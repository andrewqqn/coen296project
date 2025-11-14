Final Version may instead use FireBase api instead of google drive

# 🗂️ Document Management Agent

The **Document Management Agent** is part of a **multi-agent expense management system**.  
It handles documents in cloud environments (mocked for now) with **upload, download, keyword search, and semantic search (RAG)** capabilities.

---

## 🚀 Overview

This agent provides core document management functionality:

- **Drive API Integration** – currently mocked; can be replaced with Google Drive or OneDrive.  
- **File Retrieval and Upload** – read and write files.  
- **File Searching and Filtering** – keyword-based search.  
- **Vector Database (RAG) Integration** – semantic search using embeddings.

> This allows retrieval by **name or context**, useful for workflows like expense verification.

---

## 🧩 Architecture

DocumentAgent
├── DriveAdapter / MockDriveAdapter
└── VectorDBAdapter (RAG)


- Minimal and modular design.  
- Can be extended to connect to real cloud services or vector databases in the future.

---

## ⚙️ Capabilities

| Functionality        | Description                                      |
|---------------------|--------------------------------------------------|
| 🔍 Keyword Search     | Search files by name or metadata.               |
| 🧠 Semantic Search    | Retrieve files based on embeddings (RAG).      |
| ☁️ Upload / Download  | Add or retrieve files from storage.             |
| 🔄 Modular Design     | Replace adapters with real APIs or vector DBs.  |

---

## 🏃 How to Run

1. Place `document_agent.py` and `run_agent.py` in the same folder.  
2. In terminal, run:
python run_agent.py

3. The script will:
    Upload a mock file
    Perform keyword search
    Perform semantic search
    Download a placeholder file

CRUD Operations

| CRUD       | Current Support                              |
| ---------- | -------------------------------------------- |
| **Create** | ✅ `upload_file()` adds a new document (mock) |
| **Read**   | ✅ `download_file()` retrieves a document     |
| **Update** | ❌ Not implemented                            |
| **Delete** | ❌ Not implemented                            |


## Dependencies

- Python 3.9+
- (Planned) `google-api-python-client` for real Drive integration
- (Optional) `faiss` or `chromadb` for vector-based semantic search

## Future Additions

- Real Google Drive / OneDrive integration
- Full RAG-powered question-answering on document contents
- Update/Delete support for full CRUD
- Integration with other agents (Email, Expense, Orchestrator)

**Author:** Darren Tang  
**Project:** Multi-Agent Expense Management System (COEN296 – Fall 2025)
