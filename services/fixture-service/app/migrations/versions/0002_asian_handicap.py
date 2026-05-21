"""add Asian-handicap line to odds and bet_type to match_picks

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
    op.add_column(
        "odds",
        sa.Column("handicap", sa.Numeric(4, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "match_picks",
        sa.Column("bet_type", sa.String(16), nullable=False, server_default="EUROPEAN"),
    )


def downgrade() -> None:
    op.drop_column("match_picks", "bet_type")
    op.drop_column("odds", "handicap")
