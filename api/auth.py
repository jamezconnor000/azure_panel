#!/usr/bin/env python3
"""
AetherAccess Authentication Module
JWT-based authentication with bcrypt password hashing
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib

# Configuration
SECRET_KEY = "aether-access-secret-key-change-in-production"  # TODO: Move to environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Security
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Payload to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token with longer expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def hash_token(token: str) -> str:
    """Create a SHA-256 hash of a token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user from JWT token

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        User information from token payload

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = decode_token(token)

    # Verify token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user info
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": int(user_id),
        "username": payload.get("username"),
        "email": payload.get("email"),
        "role": payload.get("role"),
    }


async def require_role(required_roles: list[str]):
    """
    Dependency factory to require specific roles

    Usage:
        @app.get("/admin")
        async def admin_endpoint(user = Depends(require_role(["admin"]))):
            ...
    """
    async def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user["role"] not in required_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )
        return user

    return role_checker


async def get_current_active_user(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Dependency to ensure user is active
    Note: This requires database lookup - implement in main server
    """
    # TODO: Add database check for user.is_active
    return user


def create_password_reset_token(user_id: int, email: str) -> str:
    """Create a short-lived token for password reset"""
    data = {
        "sub": str(user_id),
        "email": email,
        "type": "password_reset"
    }
    expire = datetime.utcnow() + timedelta(hours=1)
    data["exp"] = expire

    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a password reset token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return payload
    except JWTError:
        return None


# Role-based permission helpers
ROLE_PERMISSIONS = {
    "admin": [
        "user.create", "user.read", "user.update", "user.delete",
        "door.create", "door.read", "door.update", "door.delete",
        "access_level.create", "access_level.read", "access_level.update", "access_level.delete",
        "access_level.assign",
        "card_holder.create", "card_holder.read", "card_holder.update", "card_holder.delete",
        "door.control", "door.configure", "system.configure",
        "audit.read", "reports.generate"
    ],
    "operator": [
        "user.read", "door.read", "access_level.read",
        "card_holder.create", "card_holder.read", "card_holder.update",
        "access_level.assign",
        "door.control", "audit.read", "reports.generate"
    ],
    "guard": [
        "door.read", "card_holder.read", "door.control", "audit.read"
    ],
    "user": [
        "door.read"
    ]
}


def has_permission(user_role: str, permission: str) -> bool:
    """Check if a role has a specific permission"""
    role_perms = ROLE_PERMISSIONS.get(user_role, [])
    return permission in role_perms


def check_permission(user: Dict[str, Any], permission: str):
    """
    Check if user has permission, raise HTTPException if not

    Usage:
        check_permission(user, "door.delete")
    """
    if not has_permission(user["role"], permission):
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied: {permission} required"
        )
