"""004: Users and API keys tables for authentication.

Revision ID: 004
Revises: 003
"""

import sqlalchemy as sa

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Integer, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("key_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("last_used", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("is_active", sa.Integer, server_default="1"),
    )
    op.create_index("ix_api_keys_hash", "api_keys", ["key_hash"])
    op.create_index("ix_api_keys_owner", "api_keys", ["owner_id"])


def downgrade():
    op.drop_index("ix_api_keys_owner", table_name="api_keys")
    op.drop_index("ix_api_keys_hash", table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
