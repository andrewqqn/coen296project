"""
Multi-Agent System for Expense Reimbursement
Uses Google's A2A protocol for agent-to-agent communication
"""
from .a2a_protocol import (
    AgentCard,
    AgentCapability,
    A2AMessage,
    A2ARequest,
    A2AResponse,
    AgentRegistry,
    agent_registry
)
from .base_agent import BaseAgent
from .expense_agent_service import ExpenseAgent, expense_agent
from .document_agent_service import DocumentAgent, document_agent
from .orchestrator_agent import OrchestratorAgent, orchestrator_agent

__all__ = [
    # Protocol
    "AgentCard",
    "AgentCapability",
    "A2AMessage",
    "A2ARequest",
    "A2AResponse",
    "AgentRegistry",
    "agent_registry",
    # Base
    "BaseAgent",
    # Agents
    "ExpenseAgent",
    "expense_agent",
    "DocumentAgent",
    "document_agent",
    "OrchestratorAgent",
    "orchestrator_agent",
]
