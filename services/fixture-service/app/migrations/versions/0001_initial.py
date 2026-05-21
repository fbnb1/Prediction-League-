"""initial fixture schema

Revision ID: 0001
Revises:
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rounds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(16), nullable=False, unique=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
    )
    op.create_table(
        "matches",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("round_id", sa.Integer(), sa.ForeignKey("rounds.id"), nullable=False),
        sa.Column("group_code", sa.String(4)),
        sa.Column("home_team", sa.String(64), nullable=False),
        sa.Column("away_team", sa.String(64), nullable=False),
        sa.Column("kickoff_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="SCHEDULED"),
        sa.Column("stake_minor", sa.BigInteger(), nullable=False),
        sa.Column("home_score", sa.Integer()),
        sa.Column("away_score", sa.Integer()),
        sa.Column("outcome", sa.String(4)),
    )
    op.create_table(
        "odds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.String(64), sa.ForeignKey("matches.id"), nullable=False, unique=True),
        sa.Column("home_odds", sa.Numeric(6, 2), nullable=False),
        sa.Column("draw_odds", sa.Numeric(6, 2), nullable=False),
        sa.Column("away_odds", sa.Numeric(6, 2), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "match_picks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("group_id", sa.String(64)),
        sa.Column("predicted_outcome", sa.String(4)),
        sa.Column("stake_minor", sa.BigInteger(), nullable=False),
        sa.Column("auto_loss", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_event_id", sa.String(64), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("match_id", "user_id", name="uq_match_picks_match_user"),
    )
    op.create_index("idx_match_picks_match_id", "match_picks", ["match_id"])
    op.create_table(
        "outbox",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("aggregate_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("routing_key", sa.String(64), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "idx_outbox_unpublished",
        "outbox",
        ["id"],
        postgresql_where=sa.text("published_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_table("outbox")
    op.drop_index("idx_match_picks_match_id", table_name="match_picks")
    op.drop_table("match_picks")
    op.drop_table("odds")
    op.drop_table("matches")
    op.drop_table("rounds")
