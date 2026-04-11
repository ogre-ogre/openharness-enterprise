"""
OpenHarness Enterprise - Authentication Service

JWT-based authentication with password hashing and API key support.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import jwt, JWTError
from passlib.hash import bcrypt
from pydantic import BaseModel

from openharness.enterprise.storage.database import User, get_database
from openharness.enterprise.storage.audit import get_audit_logger


# ============================================================================
# Configuration
# ============================================================================

class AuthConfig(BaseModel):
    """Authentication configuration."""
    jwt_secret: str = "change-this-secret-in-production"
    jwt_expire_hours: int = 24
    jwt_algorithm: str = "HS256"


# Default config (should be loaded from config file in production)
_auth_config: Optional[AuthConfig] = None


def get_auth_config() -> AuthConfig:
    """Get auth configuration."""
    global _auth_config
    if _auth_config is None:
        _auth_config = AuthConfig()
    return _auth_config


def set_auth_config(config: AuthConfig) -> None:
    """Set auth configuration."""
    global _auth_config
    _auth_config = config


# ============================================================================
# Auth Error
# ============================================================================

class AuthError(Exception):
    """Authentication error."""
    
    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(message)


# ============================================================================
# Auth Service
# ============================================================================

class AuthService:
    """
    Authentication service for login and JWT management.
    
    Features:
    - Password verification
    - JWT token generation
    - Token validation
    - Password hashing
    """
    
    def __init__(self, config: Optional[AuthConfig] = None):
        self.config = config or get_auth_config()
        self.db = get_database()
        self.audit = get_audit_logger()
    
    def login(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Login with username and password.
        
        Args:
            username: Username
            password: Password
            ip_address: Client IP address
        
        Returns:
            Dict with token and user info
        
        Raises:
            AuthError: If login fails
        """
        # Find user
        user = self.db.get_user_by_username(username)
        
        if not user:
            self.audit.log_login(0, False, ip_address)  # Log failed login with user_id=0
            raise AuthError("用户名或密码错误", "invalid_credentials")
        
        # Verify password
        if not self.verify_password(password, user.password_hash):
            self.audit.log_login(user.id, False, ip_address)
            raise AuthError("用户名或密码错误", "invalid_credentials")
        
        # Check if user is active
        if not user.is_active:
            self.audit.log_login(user.id, False, ip_address)
            raise AuthError("用户已禁用", "user_disabled")
        
        # Update last login
        self.db.update_last_login(user.id)
        
        # Generate token
        token = self.generate_token(user)
        
        # Log successful login
        self.audit.log_login(user.id, True, ip_address)
        
        return {
            "token": token,
            "expires_at": datetime.utcnow() + timedelta(hours=self.config.jwt_expire_hours),
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "role": user.role,
                "api_key": user.api_key
            }
        }
    
    def generate_token(
        self,
        user: User,
        expire_hours: Optional[int] = None
    ) -> str:
        """
        Generate JWT token for user.
        
        Args:
            user: User object
            expire_hours: Token expiration hours (default from config)
        
        Returns:
            JWT token string
        """
        expire = expire_hours or self.config.jwt_expire_hours
        
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=expire)
        }
        
        return jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            Token payload
        
        Raises:
            AuthError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm]
            )
            
            # Verify user still exists and is active
            user = self.db.get_user(payload["user_id"])
            if not user or not user.is_active:
                raise AuthError("用户无效或已禁用", "user_invalid")
            
            return payload
        
        except JWTError as e:
            if "expired" in str(e).lower():
                raise AuthError("Token 已过期", "token_expired")
            raise AuthError("Token 无效", "token_invalid")
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain password
        
        Returns:
            Hashed password
        """
        import bcrypt as bcrypt_lib
        return bcrypt_lib.hashpw(password.encode('utf-8'), bcrypt_lib.gensalt(rounds=12)).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain password
            password_hash: Hashed password
        
        Returns:
            True if password matches
        """
        import bcrypt as bcrypt_lib
        try:
            return bcrypt_lib.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    def validate_password_strength(self, password: str) -> bool:
        """
        Validate password strength.
        
        Requirements:
        - At least 8 characters
        - Contains at least one letter
        - Contains at least one number
        
        Args:
            password: Password to validate
        
        Returns:
            True if password meets requirements
        """
        if len(password) < 8:
            return False
        
        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        
        return has_letter and has_number


# ============================================================================
# Internal Auth Service (API Key)
# ============================================================================

