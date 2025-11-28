"""
Multi-Agent System for ExpenseSense

This module contains all specialized agents that work together using the A2A protocol.
"""

# Import all agents to ensure they register themselves
from . import expense_agent_service
from . import document_agent_service
from . import email_agent_service
from . import orchestrator_agent

# Import protocol components
from .a2a_protocol import agent_registry, A2ARequest, A2AResponse, A2AMessage

__all__ = [
    'expense_agent_service',
    'document_agent_service',
    'email_agent_service',
    'orchestrator_agent',
    'agent_registry',
    'A2ARequest',
    'A2AResponse',
    'A2AMessage',
]
