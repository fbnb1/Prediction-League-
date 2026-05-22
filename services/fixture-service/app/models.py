from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Round(Base):
    """A tournament stage (group stage, round of 32, ...)."""

    __tablename__ = "rounds"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    sequence: Mapped[int] = mapped_column(Integer)
    multiplier: Mapped[int] = mapped_column(Integer, default=1)


class Match(Base):
    """A match. Fixture is the source of truth for the result."""

    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    round_id: Mapped[int] = mapped_column(ForeignKey("rounds.id"))
    group_code: Mapped[str | None] = mapped_column(String(4))
    home_team: Mapped[str] = mapped_column(String(64))
    away_team: Mapped[str] = mapped_column(String(64))
    kickoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default="SCHEDULED")
    stake_minor: Mapped[int] = mapped_column(BigInteger)
    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
    outcome: Mapped[str | None] = mapped_column(String(4))


class Odds(Base):
    """Latest odds for a match (overwritten on each refresh). Display-only."""

    __tablename__ = "odds"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.id"), unique=True)
    home_odds: Mapped[float] = mapped_column(Numeric(6, 2))
    draw_odds: Mapped[float] = mapped_column(Numeric(6, 2))
    away_odds: Mapped[float] = mapped_column(Numeric(6, 2))
    # Asian-handicap line applied to the home team (e.g. -1.5). Signed:
    # positive = home gives the handicap, negative = home receives it.
    handicap: Mapped[float] = mapped_column(Numeric(4, 2), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MatchPick(Base):
    """
    Read-model projection of locked picks, fed by PickLocked events.
    Not owned data -- a CQRS projection. (match_id, user_id) is the natural
    key, so re-applying a redelivered event is idempotent.
    """

    __tablename__ = "match_picks"
    __table_args__ = (
        UniqueConstraint(
            "match_id", "user_id", "group_id", name="uq_match_picks_match_user_group"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[str] = mapped_column(String(64))
    group_id: Mapped[str] = mapped_column(String(64))
    bet_type: Mapped[str] = mapped_column(String(16), default="EUROPEAN")
    predicted_outcome: Mapped[str | None] = mapped_column(String(4))
    stake_minor: Mapped[int] = mapped_column(BigInteger)
    auto_loss: Mapped[bool] = mapped_column(Boolean, default=False)
    source_event_id: Mapped[str] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class OutboxEvent(Base):
    """
    Transactional outbox. A MatchSettled event is written here in the same
    transaction as the match result; a worker publishes it afterward.
    """

    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(primary_key=True)
    aggregate_id: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(64))
    routing_key: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
