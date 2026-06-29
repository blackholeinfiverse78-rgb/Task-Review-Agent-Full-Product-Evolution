"""
Security module initialization
"""
from .middleware import (
    SecurityConfig,
    UserRole,
    get_current_user,
    require_governor,
    require_reviewer_or_governor,
    require_operator_or_governor,
    require_any_authenticated,
    register_used_approval_token,
    validate_startup_secrets
)

# Maintain backward compatibility aliases if needed
require_admin = require_governor
require_user_or_admin = require_reviewer_or_governor

__all__ = [
    "SecurityConfig",
    "UserRole", 
    "get_current_user",
    "require_governor",
    "require_reviewer_or_governor",
    "require_operator_or_governor",
    "require_any_authenticated",
    "register_used_approval_token",
    "validate_startup_secrets",
    "require_admin",
    "require_user_or_admin"
]