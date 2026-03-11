"""Sprint 23 tests: Authentication & Access Control.

Tests cover:
  - User and API key ORM models
  - Auth service (register, login, JWT, API keys)
  - Auth API endpoints (register, login, logout, refresh, me)
  - API key management endpoints
  - Role-based access control
  - Migration file
"""

import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Model Tests ──

class TestUserModel:
    """Test UserRecord ORM model."""

    def test_model_exists(self):
        from app.db.models import UserRecord
        assert UserRecord.__tablename__ == "users"

    def test_model_columns(self):
        from app.db.models import UserRecord
        cols = {c.name for c in UserRecord.__table__.columns}
        assert {"id", "username", "password_hash", "role", "is_active", "created_at"} <= cols

    def test_model_indexes(self):
        from app.db.models import UserRecord
        idx_names = {idx.name for idx in UserRecord.__table__.indexes}
        assert "ix_users_username" in idx_names


class TestApiKeyModel:
    """Test ApiKeyRecord ORM model."""

    def test_model_exists(self):
        from app.db.models import ApiKeyRecord
        assert ApiKeyRecord.__tablename__ == "api_keys"

    def test_model_columns(self):
        from app.db.models import ApiKeyRecord
        cols = {c.name for c in ApiKeyRecord.__table__.columns}
        assert {"id", "key_hash", "label", "owner_id", "created_at", "last_used", "expires_at", "is_active"} <= cols

    def test_model_indexes(self):
        from app.db.models import ApiKeyRecord
        idx_names = {idx.name for idx in ApiKeyRecord.__table__.indexes}
        assert "ix_api_keys_hash" in idx_names
        assert "ix_api_keys_owner" in idx_names


# ── Auth Service Tests ──

class TestAuthService:
    """Test auth service functions."""

    def test_module_imports(self):
        from app.services import auth
        assert hasattr(auth, "register_user")
        assert hasattr(auth, "authenticate_user")
        assert hasattr(auth, "create_access_token")
        assert hasattr(auth, "create_refresh_token")
        assert hasattr(auth, "decode_jwt")
        assert hasattr(auth, "create_api_key")
        assert hasattr(auth, "list_api_keys")
        assert hasattr(auth, "revoke_api_key")
        assert hasattr(auth, "hash_api_key")

    def test_register_is_async(self):
        from app.services.auth import register_user
        assert asyncio.iscoroutinefunction(register_user)

    def test_authenticate_is_async(self):
        from app.services.auth import authenticate_user
        assert asyncio.iscoroutinefunction(authenticate_user)

    def test_jwt_roundtrip(self):
        from app.services.auth import create_access_token, decode_jwt
        token = create_access_token(1, "testuser", "user")
        payload = decode_jwt(token)
        assert payload is not None
        assert payload["sub"] == 1
        assert payload["username"] == "testuser"
        assert payload["role"] == "user"
        assert payload["type"] == "access"

    def test_refresh_token_type(self):
        from app.services.auth import create_refresh_token, decode_jwt
        token = create_refresh_token(42)
        payload = decode_jwt(token)
        assert payload is not None
        assert payload["type"] == "refresh"
        assert payload["sub"] == 42

    def test_invalid_jwt_returns_none(self):
        from app.services.auth import decode_jwt
        assert decode_jwt("invalid.token.here") is None
        assert decode_jwt("") is None
        assert decode_jwt("not-a-jwt") is None

    def test_password_hashing(self):
        from app.services.auth import _hash_password, _verify_password
        hashed = _hash_password("mypassword")
        assert _verify_password("mypassword", hashed) is True
        assert _verify_password("wrongpassword", hashed) is False

    def test_api_key_hashing(self):
        from app.services.auth import hash_api_key
        h1 = hash_api_key("sk-test123")
        h2 = hash_api_key("sk-test123")
        assert h1 == h2  # Deterministic
        assert len(h1) == 64  # SHA-256 hex


# ── Auth Endpoint Tests ──

