"""Auth module exports."""

from openharness.enterprise.auth.auth import (
    AuthConfig,
    AuthError,
    AuthService,
    InternalAuthService,
    UserManager,
    get_auth_config,
    set_auth_config,
    get_auth_service,
    get_internal_auth_service,
    get_user_manager,
)
from openharness.enterprise.auth.middleware import (
    AuthMiddleware,
    WorkspaceIsolationMiddleware,
    get_current_user,
    get_current_user_optional,
    require_admin,
    get_user_id,
)

__all__ = [
    "AuthConfig",
    "AuthError",
    "AuthService",
    "InternalAuthService",
    "UserManager",
    "AuthMiddleware",
    "WorkspaceIsolationMiddleware",
    "get_auth_config",
    "set_auth_config",
    "get_auth_service",
    "get_internal_auth_service",
    "get_user_manager",
    "get_current_user",
    "get_current_user_optional",
    "require_admin",
    "get_user_id",
]