"""
Application routers initialization
"""
from . import employee_router
from . import expense_router
from . import policy_router
from . import audit_router
from . import agent_router
from . import orchestrator_router

__all__ = [
    'employee_router',
    'expense_router', 
    'policy_router',
    'audit_router',
    'agent_router',
    'orchestrator_router',
]
