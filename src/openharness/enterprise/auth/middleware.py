"""
OpenHarness Enterprise - Authentication Middleware

FastAPI middleware for JWT token validation and user context injection.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from openharness.enterprise.storage.database import User, get_database
from openharness.enterprise.auth.auth import AuthService, AuthError, get_auth_service


# ============================================================================
# HTTP Bearer Security
# ============================================================================

oauth2_scheme = HTTPBearer(auto_error=False)


# ============================================================================
# Auth Middleware
# ============================================================================

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for FastAPI.
    
    Validates JWT tokens and injects user context into requests.
    """
    
    # Paths that don't require authentication
    PUBLIC_PATHS = [
        "/",
        "/health",
        "/api/auth/login",
        "/api/auth/token-by-api-key",
        "/docs",
        "/openapi.json",
    ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request through middleware."""
        
        # Skip public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # Also skip static files and favicon
        if request.url.path.startswith("/static") or request.url.path == "/favicon.ico":
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="未认证")
        
        token = auth_header.replace("Bearer ", "")
        
        # Verify token
        auth_service = get_auth_service()
        try:
            payload = auth_service.verify_token(token)
            
            # Inject user info into request state
            request.state.user_id = payload["user_id"]
            request.state.user_role = payload["role"]
            request.state.username = payload["username"]
            
        except AuthError as e:
            raise HTTPException(status_code=401, detail=e.message)
        
        return await call_next(request)


# ============================================================================
# Workspace Isolation Middleware
# ============================================================================

class WorkspaceIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to ensure workspace isolation.
    
    Prevents path traversal attacks and ensures users only access
    their own workspace files.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request through middleware."""
        
        # Check for path traversal in query parameters
        for key, value in request.query_params.items():
            if "path" in key.lower() or "file" in key.lower():
                if ".." in value or value.startswith("/"):
                    raise HTTPException(status_code=400, detail="非法路径")
        
        return await call_next(request)


# ============================================================================
# Dependency Functions
# ============================================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme)
) -> User:
    """
    Get current user from JWT token.
    
    Use as FastAPI dependency:
        @router.get("/me")
        async def get_me(user: User = Depends(get_current_user)):
            return user
    
    Args:
        credentials: HTTP Bearer credentials
    
    Returns:
        User object
    
    Raises:
        HTTPException: If token is invalid
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="未认证")
    
    auth_service = get_auth_service()
    
    try:
        payload = auth_service.verify_token(credentials.credentials)
        user = get_database().get_user(payload["user_id"])
        
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        
        return user
    
    except AuthError as e:
        raise HTTPException(status_code=401, detail=e.message)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme)
) -> Optional[User]:
    """
    Get current user optionally (returns None if not authenticated).
    
    Args:
        credentials: HTTP Bearer credentials
    
    Returns:
        User object or None
    """
    if not credentials:
        return None
    
    auth_service = get_auth_service()
    
    try:
        payload = auth_service.verify_token(credentials.credentials)
        return get_database().get_user(payload["user_id"])
    except AuthError:
        return None


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role.
    
    Use as FastAPI dependency:
        @router.post("/admin/users")
        async def create_user(
            user: User = Depends(require_admin)
        ):
            ...
    
    Args:
        current_user: Current user
    
    Returns:
        User object (admin)
    
    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    return current_user


async def get_user_id(request: Request) -> int:
    """
    Get user ID from request state.
    
    Use after AuthMiddleware has processed the request.
    
    Args:
        request: FastAPI request
    
    Returns:
        User ID
    
    Raises:
        HTTPException: If user ID not found
    """
    user_id = getattr(request.state, "user_id", None)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    return user_id