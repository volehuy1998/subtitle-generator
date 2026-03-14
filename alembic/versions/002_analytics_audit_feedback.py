"""Analytics, audit log, and feedback tables.

Revision ID: 002
Revises: 001
Create Date: 2026-03-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Analytics events (replaces SQLite analytics_events)
    op.create_table(
        "analytics_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("data", sa.Text, nullable=True),
    )
    op.create_index("ix_analytics_events_type", "analytics_events", ["event_type"])
    op.create_index("ix_analytics_events_ts", "analytics_events", ["timestamp"])

    # Analytics daily aggregates (replaces SQLite analytics_daily)
    op.create_table(
        "analytics_daily",
        sa.Column("date", sa.String(10), primary_key=True),
        sa.Column("uploads", sa.Integer, server_default="0"),
        sa.Column("completed", sa.Integer, server_default="0"),
        sa.Column("failed", sa.Integer, server_default="0"),
        sa.Column("cancelled", sa.Integer, server_default="0"),
        sa.Column("total_processing_sec", sa.Float, server_default="0.0"),
        sa.Column("avg_file_size", sa.Integer, server_default="0"),
        sa.Column("data", sa.Text, server_default="{}"),
    )

    # Analytics time-series (replaces in-memory ring buffer)
    op.create_table(
        "analytics_timeseries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, unique=True),
        sa.Column("uploads", sa.Integer, server_default="0"),
        sa.Column("completed", sa.Integer, server_default="0"),
        sa.Column("failed", sa.Integer, server_default="0"),
        sa.Column("cancelled", sa.Integer, server_default="0"),
        sa.Column("total_processing_sec", sa.Float, server_default="0.0"),
        sa.Column("task_count", sa.Integer, server_default="0"),
    )
    op.create_index("ix_analytics_ts_timestamp", "analytics_timeseries", ["timestamp"])

    # Audit log (replaces audit.jsonl)
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("path", sa.String(512), nullable=True),
        sa.Column("details", sa.Text, nullable=True),
    )
    op.create_index("ix_audit_log_event", "audit_log", ["event_type"])
    op.create_index("ix_audit_log_ts", "audit_log", ["timestamp"])

    # Feedback (replaces feedback.jsonl)
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("task_id", sa.String(36), nullable=True),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_feedback_task", "feedback", ["task_id"])
    op.create_index("ix_feedback_created", "feedback", ["created_at"])


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("audit_log")
    op.drop_table("analytics_timeseries")
    op.drop_table("analytics_daily")
    op.drop_table("analytics_events")
