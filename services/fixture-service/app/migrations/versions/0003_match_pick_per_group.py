"""key match_picks per group so a user can pick the same match in many groups

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE match_picks SET group_id = 'unknown' WHERE group_id IS NULL")
    op.alter_column("match_picks", "group_id", existing_type=sa.String(64), nullable=False)
    op.drop_constraint("uq_match_picks_match_user", "match_picks", type_="unique")
    op.create_unique_constraint(
        "uq_match_picks_match_user_group",
        "match_picks",
        ["match_id", "user_id", "group_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_match_picks_match_user_group", "match_picks", type_="unique")
    op.create_unique_constraint(
        "uq_match_picks_match_user", "match_picks", ["match_id", "user_id"]
    )
    op.alter_column("match_picks", "group_id", existing_type=sa.String(64), nullable=True)
