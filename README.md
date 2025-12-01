# 📦 ExpenSense — AI-Powered Expense Management Platform

*“the agent makes sense of your expenses intelligently”*


## 🚀 Overview

ExpenSense is an intelligent multi-agent reimbursement management platform that automates the entire expense-review lifecycle.
The system integrates traditional backend services with LLM-powered agents to deliver accurate, auditable, and policy-aligned expense decisions.

Key capabilities include:

* Automated receipt OCR + validation
* Policy-aware reimbursement decisions
* AI-based anomaly detection (frequency, patterns, merchant reasonableness)
* Admin dashboard for manual review
* Secure file, email, and policy retrieval flows
* Full audit logging for every decision

## 🧠 System Architecture

ExpenSense uses a **layered architecture**:

* **Presentation Layer** — Web UI for employees & admins
* **Business Logic Layer** — Traditional backend workflow & validation
* **Agent Logic Layer** — AI agents (Expense, Document, Email, Orchestrator)
* **Data Access Layer** — CRUD abstraction for Firestore, Cloud Storage, Gmail, Vector DB
* **Data Layer** — All persistent system storage

Architecture diagram available on page 3 of the final report. 

## 🤖 Agents

* **Expense Agent** — OCR validation, rule checking (R1–R5), anomaly detection
* **Document Agent** — Receipt processing, PDF validation, RAG-safe extraction
* **Email Agent** — Notification delivery, secure outbound messaging
* **Orchestrator Agent** — Coordinates workflows, routes tasks to specialized agents

## 📑 Key Features

* Automatic approval for valid requests ≤ $500 (Rule R1)
* Mandatory manual review for > $500 (Rule R3)
* Frequency limit enforcement (Rule R2)
* Strict documentation validation (Rule R4)
* Post-approval financial update + audit logging (Rule R5)
* Policy retrieval using Vector DB with safeguard grounding

## 🛡 Security & Red Teaming

The system includes a full MAESTRO-aligned Red Team Test Suite:

* 29 total tests across 7 layers and 4 agents
* Tests include hallucination checks, data poisoning, prompt injection, sandbox escape, RBAC enforcement, and inter-agent sanitization
* Final report documents **5 vulnerabilities**, primarily RBAC-related, with mitigation recommendations

## 📁 Project Structure

```
frontend/       # Web UI (React / Vite)
backend/        # FastAPI server, agents, business logic
services/       # Firestore, Storage, Gmail, Vector DB CRUD interfaces
agents/         # Expense, Document, Email, Orchestrator agents
redteam/        # MAESTRO-aligned test suite
```

# System Overview
<img width="1051" height="815" alt="Screenshot 2025-11-30 at 11 43 34 PM" src="https://github.com/user-attachments/assets/14a9f302-8011-496f-b3ac-7d3f4834ee94" />
<img width="1051" height="815" alt="Screenshot 2025-11-30 at 11 43 46 PM" src="https://github.com/user-attachments/assets/d4635e12-ea80-4b13-9f34-ffd7e36d07bd" />
<img width="1051" height="815" alt="Screenshot 2025-11-30 at 11 43 56 PM" src="https://github.com/user-attachments/assets/5f7be676-00ae-465c-9286-d54c1a688581" />

<img width="976" height="669" alt="Screenshot 2025-11-30 at 9 17 47 PM" src="https://github.com/user-attachments/assets/1b9101b7-7601-4fc5-b7ee-913899529a5e" />
<img width="976" height="751" alt="Screenshot 2025-11-30 at 9 18 39 PM" src="https://github.com/user-attachments/assets/328ddb94-5160-4820-a27b-baff82b6bc16" />
<img width="1051" height="815" alt="Screenshot 2025-11-30 at 11 44 08 PM" src="https://github.com/user-attachments/assets/ddbcecd1-a4e0-426d-8bb6-830bed5c6fa7" />

## 📜 Authors

ExpenSense Team (COEN 296 Red Team B):
Joshua Lee, Yulin Zeng, Andrew Nguyen, Darren Tang
GitHub Repo: [https://github.com/andrewqqn/coen296project](https://github.com/andrewqqn/coen296project)