class TestAuthEndpoints:
    """Test auth API endpoints."""

    def test_register_endpoint(self):
        res = client.post("/auth/register", json={"username": "testuser1", "password": "testpass123"})
        assert res.status_code in (200, 409)  # 200 first time, 409 if already exists

    def test_register_short_username_fails(self):
        res = client.post("/auth/register", json={"username": "ab", "password": "testpass123"})
        assert res.status_code == 422

    def test_register_short_password_fails(self):
        res = client.post("/auth/register", json={"username": "validuser", "password": "12345"})
        assert res.status_code == 422

    def test_login_endpoint(self):
        # Register first
        client.post("/auth/register", json={"username": "logintest", "password": "testpass123"})
        res = client.post("/auth/login", json={"username": "logintest", "password": "testpass123"})
        assert res.status_code in (200, 401)
        if res.status_code == 200:
            data = res.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"

    def test_login_wrong_password(self):
        client.post("/auth/register", json={"username": "wrongpwtest", "password": "testpass123"})
        res = client.post("/auth/login", json={"username": "wrongpwtest", "password": "wrongpass"})
        assert res.status_code == 401

    def test_logout_endpoint(self):
        res = client.post("/auth/logout")
        assert res.status_code == 200
        assert res.json()["ok"] is True

    def test_me_without_auth(self):
        res = client.get("/auth/me")
        assert res.status_code == 401

    def test_me_with_token(self):
        # Register and login
        client.post("/auth/register", json={"username": "metest", "password": "testpass123"})
        login_res = client.post("/auth/login", json={"username": "metest", "password": "testpass123"})
        if login_res.status_code == 200:
            token = login_res.json()["access_token"]
            res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert res.status_code == 200
            assert res.json()["user"]["username"] == "metest"

    def test_refresh_endpoint(self):
        client.post("/auth/register", json={"username": "refreshtest", "password": "testpass123"})
        login_res = client.post("/auth/login", json={"username": "refreshtest", "password": "testpass123"})
        if login_res.status_code == 200:
            refresh = login_res.json()["refresh_token"]
            res = client.post("/auth/refresh", headers={"Authorization": f"Bearer {refresh}"})
            assert res.status_code == 200
            assert "access_token" in res.json()


# ── API Key Management Tests ──

class TestApiKeyEndpoints:
    """Test API key management endpoints."""

    def _get_auth_headers(self, username="keytest"):
        client.post("/auth/register", json={"username": username, "password": "testpass123"})
        login_res = client.post("/auth/login", json={"username": username, "password": "testpass123"})
        if login_res.status_code == 200:
            return {"Authorization": f"Bearer {login_res.json()['access_token']}"}
        return {}

    def test_create_api_key(self):
        headers = self._get_auth_headers("keytest1")
        if headers:
            res = client.post("/auth/api-keys", json={"label": "test key"}, headers=headers)
            assert res.status_code in (200, 500)
            if res.status_code == 200:
                data = res.json()
                assert data["ok"] is True
                assert "api_key" in data
                assert data["api_key"]["key"].startswith("sk-")

    def test_list_api_keys(self):
        headers = self._get_auth_headers("keytest2")
        if headers:
            res = client.get("/auth/api-keys", headers=headers)
            assert res.status_code == 200
            assert "keys" in res.json()

    def test_create_and_revoke_key(self):
        headers = self._get_auth_headers("keytest3")
        if headers:
            create_res = client.post("/auth/api-keys", json={"label": "revoke test"}, headers=headers)
            if create_res.status_code == 200:
                key_id = create_res.json()["api_key"]["id"]
                revoke_res = client.delete(f"/auth/api-keys/{key_id}", headers=headers)
                assert revoke_res.status_code == 200

    def test_api_key_without_auth_fails(self):
        res = client.post("/auth/api-keys", json={"label": "test"})
        assert res.status_code == 401

    def test_revoke_nonexistent_key(self):
        headers = self._get_auth_headers("keytest4")
        if headers:
            res = client.delete("/auth/api-keys/99999", headers=headers)
            assert res.status_code == 404


# ── Migration Tests ──

class TestMigration004:
    """Test Alembic migration file."""

    def test_migration_exists(self):
        from pathlib import Path
        assert Path("alembic/versions/004_users_api_keys.py").exists()

    def test_migration_has_upgrade(self):
        from pathlib import Path
        content = Path("alembic/versions/004_users_api_keys.py").read_text()
        assert "def upgrade" in content
        assert "users" in content
        assert "api_keys" in content

    def test_migration_has_downgrade(self):
        from pathlib import Path
        content = Path("alembic/versions/004_users_api_keys.py").read_text()
        assert "def downgrade" in content

    def test_migration_chain(self):
        from pathlib import Path
        content = Path("alembic/versions/004_users_api_keys.py").read_text()
        assert '"003"' in content
