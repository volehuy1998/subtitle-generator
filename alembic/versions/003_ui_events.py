"""003: UI events table for frontend activity tracking.

Revision ID: 003
Revises: 002
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ui_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("session_id", sa.String(36), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("target", sa.String(100), nullable=True),
        sa.Column("task_id", sa.String(36), nullable=True),
        sa.Column("extra", sa.Text, nullable=True),
    )
    op.create_index("ix_ui_events_session", "ui_events", ["session_id"])
    op.create_index("ix_ui_events_type", "ui_events", ["event_type"])
    op.create_index("ix_ui_events_ts", "ui_events", ["timestamp"])
    op.create_index("ix_ui_events_target", "ui_events", ["target"])


def downgrade():
    op.drop_index("ix_ui_events_target", table_name="ui_events")
    op.drop_index("ix_ui_events_ts", table_name="ui_events")
    op.drop_index("ix_ui_events_type", table_name="ui_events")
    op.drop_index("ix_ui_events_session", table_name="ui_events")
    op.drop_table("ui_events")
