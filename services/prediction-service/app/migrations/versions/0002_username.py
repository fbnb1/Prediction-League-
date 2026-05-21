"""switch user identity from email to username

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "email",
        new_column_name="username",
        type_=sa.String(64),
        existing_type=sa.String(255),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "username",
        new_column_name="email",
        type_=sa.String(255),
        existing_type=sa.String(64),
        existing_nullable=False,
    )
