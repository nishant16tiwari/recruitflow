"""add interview_cancelled event type

Revision ID: a1b2c3d4e5f6
Revises: 45b1be0b5b48
Create Date: 2026-09-05 00:00:00.000000

"""
from alembic import op

revision = 'a1b2c3d4e5f6'
down_revision = '45b1be0b5b48'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE history_event_type ADD VALUE IF NOT EXISTS 'INTERVIEW_CANCELLED'")


def downgrade() -> None:
    pass