class InternalAuthService:
    """
    Internal authentication service for API key-based token generation.
    
    Used for embedding scenarios where external systems need to get
    user tokens without traditional login.
    """
    
    def __init__(self, config: Optional[AuthConfig] = None):
        self.config = config or get_auth_config()
        self.db = get_database()
        self.audit = get_audit_logger()
        self.auth_service = AuthService(config)
    
    def get_token_by_api_key(
        self,
        api_key: str,
        expires_in: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user token by API key.
        
        Args:
            api_key: User API key
            expires_in: Token expiration in seconds (default 1 hour)
            ip_address: Client IP address
        
        Returns:
            Dict with token and user info
        
        Raises:
            AuthError: If API key is invalid
        """
        # Find user by API key
        user = self.db.get_user_by_api_key(api_key)
        
        if not user:
            raise AuthError("API Key 无效", "invalid_api_key")
        
        if not user.is_active:
            raise AuthError("用户已禁用", "user_disabled")
        
        if not user.api_key_enabled:
            raise AuthError("用户 API Key 已禁用", "api_key_disabled")
        
        # Generate token
        expire_hours = (expires_in or 3600) / 3600  # Default 1 hour
        token = self.auth_service.generate_token(user, expire_hours=expire_hours)
        
        # Update API key usage
        self.db.update_api_key_last_used(user.id)
        
        # Log API key usage
        self.audit.log_api_key_usage(user.id, expires_in)
        
        return {
            "token": token,
            "expires_at": datetime.utcnow() + timedelta(seconds=expires_in or 3600),
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name
            }
        }


# ============================================================================
# User Manager (API Key Generation)
# ============================================================================

class UserManager:
    """
    User management service.
    
    Features:
    - User creation
    - User update
    - API key generation
    """
    
    def __init__(self):
        self.db = get_database()
        self.auth_service = AuthService()
        self.audit = get_audit_logger()
    
    def create_user(
        self,
        username: str,
        password: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        role: str = "user"
    ) -> User:
        """
        Create a new user.
        
        Args:
            username: Username
            password: Password
            display_name: Display name
            email: Email
            role: User role ('user' or 'admin')
        
        Returns:
            Created user
        
        Raises:
            AuthError: If username exists or password is weak
        """
        # Check if username exists
        if self.db.user_exists(username):
            raise AuthError("用户名已存在", "username_exists")
        
        # Validate password
        if not self.auth_service.validate_password_strength(password):
            raise AuthError("密码强度不足，至少8位且包含字母和数字", "weak_password")
        
        # Hash password
        password_hash = self.auth_service.hash_password(password)
        
        # Generate API key
        api_key = self.generate_api_key()
        
        # Create user
        user = self.db.create_user(
            username=username,
            password_hash=password_hash,
            display_name=display_name,
            email=email,
            role=role,
            api_key=api_key
        )
        
        return user
    
    def generate_api_key(self) -> str:
        """
        Generate a new API key.
        
        Format: oh_user_{random_32_chars}
        
        Returns:
            API key string
        """
        return f"oh_user_{secrets.token_urlsafe(32)}"
    
    def regenerate_api_key(self, user_id: int) -> str:
        """
        Regenerate API key for user.
        
        Args:
            user_id: User ID
        
        Returns:
            New API key
        """
        new_key = self.generate_api_key()
        self.db.update_api_key(user_id, new_key)
        self.audit.log_admin_action(user_id, "api_key_regenerated", user_id)
        return new_key
    
    def set_api_key_enabled(self, user_id: int, enabled: bool) -> None:
        """
        Enable or disable API key.
        
        Args:
            user_id: User ID
            enabled: Enable or disable
        """
        self.db.set_api_key_enabled(user_id, enabled)
        self.audit.log_admin_action(
            user_id,
            f"api_key_{ 'enabled' if enabled else 'disabled' }",
            user_id
        )
    
    def update_user(
        self,
        user_id: int,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[User]:
        """
        Update user info.
        
        Args:
            user_id: User ID
            display_name: Display name
            email: Email
            role: Role
            is_active: Active status
        
        Returns:
            Updated user
        """
        return self.db.update_user(
            user_id=user_id,
            display_name=display_name,
            email=email,
            role=role,
            is_active=is_active
        )
    
    def reset_password(self, user_id: int, new_password: str) -> None:
        """
        Reset user password.
        
        Args:
            user_id: User ID
            new_password: New password
        
        Raises:
            AuthError: If password is weak
        """
        if not self.auth_service.validate_password_strength(new_password):
            raise AuthError("密码强度不足", "weak_password")
        
        password_hash = self.auth_service.hash_password(new_password)
        self.db.update_password(user_id, password_hash)
        self.audit.log_admin_action(0, "reset_password", user_id)


# ============================================================================
# Service Instances
# ============================================================================

_auth_service: Optional[AuthService] = None
_internal_auth_service: Optional[InternalAuthService] = None
_user_manager: Optional[UserManager] = None


def get_auth_service() -> AuthService:
    """Get auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


def get_internal_auth_service() -> InternalAuthService:
    """Get internal auth service instance."""
    global _internal_auth_service
    if _internal_auth_service is None:
        _internal_auth_service = InternalAuthService()
    return _internal_auth_service


def get_user_manager() -> UserManager:
    """Get user manager instance."""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager