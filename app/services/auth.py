"""Authentication and authorization service.

Handles user registration, login, JWT token management, and API key operations.
"""

import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
import base64

from sqlalchemy import select, and_

from app.db.engine import get_session
from app.db.models import UserRecord, ApiKeyRecord

logger = logging.getLogger("subtitle-generator")

# JWT secret (generated at startup, configurable via env)
import os
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_ACCESS_EXPIRE_MINUTES", "60"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("JWT_REFRESH_EXPIRE_DAYS", "7"))


def _hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt (lightweight, no bcrypt dependency)."""
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}:{h}"


def _verify_password(password: str, stored: str) -> bool:
    """Verify password against stored hash."""
    if ":" not in stored:
        return False
    salt, expected = stored.split(":", 1)
    h = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return hmac.compare_digest(h, expected)


def _create_jwt(payload: dict, expires_delta: timedelta) -> str:
    """Create a simple JWT token (HS256, no external dependency)."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    payload["exp"] = int((datetime.now(timezone.utc) + expires_delta).timestamp())
    payload["iat"] = int(datetime.now(timezone.utc).timestamp())
    body = base64.urlsafe_b64encode(json.dumps(payload, default=str).encode()).rstrip(b"=").decode()
    signing_input = f"{header}.{body}"
    sig = hmac.new(JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    return f"{header}.{body}.{signature}"


def decode_jwt(token: str) -> Optional[dict]:
    """Decode and verify a JWT token. Returns payload or None if invalid."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, body, signature = parts
        # Verify signature
        signing_input = f"{header}.{body}"
        expected_sig = hmac.new(JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
        expected = base64.urlsafe_b64encode(expected_sig).rstrip(b"=").decode()
        if not hmac.compare_digest(signature, expected):
            return None
        # Decode payload
        padding = 4 - len(body) % 4
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * padding))
        # Check expiration
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def create_access_token(user_id: int, username: str, role: str) -> str:
    """Create a JWT access token."""
    return _create_jwt(
        {"sub": user_id, "username": username, "role": role, "type": "access"},
        timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: int) -> str:
    """Create a JWT refresh token."""
    return _create_jwt(
        {"sub": user_id, "type": "refresh"},
        timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(key.encode()).hexdigest()


async def register_user(username: str, password: str, role: str = "user") -> Optional[dict]:
    """Register a new user. Returns user dict or None if username taken."""
    try:
        async with get_session() as session:
            # Check existing
            result = await session.execute(
                select(UserRecord).where(UserRecord.username == username)
            )
            if result.scalar_one_or_none():
                return None
            user = UserRecord(
                username=username,
                password_hash=_hash_password(password),
                role=role,
            )
            session.add(user)
            await session.flush()
            return {"id": user.id, "username": user.username, "role": user.role}
    except Exception as e:
        logger.error(f"AUTH Registration failed: {e}")
        return None


async def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user by username/password. Returns user dict or None."""
    try:
        async with get_session() as session:
            result = await session.execute(
                select(UserRecord).where(
                    and_(UserRecord.username == username, UserRecord.is_active == 1)
                )
            )
            user = result.scalar_one_or_none()
            if not user or not _verify_password(password, user.password_hash):
                return None
            return {"id": user.id, "username": user.username, "role": user.role}
    except Exception as e:
        logger.error(f"AUTH Login failed: {e}")
        return None


async def get_user_by_id(user_id: int) -> Optional[dict]:
    """Get user by ID."""
    try:
        async with get_session() as session:
            result = await session.execute(
                select(UserRecord).where(UserRecord.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None
            return {"id": user.id, "username": user.username, "role": user.role, "is_active": bool(user.is_active)}
    except Exception:
        return None


async def create_api_key(owner_id: int, label: str = "", expires_days: int = None) -> Optional[dict]:
    """Create a new API key for a user. Returns the raw key (only shown once)."""
    try:
        raw_key = f"sk-{secrets.token_hex(24)}"
        key_hash_val = hash_api_key(raw_key)
        expires = None
        if expires_days:
            expires = datetime.now(timezone.utc) + timedelta(days=expires_days)

        async with get_session() as session:
            record = ApiKeyRecord(
                key_hash=key_hash_val,
                label=label or "default",
                owner_id=owner_id,
                expires_at=expires,
            )
            session.add(record)
            await session.flush()
            return {
                "id": record.id,
                "key": raw_key,
                "label": record.label,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "expires_at": record.expires_at.isoformat() if record.expires_at else None,
            }
    except Exception as e:
        logger.error(f"AUTH API key creation failed: {e}")
        return None


async def validate_db_api_key(raw_key: str) -> Optional[dict]:
    """Validate an API key against the database. Returns owner info or None."""
    try:
        key_hash_val = hash_api_key(raw_key)
        async with get_session() as session:
            result = await session.execute(
                select(ApiKeyRecord).where(
                    and_(ApiKeyRecord.key_hash == key_hash_val, ApiKeyRecord.is_active == 1)
                )
            )
            record = result.scalar_one_or_none()
            if not record:
                return None
            # Check expiration
            if record.expires_at and record.expires_at < datetime.now(timezone.utc):
                return None
            # Update last_used
            record.last_used = datetime.now(timezone.utc)
            # Get owner
            owner_result = await session.execute(
                select(UserRecord).where(UserRecord.id == record.owner_id)
            )
            owner = owner_result.scalar_one_or_none()
            if not owner or not owner.is_active:
                return None
            return {"user_id": owner.id, "username": owner.username, "role": owner.role}
    except Exception as e:
        logger.debug(f"AUTH API key validation error: {e}")
        return None


async def list_api_keys(owner_id: int) -> list[dict]:
    """List API keys for a user (without the actual key values)."""
    try:
        async with get_session() as session:
            result = await session.execute(
                select(ApiKeyRecord).where(
                    and_(ApiKeyRecord.owner_id == owner_id, ApiKeyRecord.is_active == 1)
                )
            )
            keys = result.scalars().all()
            return [{
                "id": k.id,
                "label": k.label,
                "created_at": k.created_at.isoformat() if k.created_at else None,
                "last_used": k.last_used.isoformat() if k.last_used else None,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            } for k in keys]
    except Exception:
        return []


async def revoke_api_key(key_id: int, owner_id: int) -> bool:
    """Revoke an API key. Returns True if successful."""
    try:
        async with get_session() as session:
            result = await session.execute(
                select(ApiKeyRecord).where(
                    and_(ApiKeyRecord.id == key_id, ApiKeyRecord.owner_id == owner_id)
                )
            )
            record = result.scalar_one_or_none()
            if not record:
                return False
            record.is_active = 0
            return True
    except Exception:
        return False
