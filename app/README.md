# 🗂️ Document Management Agent

The **Document Management Agent** is part of a larger **multi-agent expense management system** designed to handle documents stored in cloud environments like **Google Drive** and **OneDrive**.  
It enables **retrieval**, **upload**, and **semantic search (RAG)** capabilities to support other agents such as the Email Agent and Expense Agent.

---

## 🚀 Overview

This agent provides intelligent document management by combining:

- **Drive API Integration** – connects to cloud storage platforms.  
- **File Retrieval and Upload** – enables reading, writing, and organizing files.  
- **File Searching and Filtering** – supports keyword and metadata-based lookups.  
- **Vector Database (RAG) Integration** – allows semantic document search using embeddings.

Together, these modules make the agent capable of retrieving files by meaning or context, not just by name — improving automation for workflows like expense verification and policy lookup.

---

## 🧩 Architecture

DocumentAgent
├── DriveAdapter (for Google Drive / OneDrive)
├── VectorDBAdapter (for RAG)
├── DocumentSearchEngine
└── EventBus (communication with other agents)


The agent can operate independently or communicate with other agents through an internal event system.  
It is structured to allow modular replacement of components (e.g., swapping Google Drive for OneDrive, or FAISS for Pinecone).

---

## ⚙️ Capabilities

| Functionality | Description |
|----------------|-------------|
| 🔍 Search | Keyword and metadata-based search via Drive API |
| 🧠 Semantic Retrieval | Embedding-based retrieval (RAG) using Vector DB |
| ☁️ Upload / Download | Add or retrieve files from connected cloud storage |
| 🧩 Event Integration | Publishes and subscribes to document-related events |
| 🔄 Modular Design | Easily extendable to different APIs or vector databases |

---

## 🧠 Integration

The Document Agent interacts with other components of the system:

| Agent | Interaction |
|--------|--------------|
| **Email Agent** | Retrieves attachments or shared files |
| **Expense Agent** | Fetches receipts or reports for verification |
| **Orchestrator** | Coordinates document searches and indexing |

The EventBus enables these communications asynchronously and in a decoupled manner.

---

## 🧰 Dependencies

- **Python 3.9+**
- (Planned) `google-api-python-client` for Drive integration  
- (Optional) `faiss` or `chromadb` for vector-based semantic search  

---

## 🔜 Future Additions

- Google Drive API authentication using `gcloud`
- OneDrive adapter
- RAG-powered question-answering from document contents
- Integration with orchestrator agent for full workflow automation

---

## 🧾 Summary

The **Document Management Agent** acts as the system’s intelligent file librarian —  
bridging cloud storage and AI retrieval to make enterp&rise data more accessible and automatable.

It currently runs with placeholder adapters (mock APIs) and can be easily extended to connect to real cloud services and vector databases as they are added.

---


**Author:** Darren Tang  
**Project:** Multi-Agent Expense Management System (COEN296 – Fall 2025)