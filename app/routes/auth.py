"""Authentication and API key management routes.

Provides user registration, login, logout, and API key CRUD operations.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.auth import (
    register_user,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_jwt,
    create_api_key,
    list_api_keys,
    revoke_api_key,
    get_user_by_id,
)

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Auth"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=200)


class LoginRequest(BaseModel):
    username: str = Field(..., max_length=100)
    password: str = Field(..., max_length=200)


class ApiKeyCreateRequest(BaseModel):
    label: str = Field("", max_length=100)
    expires_days: Optional[int] = Field(None, ge=1, le=365)


def _get_current_user(request: Request) -> Optional[dict]:
    """Extract current user from Authorization header (JWT)."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        payload = decode_jwt(token)
        if payload and payload.get("type") == "access":
            return {"id": payload["sub"], "username": payload.get("username"), "role": payload.get("role")}
    return None


def _require_auth(request: Request) -> dict:
    """Require authenticated user. Raises 401 if not authenticated."""
    user = _get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def _require_admin(request: Request) -> dict:
    """Require admin role. Raises 403 if not admin."""
    user = _require_auth(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.post("/auth/register")
async def register(body: RegisterRequest):
    """Register a new user account."""
    result = await register_user(body.username, body.password)
    if not result:
        raise HTTPException(status_code=409, detail="Username already taken")
    return {"ok": True, "user": result}


@router.post("/auth/login")
async def login(body: LoginRequest):
    """Authenticate and receive JWT tokens."""
    user = await authenticate_user(body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(user["id"], user["username"], user["role"])
    refresh_token = create_refresh_token(user["id"])
    return {
        "ok": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/auth/logout")
async def logout(request: Request):
    """Logout (client should discard tokens)."""
    return {"ok": True, "message": "Logged out"}


@router.post("/auth/refresh")
async def refresh_token(request: Request):
    """Refresh an access token using a refresh token."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Refresh token required")
    token = auth[7:]
    payload = decode_jwt(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = await get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access_token = create_access_token(user["id"], user["username"], user["role"])
    return {"ok": True, "access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me")
async def get_me(request: Request):
    """Get current user info."""
    user = _require_auth(request)
    return {"ok": True, "user": user}


# ── API Key Management ──


@router.post("/auth/api-keys")
async def create_key(body: ApiKeyCreateRequest, request: Request):
    """Create a new API key (authenticated users only)."""
    user = _require_auth(request)
    result = await create_api_key(user["id"], body.label, body.expires_days)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create API key")
    return {"ok": True, "api_key": result}


@router.get("/auth/api-keys")
async def list_keys(request: Request):
    """List API keys for the current user."""
    user = _require_auth(request)
    keys = await list_api_keys(user["id"])
    return {"ok": True, "keys": keys}


@router.delete("/auth/api-keys/{key_id}")
async def revoke_key(key_id: int, request: Request):
    """Revoke an API key."""
    user = _require_auth(request)
    success = await revoke_api_key(key_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"ok": True, "message": "API key revoked"}
