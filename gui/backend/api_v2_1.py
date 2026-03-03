#!/usr/bin/env python3
"""
AetherAccess API v2.1 - Extended Features
Authentication, User Management, Door Configuration, Access Levels
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import auth
import database as db

# Create router
router = APIRouter(prefix="/api/v2.1", tags=["v2.1"])


# =============================================================================
# Pydantic Models
# =============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "user"
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    phone: Optional[str]
    is_active: bool
    last_login_at: Optional[int]
    created_at: int


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class DoorConfigCreate(BaseModel):
    door_id: Optional[int] = None  # Auto-assigned if not provided
    door_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    location: Optional[str] = None
    door_type: Optional[str] = "interior"
    osdp_enabled: bool = False
    scbk: Optional[str] = None  # Hex string
    reader_address: Optional[int] = Field(None, ge=0, le=126)
    baud_rate: int = 9600
    led_control: bool = True
    buzzer_control: bool = True
    biometric_enabled: bool = False
    display_enabled: bool = False
    keypad_enabled: bool = False
    is_monitored: bool = True
    alert_on_failure: bool = True
    notes: Optional[str] = None


class DoorConfigUpdate(BaseModel):
    door_name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    door_type: Optional[str] = None
    osdp_enabled: Optional[bool] = None
    scbk: Optional[str] = None
    reader_address: Optional[int] = Field(None, ge=0, le=126)
    baud_rate: Optional[int] = None
    led_control: Optional[bool] = None
    buzzer_control: Optional[bool] = None
    biometric_enabled: Optional[bool] = None
    display_enabled: Optional[bool] = None
    keypad_enabled: Optional[bool] = None
    is_monitored: Optional[bool] = None
    alert_on_failure: Optional[bool] = None
    notes: Optional[str] = None


class DoorConfigResponse(BaseModel):
    door_id: int
    door_name: str
    description: Optional[str]
    location: Optional[str]
    door_type: Optional[str]
    osdp_enabled: bool
    reader_address: Optional[int]
    baud_rate: int
    led_control: bool
    buzzer_control: bool
    is_monitored: bool
    created_at: int
    updated_at: int


class AccessLevelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    priority: int = Field(0, ge=0, le=100)


class AccessLevelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class AccessLevelResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    priority: int
    is_active: bool
    created_at: int


class AccessLevelDoorAssignment(BaseModel):
    door_id: int
    timezone_id: int = 2  # 2 = Always
    entry_allowed: bool = True
    exit_allowed: bool = True


# =============================================================================
# Card Holder Models
# =============================================================================

class CardHolderCreate(BaseModel):
    card_number: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    employee_id: Optional[str] = Field(None, max_length=50)
    badge_number: Optional[str] = Field(None, max_length=50)
    photo_url: Optional[str] = Field(None, max_length=500)
    activation_date: Optional[int] = None
    expiration_date: Optional[int] = None
    is_active: bool = True
    notes: Optional[str] = None
    user_id: Optional[int] = None  # Link to users table


class CardHolderUpdate(BaseModel):
    card_number: Optional[str] = Field(None, min_length=1, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    employee_id: Optional[str] = Field(None, max_length=50)
    badge_number: Optional[str] = Field(None, max_length=50)
    photo_url: Optional[str] = Field(None, max_length=500)
    activation_date: Optional[int] = None
    expiration_date: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    user_id: Optional[int] = None


class CardHolderResponse(BaseModel):
    id: int
    card_number: str
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    department: Optional[str]
    employee_id: Optional[str]
    badge_number: Optional[str]
    photo_url: Optional[str]
    activation_date: int
    expiration_date: int
    is_active: bool
    notes: Optional[str]
    user_id: Optional[int]
    created_at: int
    updated_at: int


class UserAccessLevelGrant(BaseModel):
    access_level_id: int
    activation_date: int = 0  # 0 = immediate
    expiration_date: int = 0  # 0 = never
    notes: Optional[str] = None


# =============================================================================
# Authentication Endpoints
# =============================================================================

@router.post("/auth/login", response_model=LoginResponse)
async def login(request: Request, credentials: LoginRequest):
    """
    Login endpoint - authenticate user and return JWT tokens
    """
    # Get user
    user = await db.get_user_by_username(credentials.username)

    if not user:
        # Log failed attempt
        await db.log_audit(
            None, "login_failed", details={"username": credentials.username, "reason": "user_not_found"},
            ip_address=request.client.host, success=False
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check if account is locked
    if user.get("is_locked"):
        raise HTTPException(status_code=403, detail="Account is locked")

    # Check if account is active
    if not user.get("is_active"):
        raise HTTPException(status_code=403, detail="Account is inactive")

    # Verify password
    if not auth.verify_password(credentials.password, user["password_hash"]):
        # Increment failed login attempts
        failed_count = await db.increment_failed_login(user["id"])

        # Lock account after 5 failed attempts
        if failed_count >= 5:
            await db.update_user(user["id"], is_locked=True)

        await db.log_audit(
            user["id"], "login_failed", details={"reason": "invalid_password"},
            ip_address=request.client.host, success=False
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Reset failed login attempts
    await db.reset_failed_login(user["id"])

    # Update last login
    await db.update_last_login(user["id"])

    # Create tokens
    token_data = {
        "sub": str(user["id"]),
        "username": user["username"],
        "email": user["email"],
        "role": user["role"]
    }

    access_token = auth.create_access_token(token_data)
    refresh_token = auth.create_refresh_token({"sub": str(user["id"])})

    # Create session
    token_hash = auth.hash_token(access_token)
    expires_at = int((datetime.utcnow() + timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp())
    await db.create_session(
        user["id"], token_hash, expires_at,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

    # Log successful login
    await db.log_audit(
        user["id"], "login_success",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

    # Return tokens and user info
    user_response = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "role": user["role"]
    }

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_response
    }


@router.post("/auth/logout")
async def logout(request: Request, current_user: Dict = Depends(auth.get_current_user)):
    """Logout - invalidate current session"""
    # Get token from request
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        token_hash = auth.hash_token(token)
        await db.invalidate_session(token_hash)

    await db.log_audit(
        current_user["id"], "logout",
        ip_address=request.client.host
    )

    return {"message": "Logged out successfully"}


@router.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    payload = auth.decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = int(payload.get("sub"))
    user = await db.get_user_by_id(user_id)

    if not user or not user.get("is_active"):
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Create new access token
    token_data = {
        "sub": str(user["id"]),
        "username": user["username"],
        "email": user["email"],
        "role": user["role"]
    }

    new_access_token = auth.create_access_token(token_data)

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


@router.get("/auth/me")
async def get_current_user_info(current_user: Dict = Depends(auth.get_current_user)):
    """Get current user information"""
    user = await db.get_user_by_id(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "role": user["role"],
        "phone": user.get("phone"),
        "is_active": user["is_active"],
        "last_login_at": user.get("last_login_at"),
        "created_at": user["created_at"]
    }


# =============================================================================
# User Management Endpoints
# =============================================================================

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Create a new user (admin only)"""
    auth.check_permission(current_user, "user.create")

    # Check if username exists
    existing = await db.get_user_by_username(user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check if email exists
    existing = await db.get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Hash password
    password_hash = auth.hash_password(user_data.password)

    # Create user
    user_id = await db.create_user(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        phone=user_data.phone
    )

    # Log action
    await db.log_audit(
        current_user["id"], "user_created",
        resource_type="user", resource_id=user_id,
        details={"username": user_data.username, "role": user_data.role}
    )

    # Get and return created user
    user = await db.get_user_by_id(user_id)
    return user


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    include_inactive: bool = False,
    current_user: Dict = Depends(auth.get_current_user)
):
    """List all users"""
    auth.check_permission(current_user, "user.read")

    users = await db.get_all_users(include_inactive=include_inactive)
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get user by ID"""
    auth.check_permission(current_user, "user.read")

    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Update user"""
    auth.check_permission(current_user, "user.update")

    # Check user exists
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user
    update_dict = user_data.dict(exclude_unset=True)
    if update_dict:
        await db.update_user(user_id, **update_dict)

        await db.log_audit(
            current_user["id"], "user_updated",
            resource_type="user", resource_id=user_id,
            details=update_dict
        )

    # Return updated user
    user = await db.get_user_by_id(user_id)
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Delete user (soft delete)"""
    auth.check_permission(current_user, "user.delete")

    # Prevent self-deletion
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete_user(user_id)

    await db.log_audit(
        current_user["id"], "user_deleted",
        resource_type="user", resource_id=user_id,
        details={"username": user["username"]}
    )

    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/change-password")
async def change_user_password(
    user_id: int,
    password_data: PasswordChange,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Change user password"""
    # Users can change their own password, admins can change any password
    if user_id != current_user["id"]:
        auth.check_permission(current_user, "user.update")

    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify current password if user is changing their own
    if user_id == current_user["id"]:
        if not auth.verify_password(password_data.current_password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Hash new password
    new_hash = auth.hash_password(password_data.new_password)

    # Update password
    await db.update_user(
        user_id,
        password_hash=new_hash,
        password_changed_at=int(datetime.now().timestamp())
    )

    # Invalidate all sessions
    await db.invalidate_user_sessions(user_id)

    await db.log_audit(
        current_user["id"], "password_changed",
        resource_type="user", resource_id=user_id
    )

    return {"message": "Password changed successfully"}


# =============================================================================
# Door Configuration Endpoints
# =============================================================================

@router.post("/doors", response_model=DoorConfigResponse)
async def create_door_config(
    door_data: DoorConfigCreate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Create door configuration"""
    auth.check_permission(current_user, "door.create")

    # Auto-assign door_id if not provided
    if door_data.door_id is None:
        # Get next available door_id
        doors = await db.get_all_door_configs()
        door_ids = [d['door_id'] for d in doors]
        door_data.door_id = max(door_ids) + 1 if door_ids else 1

    # Check if door already exists
    existing = await db.get_door_config(door_data.door_id)
    if existing:
        raise HTTPException(status_code=400, detail="Door configuration already exists")

    # Create door config
    config_dict = door_data.dict(exclude={"door_id", "door_name"})
    await db.create_door_config(door_data.door_id, door_data.door_name, **config_dict)

    await db.log_audit(
        current_user["id"], "door_created",
        resource_type="door", resource_id=door_data.door_id,
        details={"door_name": door_data.door_name}
    )

    door = await db.get_door_config(door_data.door_id)
    return door


@router.get("/doors", response_model=List[DoorConfigResponse])
async def list_doors(current_user: Dict = Depends(auth.get_current_user)):
    """List all door configurations"""
    auth.check_permission(current_user, "door.read")

    doors = await db.get_all_door_configs()
    return doors


@router.get("/doors/{door_id}", response_model=DoorConfigResponse)
async def get_door_config(
    door_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get door configuration"""
    auth.check_permission(current_user, "door.read")

    door = await db.get_door_config(door_id)
    if not door:
        raise HTTPException(status_code=404, detail="Door not found")

    return door


@router.put("/doors/{door_id}", response_model=DoorConfigResponse)
async def update_door_config(
    door_id: int,
    door_data: DoorConfigUpdate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Update door configuration"""
    auth.check_permission(current_user, "door.update")

    door = await db.get_door_config(door_id)
    if not door:
        raise HTTPException(status_code=404, detail="Door not found")

    update_dict = door_data.dict(exclude_unset=True)
    if update_dict:
        await db.update_door_config(door_id, **update_dict)

        await db.log_audit(
            current_user["id"], "door_updated",
            resource_type="door", resource_id=door_id,
            details=update_dict
        )

    door = await db.get_door_config(door_id)
    return door


@router.delete("/doors/{door_id}")
async def delete_door_config(
    door_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Delete door configuration"""
    auth.check_permission(current_user, "door.delete")

    door = await db.get_door_config(door_id)
    if not door:
        raise HTTPException(status_code=404, detail="Door not found")

    await db.delete_door_config(door_id)

    await db.log_audit(
        current_user["id"], "door_deleted",
        resource_type="door", resource_id=door_id,
        details={"door_name": door["door_name"]}
    )

    return {"message": "Door configuration deleted"}


class OSDPEnableRequest(BaseModel):
    scbk: str = Field(..., min_length=32, max_length=32)
    reader_address: int = Field(..., ge=0, le=126)


@router.post("/doors/{door_id}/osdp/enable")
async def enable_osdp_secure_channel(
    door_id: int,
    osdp_data: OSDPEnableRequest,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Enable OSDP Secure Channel for a door"""
    auth.check_permission(current_user, "door.configure")

    door = await db.get_door_config(door_id)
    if not door:
        raise HTTPException(status_code=404, detail="Door not found")

    # Validate SCBK (should be 32 hex characters for 16 bytes)
    try:
        int(osdp_data.scbk, 16)
    except ValueError:
        raise HTTPException(status_code=400, detail="SCBK must be valid hex")

    # Update door config
    await db.update_door_config(
        door_id,
        osdp_enabled=True,
        scbk=osdp_data.scbk,
        reader_address=osdp_data.reader_address
    )

    await db.log_audit(
        current_user["id"], "osdp_enabled",
        resource_type="door", resource_id=door_id,
        details={"reader_address": osdp_data.reader_address}
    )

    return {"message": "OSDP Secure Channel enabled", "door_id": door_id}


@router.post("/doors/{door_id}/osdp/disable")
async def disable_osdp_secure_channel(
    door_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Disable OSDP Secure Channel for a door"""
    auth.check_permission(current_user, "door.configure")

    door = await db.get_door_config(door_id)
    if not door:
        raise HTTPException(status_code=404, detail="Door not found")

    await db.update_door_config(door_id, osdp_enabled=False)

    await db.log_audit(
        current_user["id"], "osdp_disabled",
        resource_type="door", resource_id=door_id
    )

    return {"message": "OSDP Secure Channel disabled", "door_id": door_id}


# =============================================================================
# Access Level Endpoints
# =============================================================================

@router.post("/access-levels", response_model=AccessLevelResponse)
async def create_access_level(
    level_data: AccessLevelCreate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Create access level"""
    auth.check_permission(current_user, "access_level.create")

    level_id = await db.create_access_level(
        name=level_data.name,
        description=level_data.description,
        priority=level_data.priority
    )

    await db.log_audit(
        current_user["id"], "access_level_created",
        resource_type="access_level", resource_id=level_id,
        details={"name": level_data.name}
    )

    level = await db.get_access_level(level_id)
    return level


@router.get("/access-levels", response_model=List[AccessLevelResponse])
async def list_access_levels(
    include_inactive: bool = False,
    current_user: Dict = Depends(auth.get_current_user)
):
    """List all access levels"""
    auth.check_permission(current_user, "access_level.read")

    levels = await db.get_all_access_levels(include_inactive=include_inactive)
    return levels


@router.get("/access-levels/{level_id}", response_model=AccessLevelResponse)
async def get_access_level(
    level_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get access level"""
    auth.check_permission(current_user, "access_level.read")

    level = await db.get_access_level(level_id)
    if not level:
        raise HTTPException(status_code=404, detail="Access level not found")

    return level


@router.put("/access-levels/{level_id}", response_model=AccessLevelResponse)
async def update_access_level(
    level_id: int,
    level_data: AccessLevelUpdate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Update access level"""
    auth.check_permission(current_user, "access_level.update")

    level = await db.get_access_level(level_id)
    if not level:
        raise HTTPException(status_code=404, detail="Access level not found")

    update_dict = level_data.dict(exclude_unset=True)
    if update_dict:
        await db.update_access_level(level_id, **update_dict)

        await db.log_audit(
            current_user["id"], "access_level_updated",
            resource_type="access_level", resource_id=level_id,
            details=update_dict
        )

    level = await db.get_access_level(level_id)
    return level


@router.delete("/access-levels/{level_id}")
async def delete_access_level(
    level_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Delete access level"""
    auth.check_permission(current_user, "access_level.delete")

    level = await db.get_access_level(level_id)
    if not level:
        raise HTTPException(status_code=404, detail="Access level not found")

    await db.delete_access_level(level_id)

    await db.log_audit(
        current_user["id"], "access_level_deleted",
        resource_type="access_level", resource_id=level_id,
        details={"name": level["name"]}
    )

    return {"message": "Access level deleted"}


@router.post("/access-levels/{level_id}/doors")
async def add_door_to_access_level(
    level_id: int,
    assignment: AccessLevelDoorAssignment,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Add door to access level"""
    auth.check_permission(current_user, "access_level.update")

    level = await db.get_access_level(level_id)
    if not level:
        raise HTTPException(status_code=404, detail="Access level not found")

    door = await db.get_door_config(assignment.door_id)
    if not door:
        raise HTTPException(status_code=404, detail="Door not found")

    await db.add_door_to_access_level(
        level_id,
        assignment.door_id,
        assignment.timezone_id,
        assignment.entry_allowed,
        assignment.exit_allowed
    )

    await db.log_audit(
        current_user["id"], "door_added_to_level",
        resource_type="access_level", resource_id=level_id,
        details={"door_id": assignment.door_id, "door_name": door["door_name"]}
    )

    return {"message": "Door added to access level"}


@router.delete("/access-levels/{level_id}/doors/{door_id}")
async def remove_door_from_access_level(
    level_id: int,
    door_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Remove door from access level"""
    auth.check_permission(current_user, "access_level.update")

    await db.remove_door_from_access_level(level_id, door_id)

    await db.log_audit(
        current_user["id"], "door_removed_from_level",
        resource_type="access_level", resource_id=level_id,
        details={"door_id": door_id}
    )

    return {"message": "Door removed from access level"}


@router.get("/access-levels/{level_id}/doors")
async def get_access_level_doors(
    level_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get doors for access level"""
    auth.check_permission(current_user, "access_level.read")

    doors = await db.get_access_level_doors(level_id)
    return doors


# =============================================================================
# User Access Level Assignment
# =============================================================================

@router.post("/users/{user_id}/access-levels")
async def grant_user_access_level(
    user_id: int,
    grant_data: UserAccessLevelGrant,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Grant access level to user"""
    auth.check_permission(current_user, "user.update")

    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    level = await db.get_access_level(grant_data.access_level_id)
    if not level:
        raise HTTPException(status_code=404, detail="Access level not found")

    await db.grant_user_access_level(
        user_id,
        grant_data.access_level_id,
        grant_data.activation_date,
        grant_data.expiration_date,
        granted_by=current_user["id"],
        notes=grant_data.notes
    )

    await db.log_audit(
        current_user["id"], "access_granted",
        resource_type="user", resource_id=user_id,
        details={
            "access_level_id": grant_data.access_level_id,
            "access_level_name": level["name"]
        }
    )

    return {"message": "Access level granted"}


@router.delete("/users/{user_id}/access-levels/{level_id}")
async def revoke_user_access_level(
    user_id: int,
    level_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Revoke access level from user"""
    auth.check_permission(current_user, "user.update")

    await db.revoke_user_access_level(user_id, level_id, revoked_by=current_user["id"])

    await db.log_audit(
        current_user["id"], "access_revoked",
        resource_type="user", resource_id=user_id,
        details={"access_level_id": level_id}
    )

    return {"message": "Access level revoked"}


@router.get("/users/{user_id}/access-levels")
async def get_user_access_levels(
    user_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get user's access levels"""
    auth.check_permission(current_user, "user.read")

    levels = await db.get_user_access_levels(user_id)
    return levels


@router.get("/users/{user_id}/doors")
async def get_user_doors(
    user_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get doors user can access"""
    # Users can see their own doors, admins can see any user's doors
    if user_id != current_user["id"]:
        auth.check_permission(current_user, "user.read")

    doors = await db.get_user_doors(user_id)
    return doors


# =============================================================================
# Audit Log Endpoints
# =============================================================================

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get audit logs"""
    auth.check_permission(current_user, "audit.read")

    logs = await db.get_audit_logs(
        limit=limit,
        offset=offset,
        user_id=user_id,
        action_type=action_type,
        start_time=start_time,
        end_time=end_time
    )
    return logs


# =============================================================================
# Card Holder Endpoints
# =============================================================================

@router.post("/card-holders", response_model=CardHolderResponse)
async def create_card_holder(
    card_holder_data: CardHolderCreate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Create a new card holder"""
    auth.check_permission(current_user, "card_holder.create")

    # Check if card number already exists
    existing = await db.get_card_holder_by_card_number(card_holder_data.card_number)
    if existing:
        raise HTTPException(status_code=400, detail="Card number already exists")

    # Create card holder
    config_dict = card_holder_data.dict()
    card_holder_id = await db.create_card_holder(**config_dict)

    await db.log_audit(
        current_user["id"], "card_holder_created",
        resource_type="card_holder", resource_id=card_holder_id,
        details={"card_number": card_holder_data.card_number, "name": f"{card_holder_data.first_name} {card_holder_data.last_name}"}
    )

    card_holder = await db.get_card_holder(card_holder_id)
    return card_holder


@router.get("/card-holders", response_model=List[CardHolderResponse])
async def list_card_holders(
    include_inactive: bool = False,
    current_user: Dict = Depends(auth.get_current_user)
):
    """List all card holders"""
    auth.check_permission(current_user, "card_holder.read")
    return await db.get_all_card_holders(include_inactive=include_inactive)


@router.get("/card-holders/{card_holder_id}", response_model=CardHolderResponse)
async def get_card_holder(
    card_holder_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get card holder by ID"""
    auth.check_permission(current_user, "card_holder.read")

    card_holder = await db.get_card_holder(card_holder_id)
    if not card_holder:
        raise HTTPException(status_code=404, detail="Card holder not found")

    return card_holder


@router.put("/card-holders/{card_holder_id}", response_model=CardHolderResponse)
async def update_card_holder(
    card_holder_id: int,
    card_holder_data: CardHolderUpdate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Update card holder"""
    auth.check_permission(current_user, "card_holder.update")

    # Check if card holder exists
    existing = await db.get_card_holder(card_holder_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Card holder not found")

    # If updating card number, check for duplicates
    if card_holder_data.card_number and card_holder_data.card_number != existing["card_number"]:
        duplicate = await db.get_card_holder_by_card_number(card_holder_data.card_number)
        if duplicate:
            raise HTTPException(status_code=400, detail="Card number already exists")

    # Update card holder
    update_dict = card_holder_data.dict(exclude_unset=True)
    await db.update_card_holder(card_holder_id, **update_dict)

    await db.log_audit(
        current_user["id"], "card_holder_updated",
        resource_type="card_holder", resource_id=card_holder_id,
        details=update_dict
    )

    card_holder = await db.get_card_holder(card_holder_id)
    return card_holder


@router.delete("/card-holders/{card_holder_id}", response_model=Dict[str, str])
async def delete_card_holder(
    card_holder_id: int,
    permanent: bool = False,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Delete card holder (soft delete by default, permanent if specified)"""
    auth.check_permission(current_user, "card_holder.delete")

    # Check if card holder exists
    existing = await db.get_card_holder(card_holder_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Card holder not found")

    if permanent:
        await db.hard_delete_card_holder(card_holder_id)
    else:
        await db.delete_card_holder(card_holder_id)

    await db.log_audit(
        current_user["id"], "card_holder_deleted" if not permanent else "card_holder_hard_deleted",
        resource_type="card_holder", resource_id=card_holder_id,
        details={"permanent": permanent}
    )

    return {"message": "Card holder deleted successfully"}


# =============================================================================
# Card Holder Access Level Endpoints
# =============================================================================

@router.post("/card-holders/{card_holder_id}/access-levels/{level_id}", response_model=Dict[str, str])
async def grant_card_holder_access_level(
    card_holder_id: int,
    level_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Grant an access level to a card holder"""
    auth.check_permission(current_user, "access_level.assign")

    # Verify card holder exists
    card_holder = await db.get_card_holder(card_holder_id)
    if not card_holder:
        raise HTTPException(status_code=404, detail="Card holder not found")

    # Verify access level exists
    level = await db.get_access_level(level_id)
    if not level:
        raise HTTPException(status_code=404, detail="Access level not found")

    # Grant access
    try:
        await db.grant_card_holder_access_level(card_holder_id, level_id, granted_by=current_user["id"])
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Card holder already has this access level")
        raise

    await db.log_audit(
        current_user["id"], "card_holder_access_granted",
        resource_type="card_holder", resource_id=card_holder_id,
        details={"level_id": level_id, "level_name": level["name"]}
    )

    return {"message": f"Access level '{level['name']}' granted to card holder"}


@router.delete("/card-holders/{card_holder_id}/access-levels/{level_id}", response_model=Dict[str, str])
async def revoke_card_holder_access_level(
    card_holder_id: int,
    level_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Revoke an access level from a card holder"""
    auth.check_permission(current_user, "access_level.assign")

    await db.revoke_card_holder_access_level(card_holder_id, level_id)

    await db.log_audit(
        current_user["id"], "card_holder_access_revoked",
        resource_type="card_holder", resource_id=card_holder_id,
        details={"level_id": level_id}
    )

    return {"message": "Access level revoked from card holder"}


@router.get("/card-holders/{card_holder_id}/access-levels")
async def get_card_holder_access_levels(
    card_holder_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get all access levels for a card holder"""
    auth.check_permission(current_user, "card_holder.read")

    card_holder = await db.get_card_holder(card_holder_id)
    if not card_holder:
        raise HTTPException(status_code=404, detail="Card holder not found")

    return await db.get_card_holder_access_levels(card_holder_id)


@router.get("/card-holders/{card_holder_id}/doors")
async def get_card_holder_doors(
    card_holder_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get all doors a card holder can access"""
    auth.check_permission(current_user, "card_holder.read")

    card_holder = await db.get_card_holder(card_holder_id)
    if not card_holder:
        raise HTTPException(status_code=404, detail="Card holder not found")

    return await db.get_card_holder_doors(card_holder_id)


@router.get("/access-levels/{level_id}/card-holders")
async def get_access_level_card_holders(
    level_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get all card holders assigned to an access level"""
    auth.check_permission(current_user, "access_level.read")

    level = await db.get_access_level(level_id)
    if not level:
        raise HTTPException(status_code=404, detail="Access level not found")

    return await db.get_access_level_card_holders(level_id)


# =============================================================================
# Panel Management & Hardware Tree
# =============================================================================

class PanelCreate(BaseModel):
    panel_id: int
    panel_name: str = Field(..., min_length=1, max_length=100)
    panel_type: str = Field(..., pattern="^(MASTER|DOWNSTREAM)$")
    parent_panel_id: Optional[int] = None
    rs485_address: Optional[int] = None
    firmware_version: Optional[str] = None


class PanelUpdate(BaseModel):
    panel_name: Optional[str] = None
    status: Optional[str] = None
    firmware_version: Optional[str] = None
    notes: Optional[str] = None


class PanelReaderCreate(BaseModel):
    panel_id: int
    reader_address: int
    reader_name: Optional[str] = None


class PanelIOCreate(BaseModel):
    panel_id: int
    number: int
    name: Optional[str] = None


@router.post("/panels")
async def create_panel(
    panel_data: PanelCreate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Create a new panel (master or downstream)"""
    auth.check_permission(current_user, "system.configure")

    # Validate parent panel if downstream
    if panel_data.panel_type == "DOWNSTREAM":
        if not panel_data.parent_panel_id:
            raise HTTPException(status_code=400, detail="Downstream panel requires parent_panel_id")
        if not panel_data.rs485_address:
            raise HTTPException(status_code=400, detail="Downstream panel requires rs485_address")

        parent = await db.get_panel(panel_data.parent_panel_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent panel not found")
        if parent['panel_type'] != 'MASTER':
            raise HTTPException(status_code=400, detail="Parent must be a MASTER panel")

    # Check if panel ID already exists
    existing = await db.get_panel(panel_data.panel_id)
    if existing:
        raise HTTPException(status_code=409, detail="Panel ID already exists")

    panel_id = await db.create_panel(
        panel_data.panel_id,
        panel_data.panel_name,
        panel_data.panel_type,
        panel_data.parent_panel_id,
        panel_data.rs485_address,
        panel_data.firmware_version
    )

    return await db.get_panel(panel_id)


@router.get("/panels")
async def get_all_panels(current_user: Dict = Depends(auth.get_current_user)):
    """Get all panels"""
    auth.check_permission(current_user, "door.read")
    return await db.get_all_panels()


@router.get("/panels/{panel_id}")
async def get_panel(
    panel_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get panel details"""
    auth.check_permission(current_user, "door.read")

    panel = await db.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    return panel


@router.put("/panels/{panel_id}")
async def update_panel(
    panel_id: int,
    panel_data: PanelUpdate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Update panel information"""
    auth.check_permission(current_user, "system.configure")

    panel = await db.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    update_data = {k: v for k, v in panel_data.dict().items() if v is not None}
    return await db.update_panel(panel_id, **update_data)


@router.delete("/panels/{panel_id}")
async def delete_panel(
    panel_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Delete a panel and all associated devices"""
    auth.check_permission(current_user, "system.configure")

    panel = await db.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    # Check if panel has downstream panels
    if panel['panel_type'] == 'MASTER':
        downstream = await db.get_downstream_panels(panel_id)
        if downstream:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete master panel with {len(downstream)} downstream panels"
            )

    await db.delete_panel(panel_id)
    return {"message": "Panel deleted successfully"}


@router.get("/panels/{panel_id}/downstream")
async def get_downstream_panels(
    panel_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get all downstream panels for a master panel"""
    auth.check_permission(current_user, "door.read")

    panel = await db.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    if panel['panel_type'] != 'MASTER':
        raise HTTPException(status_code=400, detail="Panel is not a master panel")

    return await db.get_downstream_panels(panel_id)


@router.get("/hardware-tree")
async def get_hardware_tree(current_user: Dict = Depends(auth.get_current_user)):
    """
    Get complete hardware tree with all panels, readers, I/O
    Returns hierarchical structure for tree visualization
    """
    auth.check_permission(current_user, "door.read")
    return await db.get_hardware_tree()


# Panel Readers
@router.post("/panels/{panel_id}/readers")
async def create_panel_reader(
    panel_id: int,
    reader_data: PanelReaderCreate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Add a reader to a panel"""
    auth.check_permission(current_user, "door.configure")

    panel = await db.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    reader_id = await db.create_panel_reader(
        reader_data.panel_id,
        reader_data.reader_address,
        reader_data.reader_name
    )

    return {"reader_id": reader_id, "message": "Reader created successfully"}


@router.get("/panels/{panel_id}/readers")
async def get_panel_readers(
    panel_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get all readers for a panel"""
    auth.check_permission(current_user, "door.read")

    panel = await db.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    return await db.get_panel_readers(panel_id)


# Panel Inputs
@router.post("/panels/{panel_id}/inputs")
async def create_panel_input(
    panel_id: int,
    input_data: PanelIOCreate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Add an input to a panel"""
    auth.check_permission(current_user, "door.configure")

    panel = await db.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    input_id = await db.create_panel_input(
        input_data.panel_id,
        input_data.number,
        input_data.name
    )

    return {"input_id": input_id, "message": "Input created successfully"}


@router.get("/panels/{panel_id}/inputs")
async def get_panel_inputs(
    panel_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get all inputs for a panel"""
    auth.check_permission(current_user, "door.read")

    panel = await db.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    return await db.get_panel_inputs(panel_id)


# Panel Outputs
@router.post("/panels/{panel_id}/outputs")
async def create_panel_output(
    panel_id: int,
    output_data: PanelIOCreate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Add an output to a panel"""
    auth.check_permission(current_user, "door.configure")

    panel = await db.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    output_id = await db.create_panel_output(
        output_data.panel_id,
        output_data.number,
        output_data.name
    )

    return {"output_id": output_id, "message": "Output created successfully"}


@router.get("/panels/{panel_id}/outputs")
async def get_panel_outputs(
    panel_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get all outputs for a panel"""
    auth.check_permission(current_user, "door.read")

    panel = await db.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    return await db.get_panel_outputs(panel_id)


# Panel Relays
@router.post("/panels/{panel_id}/relays")
async def create_panel_relay(
    panel_id: int,
    relay_data: PanelIOCreate,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Add a relay to a panel"""
    auth.check_permission(current_user, "door.configure")

    panel = await db.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    relay_id = await db.create_panel_relay(
        relay_data.panel_id,
        relay_data.number,
        relay_data.name
    )

    return {"relay_id": relay_id, "message": "Relay created successfully"}


@router.get("/panels/{panel_id}/relays")
async def get_panel_relays(
    panel_id: int,
    current_user: Dict = Depends(auth.get_current_user)
):
    """Get all relays for a panel"""
    auth.check_permission(current_user, "door.read")

    panel = await db.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    return await db.get_panel_relays(panel_id)
