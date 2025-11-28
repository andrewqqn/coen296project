"""
Role-Based Access Control (RBAC) utilities for the orchestrator agent
"""
from functools import wraps
from typing import Callable, List, Literal
from pydantic_ai import RunContext
import logging

logger = logging.getLogger("rbac")

# Define role hierarchy
ROLE_HIERARCHY = {
    "admin": ["admin", "employee"],  # Admin has all employee permissions
    "employee": ["employee"]
}


def has_permission(user_role: str, required_role: str) -> bool:
    """
    Check if a user role has the required permission.
    
    Args:
        user_role: The user's actual role
        required_role: The minimum required role
        
    Returns:
        True if user has permission, False otherwise
    """
    allowed_roles = ROLE_HIERARCHY.get(user_role, [])
    return required_role in allowed_roles


def require_role(*required_roles: str):
    """
    Decorator to enforce role-based access control on agent tools.
    
    Usage:
        @require_role("admin")
        def admin_only_tool(ctx: RunContext[OrchestratorContext], ...):
            ...
        
        @require_role("employee", "admin")  # Either role works
        def employee_or_admin_tool(ctx: RunContext[OrchestratorContext], ...):
            ...
    
    Args:
        *required_roles: One or more roles that are allowed to use this tool
    """
    def decorator(func: Callable):
        # Check if the function is async
        import asyncio
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(ctx, *args, **kwargs):
                user_role = ctx.deps.role
                
                # Debug logging
                logger.info(
                    f"[RBAC CHECK] Tool: {func.__name__}, "
                    f"User: {ctx.deps.user_id}, "
                    f"User Role: '{user_role}', "
                    f"Required Roles: {required_roles}"
                )
                
                # Check if user has any of the required roles
                has_access = any(
                    has_permission(user_role, required_role)
                    for required_role in required_roles
                )
                
                logger.info(f"[RBAC CHECK] Access granted: {has_access}")
                
                if not has_access:
                    logger.warning(
                        f"Access denied: User {ctx.deps.user_id} with role '{user_role}' "
                        f"attempted to use tool '{func.__name__}' which requires one of: {required_roles}"
                    )
                    
                    # Log unauthorized access attempt
                    from services.audit_log_service import log_unauthorized_access
                    log_unauthorized_access(
                        actor="Human",
                        user_id=ctx.deps.user_id,
                        resource=func.__name__,
                        action="invoke_tool",
                        reason=f"User role '{user_role}' does not have required role(s): {', '.join(required_roles)}"
                    )
                    
                    return {
                        "error": f"Access denied: This operation requires one of the following roles: {', '.join(required_roles)}",
                        "required_roles": list(required_roles),
                        "user_role": user_role
                    }
                
                # User has permission, execute the function
                return await func(ctx, *args, **kwargs)
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(ctx, *args, **kwargs):
                user_role = ctx.deps.role
                
                # Debug logging
                logger.info(
                    f"[RBAC CHECK] Tool: {func.__name__}, "
                    f"User: {ctx.deps.user_id}, "
                    f"User Role: '{user_role}', "
                    f"Required Roles: {required_roles}"
                )
                
                # Check if user has any of the required roles
                has_access = any(
                    has_permission(user_role, required_role)
                    for required_role in required_roles
                )
                
                logger.info(f"[RBAC CHECK] Access granted: {has_access}")
                
                if not has_access:
                    logger.warning(
                        f"Access denied: User {ctx.deps.user_id} with role '{user_role}' "
                        f"attempted to use tool '{func.__name__}' which requires one of: {required_roles}"
                    )
                    
                    # Log unauthorized access attempt
                    from services.audit_log_service import log_unauthorized_access
                    log_unauthorized_access(
                        actor="Human",
                        user_id=ctx.deps.user_id,
                        resource=func.__name__,
                        action="invoke_tool",
                        reason=f"User role '{user_role}' does not have required role(s): {', '.join(required_roles)}"
                    )
                    
                    return {
                        "error": f"Access denied: This operation requires one of the following roles: {', '.join(required_roles)}",
                        "required_roles": list(required_roles),
                        "user_role": user_role
                    }
                
                # User has permission, execute the function
                return func(ctx, *args, **kwargs)
            
            return sync_wrapper
    
    return decorator


def filter_by_ownership(
    ctx,
    items: List[dict],
    owner_field: str = "employee_id"
) -> List[dict]:
    """
    Filter a list of items to only include those owned by the current user.
    Admins see all items, employees only see their own.
    
    Args:
        ctx: RunContext with user information
        items: List of items to filter
        owner_field: Field name that contains the owner ID
        
    Returns:
        Filtered list of items
    """
    if ctx.deps.role == "admin":
        return items
    
    # Filter to only items owned by this user
    filtered = [
        item for item in items
        if item.get(owner_field) == ctx.deps.user_id
    ]
    
    logger.info(
        f"Filtered {len(items)} items to {len(filtered)} for employee {ctx.deps.user_id}"
    )
    
    return filtered


def check_ownership(
    ctx,
    item: dict,
    owner_field: str = "employee_id"
) -> bool:
    """
    Check if the current user owns an item or is an admin.
    
    Args:
        ctx: RunContext with user information
        item: The item to check
        owner_field: Field name that contains the owner ID
        
    Returns:
        True if user has access, False otherwise
    """
    if ctx.deps.role == "admin":
        return True
    
    return item.get(owner_field) == ctx.deps.user_id
