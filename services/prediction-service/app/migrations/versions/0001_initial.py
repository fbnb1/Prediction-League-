"""initial prediction schema

Revision ID: 0001
Revises:
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "groups",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("owner_user_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "group_members",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("group_id", sa.String(64), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_members"),
    )
    op.create_table(
        "picks",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("group_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("match_id", sa.String(64), nullable=False),
        sa.Column("predicted_outcome", sa.String(4)),
        sa.Column("stake_minor", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="OPEN"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("group_id", "user_id", "match_id", name="uq_picks_group_user_match"),
    )
    op.create_index("idx_picks_match_id", "picks", ["match_id"])
    op.create_table(
        "match_ref",
        sa.Column("match_id", sa.String(64), primary_key=True),
        sa.Column("home_team", sa.String(64), nullable=False),
        sa.Column("away_team", sa.String(64), nullable=False),
        sa.Column("kickoff_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lock_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stake_minor", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="SCHEDULED"),
    )


def downgrade() -> None:
    op.drop_table("match_ref")
    op.drop_index("idx_picks_match_id", table_name="picks")
    op.drop_table("picks")
    op.drop_table("group_members")
    op.drop_table("groups")
    op.drop_table("users")
