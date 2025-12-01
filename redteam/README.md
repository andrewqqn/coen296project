# Red Team Testing

This directory contains the red team testing materials for the Enterprise Copilot application, systematically evaluating security threats across all 7 MAESTRO layers.

## 📊 Quick Summary

- **4 Agent Test Suites**: Document, Email, Expense, and Orchestrator Agents
- **29 Total Test Cases**: Comprehensive coverage across all 7 MAESTRO layers
- **🔴 5 Vulnerabilities Found**: Actual security issues requiring fixes
- **✅ 19 Tests Passed**: Security controls working correctly
- **Complete Coverage**: All required MAESTRO layers tested for each agent

## 🚀 Quick Start

### Prerequisites
- Backend server running on `http://localhost:8000`
- Firebase emulators running
- Python 3.x with required dependencies

### Run Tests

```bash
# Navigate to test directory
cd testdata/

# Run all tests for an agent
python3 test_document_agent.py
python3 test_email_agent.py
python3 test_expense_agent.py
python3 test_orchestrator_agent.py

# Run specific MAESTRO layer
python3 test_document_agent.py layer1
python3 test_document_agent.py layer6
```

### Review Results
- **Test Results**: See `TEST_RESULTS.md` for detailed execution results
- **Vulnerabilities**: See `REPORT.md` for detailed vulnerability reports (Appendix C format)
- **Full Documentation**: See `RED_TEAM_TEST_SUITE.md` for comprehensive test suite documentation

## 📁 Directory Structure

```
redteam/
├── README.md                    # This file - overview of red team testing
├── RED_TEAM_TEST_SUITE.md       # Comprehensive test suite documentation
├── REPORT.md                     # Detailed vulnerability reports (Section 10)
├── TEST_RESULTS.md              # Detailed test execution results
├── plan.md                      # Red team test plan aligned with MAESTRO Threat Model
├── testdata/                    # Test scripts for executing red team attacks
│   ├── test_document_agent.py  # Document Agent tests (all 7 layers)
│   ├── test_email_agent.py      # Email Agent tests (all 7 layers)
│   ├── test_expense_agent.py    # Expense Agent tests (all 7 layers)
│   └── test_orchestrator_agent.py # Orchestrator Agent tests (all 7 layers)
└── sample_expenses/             # Sample PDF receipts used for testing
```

## 🎯 Overview

The red team testing suite systematically evaluates the Enterprise Copilot application against security threats identified in the **MAESTRO Threat Model**. Tests are organized by:

- **MAESTRO Layers**: Foundation Models, Data Operations, Agent Frameworks, Deployment & Infrastructure, Evaluation & Observability, Security & Compliance, Agent Ecosystem
- **ASI Threat Taxonomy**: Agency & Reasoning, Data & Memory-Based, Tool & Execution-Based, Authentication & Identity, Human-in-the-Loop threats

## 📋 Key Findings

- **🔴 5 Security Vulnerabilities Found**: RBAC bypass issues across multiple agents
- **Most Common Issue**: RBAC Bypass (found in 3 out of 4 agents)
- **✅ Strong Defenses**: Prompt injection, sandbox escape, and inter-agent injection all properly blocked

For detailed findings, see:
- **`TEST_RESULTS.md`**: Complete test execution results
- **`REPORT.md`**: Detailed vulnerability reports following Appendix C template

## 📚 Documentation

| Document | Purpose |
|:---------|:--------|
| **`RED_TEAM_TEST_SUITE.md`** | Complete test suite documentation with methodology, test cases, and results |
| **`TEST_RESULTS.md`** | Detailed test execution results with vulnerability breakdown |
| **`REPORT.md`** | Detailed vulnerability reports using Appendix C reporting template |
| **`plan.md`** | Red team test plan aligned with MAESTRO Threat Model |

## ✅ Project Specification Compliance

This test suite fully complies with **COEN 296 Project Specification Section 3.6 Red Teaming**:
- ✅ All 7 MAESTRO layers tested for each agent
- ✅ ASI Threat Taxonomy alignment
- ✅ Comprehensive test coverage
- ✅ Detailed vulnerability reporting (Appendix C format)
