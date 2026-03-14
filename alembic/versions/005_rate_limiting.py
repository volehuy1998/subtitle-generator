"""005: Brute force events and IP lists tables for rate limiting persistence.

Revision ID: 005
Revises: 004
"""

import sqlalchemy as sa

from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "brute_force_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ip", sa.String(45), nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("path", sa.String(512), nullable=True),
        sa.Column("blocked_until", sa.DateTime, nullable=True),
    )
    op.create_index("ix_brute_force_ip", "brute_force_events", ["ip"])
    op.create_index("ix_brute_force_ts", "brute_force_events", ["timestamp"])

    op.create_table(
        "ip_lists",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ip", sa.String(45), nullable=False),
        sa.Column("list_type", sa.String(10), nullable=False),  # allow, block
        sa.Column("reason", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ip_lists_ip", "ip_lists", ["ip"])
    op.create_index("ix_ip_lists_type", "ip_lists", ["list_type"])


def downgrade():
    op.drop_index("ix_ip_lists_type", table_name="ip_lists")
    op.drop_index("ix_ip_lists_ip", table_name="ip_lists")
    op.drop_table("ip_lists")
    op.drop_index("ix_brute_force_ts", table_name="brute_force_events")
    op.drop_index("ix_brute_force_ip", table_name="brute_force_events")
    op.drop_table("brute_force_events")
