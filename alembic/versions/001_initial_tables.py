"""Initial tables: tasks and sessions.

Revision ID: 001
Revises: None
Create Date: 2026-03-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("last_seen", sa.DateTime, nullable=False),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
    )
    op.create_index("ix_sessions_last_seen", "sessions", ["last_seen"])

    op.create_table(
        "tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("language_requested", sa.String(10), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("model_size", sa.String(20), nullable=True),
        sa.Column("device", sa.String(10), nullable=True),
        sa.Column("percent", sa.Float, server_default="0.0"),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("file_size", sa.Integer, nullable=True),
        sa.Column("file_size_fmt", sa.String(20), nullable=True),
        sa.Column("audio_size_fmt", sa.String(20), nullable=True),
        sa.Column("duration", sa.Float, nullable=True),
        sa.Column("segments", sa.Text, nullable=True),
        sa.Column("word_timestamps", sa.Integer, server_default="0"),
        sa.Column("diarize", sa.Integer, server_default="0"),
        sa.Column("speakers", sa.Integer, nullable=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("sessions.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_session_id", "tasks", ["session_id"])
    op.create_index("ix_tasks_session_status", "tasks", ["session_id", "status"])
    op.create_index("ix_tasks_created_at", "tasks", ["created_at"])


def downgrade() -> None:
    op.drop_table("tasks")
    op.drop_table("sessions")
