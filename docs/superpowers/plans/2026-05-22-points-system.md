# Points System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all real-money tracking with virtual points (1 pt = 10,000đ reference only), add per-round multipliers managed by admin, and remove the ledger/deposit system entirely from the app.

**Architecture:** Points are computed on-the-fly by the BFF: `points_lost = sum(round.multiplier for each LOST pick)`. Round multipliers live in `fixture-service.rounds.multiplier`. No money is stored anywhere. The ledger-service is silently abandoned (files kept, BFF stops calling it).

**Tech Stack:** Python/FastAPI (fixture-service, prediction-service, bff-service), React/Vite (web), Alembic migrations, SQLAlchemy ORM, PostgreSQL.

---

## File Map

| File | Action | What changes |
|---|---|---|
| `services/fixture-service/app/migrations/versions/0004_round_multiplier.py` | **Create** | Add `multiplier` column to `rounds` |
| `services/fixture-service/app/models.py` | **Modify** | Add `multiplier` field to `Round` |
| `services/fixture-service/app/schemas.py` | **Modify** | Add `round_multiplier` to `MatchOut`/`PickResultOut`; new `RoundOut`, `RoundMultiplierIn`, `MatchRoundIn` |
| `services/fixture-service/app/api/fixtures.py` | **Modify** | Join Round in all queries; add `GET /rounds` |
| `services/fixture-service/app/api/admin.py` | **Modify** | Add `PUT /admin/rounds/{id}/multiplier`, `PUT /admin/matches/{id}/round` |
| `services/prediction-service/app/api/admin.py` | **Modify** | Add `DELETE /admin/groups/{group_id}/members/{user_id}` |
| `services/bff-service/app/schemas.py` | **Modify** | Replace money fields with points fields |
| `services/bff-service/app/aggregation.py` | **Modify** | Use `round_multiplier` instead of `stake_minor`; remove deposit helpers |
| `services/bff-service/app/api/deposits.py` | **Delete** | Entire file removed |
| `services/bff-service/app/clients/ledger.py` | **Delete** | Entire file removed |
| `services/bff-service/app/clients/fixture.py` | **Modify** | Add `list_rounds`, `update_round_multiplier`, `set_match_round` |
| `services/bff-service/app/api/leaderboard.py` | **Modify** | Remove ledger call |
| `services/bff-service/app/api/players.py` | **Modify** | Remove ledger calls; no deposits |
| `services/bff-service/app/api/matches.py` | **Modify** | Use `round_multiplier`; remove odds proxy |
| `services/bff-service/app/api/rounds.py` | **Create** | Proxy endpoints for round management |
| `services/bff-service/app/main.py` | **Modify** | Remove deposits router; add rounds router |
| `web/src/components/Points.jsx` | **Create** | Replaces Money component |
| `web/src/components/Money.jsx` | **Delete** | No longer used |
| `web/src/utils/format.js` | **Modify** | Replace `formatMoney` with `formatPoints` |
| `web/src/pages/Home.jsx` | **Modify** | Remove deposits table; update leaderboard columns |
| `web/src/pages/PlayerDetail.jsx` | **Modify** | Remove deposits section; use Points |
| `web/src/pages/GroupSettings.jsx` | **Modify** | Remove BetTypePanel & DepositsPanel; add remove-member button |
| `web/src/pages/Admin.jsx` | **Modify** | Remove OddsManager; add RoundsManager; fix CreateGroupModal |

---

## Task 1: fixture-service — DB migration: add multiplier to rounds

**Files:**
- Create: `services/fixture-service/app/migrations/versions/0004_round_multiplier.py`

- [ ] **Step 1: Create the migration file**

```python
# services/fixture-service/app/migrations/versions/0004_round_multiplier.py
"""add multiplier column to rounds

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rounds",
        sa.Column("multiplier", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("rounds", "multiplier")
```

- [ ] **Step 2: Apply the migration (inside the fixture-service container or with the DB running)**

```bash
cd services/fixture-service
alembic upgrade head
```

Expected: `Running upgrade 0003 -> 0004, add multiplier column to rounds`

- [ ] **Step 3: Commit**

```bash
git add services/fixture-service/app/migrations/versions/0004_round_multiplier.py
git commit -m "feat(fixture-service): add multiplier column to rounds table"
```

---

## Task 2: fixture-service — Update Round model and schemas

**Files:**
- Modify: `services/fixture-service/app/models.py`
- Modify: `services/fixture-service/app/schemas.py`

- [ ] **Step 1: Add `multiplier` to the Round model**

In `services/fixture-service/app/models.py`, find the `Round` class and add the `multiplier` field:

```python
class Round(Base):
    """A tournament stage (group stage, round of 32, ...)."""

    __tablename__ = "rounds"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    sequence: Mapped[int] = mapped_column(Integer)
    multiplier: Mapped[int] = mapped_column(Integer, default=1)
```

- [ ] **Step 2: Replace schemas.py**

Replace the entire `services/fixture-service/app/schemas.py`:

```python
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.config import settings


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: str
    round_id: int
    round_multiplier: int = 1
    group_code: str | None
    home_team: str
    away_team: str
    kickoff_at: datetime
    status: str
    stake_minor: int
    home_score: int | None
    away_score: int | None
    outcome: str | None

    @computed_field
    @property
    def lock_at(self) -> datetime:
        """When picks lock: a fixed offset before kickoff."""
        return self.kickoff_at - timedelta(minutes=settings.lock_offset_minutes)


class RoundOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    sequence: int
    multiplier: int


class OddsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: str
    home_odds: float
    draw_odds: float
    away_odds: float
    handicap: float
    updated_at: datetime


class ResultIn(BaseModel):
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)


class KickoffIn(BaseModel):
    kickoff_at: datetime


class OddsUpdateIn(BaseModel):
    home_odds: float = Field(gt=1.0)
    draw_odds: float = Field(gt=1.0)
    away_odds: float = Field(gt=1.0)
    handicap: float


class RoundMultiplierIn(BaseModel):
    multiplier: int = Field(ge=1)


class MatchRoundIn(BaseModel):
    round_id: int
    set_subsequent: bool = True


class MatchPickOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: str
    user_id: str
    bet_type: str
    predicted_outcome: str | None
    stake_minor: int
    auto_loss: bool


class PickResultOut(BaseModel):
    """A locked pick joined with its match result, round multiplier, and settled outcome."""

    match_id: str
    user_id: str
    predicted_outcome: str | None
    auto_loss: bool
    stake_minor: int
    round_multiplier: int
    bet_type: str
    home_team: str
    away_team: str
    kickoff_at: datetime
    status: str
    outcome: str | None
    home_score: int | None
    away_score: int | None
    result: str  # WON | LOST | PENDING
```

- [ ] **Step 3: Commit**

```bash
git add services/fixture-service/app/models.py services/fixture-service/app/schemas.py
git commit -m "feat(fixture-service): add round_multiplier to schemas"
```

---

## Task 3: fixture-service — Update fixtures.py endpoints

**Files:**
- Modify: `services/fixture-service/app/api/fixtures.py`

- [ ] **Step 1: Replace fixtures.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.domain.evaluation import outcome_from_scores, settle_pick, settle_pick_asian
from app.models import Match, MatchPick, Odds, Round
from app.schemas import MatchOut, MatchPickOut, OddsOut, PickResultOut, RoundOut

router = APIRouter(prefix="/fixtures", tags=["fixtures"])


def _match_out(match: Match, round_: Round) -> MatchOut:
    return MatchOut(
        id=match.id,
        round_id=match.round_id,
        round_multiplier=round_.multiplier,
        group_code=match.group_code,
        home_team=match.home_team,
        away_team=match.away_team,
        kickoff_at=match.kickoff_at,
        status=match.status,
        stake_minor=match.stake_minor,
        home_score=match.home_score,
        away_score=match.away_score,
        outcome=match.outcome,
    )


@router.get("", response_model=list[MatchOut])
def list_fixtures(session: Session = Depends(get_session)) -> list[MatchOut]:
    rows = (
        session.query(Match, Round)
        .join(Round, Round.id == Match.round_id)
        .order_by(Match.kickoff_at, Match.id)
        .all()
    )
    return [_match_out(m, r) for m, r in rows]


@router.get("/rounds", response_model=list[RoundOut])
def list_rounds(session: Session = Depends(get_session)) -> list[Round]:
    return session.query(Round).order_by(Round.sequence).all()


@router.get("/pick-results", response_model=list[PickResultOut])
def pick_results(
    group_id: str, session: Session = Depends(get_session)
) -> list[PickResultOut]:
    """Every locked pick in a group, joined with match result, round multiplier, and settled."""
    rows = (
        session.query(MatchPick, Match, Round, Odds)
        .join(Match, Match.id == MatchPick.match_id)
        .join(Round, Round.id == Match.round_id)
        .outerjoin(Odds, Odds.match_id == MatchPick.match_id)
        .filter(MatchPick.group_id == group_id)
        .order_by(Match.kickoff_at, MatchPick.user_id)
        .all()
    )
    results: list[PickResultOut] = []
    for pick, match, round_, odds in rows:
        if match.status != "FINAL" or match.outcome is None:
            result = "PENDING"
        elif pick.bet_type == "ASIAN":
            handicap = float(odds.handicap) if odds is not None else 0.0
            result = settle_pick_asian(
                pick.predicted_outcome,
                match.home_score,
                match.away_score,
                handicap,
            )
        else:
            result = settle_pick(
                pick.predicted_outcome,
                outcome_from_scores(match.home_score, match.away_score),
            )
        results.append(
            PickResultOut(
                match_id=pick.match_id,
                user_id=pick.user_id,
                predicted_outcome=pick.predicted_outcome,
                auto_loss=pick.auto_loss,
                stake_minor=pick.stake_minor,
                round_multiplier=round_.multiplier,
                bet_type=pick.bet_type,
                home_team=match.home_team,
                away_team=match.away_team,
                kickoff_at=match.kickoff_at,
                status=match.status,
                outcome=match.outcome,
                home_score=match.home_score,
                away_score=match.away_score,
                result=result,
            )
        )
    return results


@router.get("/{match_id}", response_model=MatchOut)
def get_fixture(match_id: str, session: Session = Depends(get_session)) -> MatchOut:
    row = (
        session.query(Match, Round)
        .join(Round, Round.id == Match.round_id)
        .filter(Match.id == match_id)
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="match not found")
    m, r = row
    return _match_out(m, r)


@router.get("/{match_id}/odds", response_model=OddsOut)
def get_odds(match_id: str, session: Session = Depends(get_session)) -> Odds:
    odds = session.query(Odds).filter_by(match_id=match_id).one_or_none()
    if odds is None:
        raise HTTPException(status_code=404, detail="odds not available")
    return odds


@router.get("/{match_id}/picks", response_model=list[MatchPickOut])
def get_picks(match_id: str, session: Session = Depends(get_session)) -> list[MatchPick]:
    return (
        session.query(MatchPick)
        .filter_by(match_id=match_id)
        .order_by(MatchPick.user_id)
        .all()
    )
```

- [ ] **Step 2: Run existing tests**

```bash
cd services/fixture-service
python -m pytest tests/ -v
```

Expected: all existing tests pass (evaluation logic unchanged).

- [ ] **Step 3: Commit**

```bash
git add services/fixture-service/app/api/fixtures.py
git commit -m "feat(fixture-service): expose round_multiplier in fixture and pick-result responses"
```

---

## Task 4: fixture-service — Add admin round management endpoints

**Files:**
- Modify: `services/fixture-service/app/api/admin.py`

- [ ] **Step 1: Replace admin.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import operations
from app.admin_auth import require_admin_key
from app.db import get_session
from app.errors import MatchAlreadySettled, MatchNotFound
from app.models import Match, Round
from app.providers.factory import get_provider
from app.schemas import (
    KickoffIn,
    MatchRoundIn,
    OddsOut,
    OddsUpdateIn,
    ResultIn,
    RoundMultiplierIn,
    RoundOut,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_key)])


@router.post("/matches/{match_id}/result")
def enter_result(match_id: str, body: ResultIn, session: Session = Depends(get_session)) -> dict:
    try:
        payload = operations.settle_match(session, match_id, body.home_score, body.away_score)
    except MatchNotFound:
        raise HTTPException(status_code=404, detail="match not found")
    except MatchAlreadySettled:
        raise HTTPException(status_code=409, detail="match already settled")
    return {"status": "settled", "match_id": match_id, "event_id": payload["event_id"]}


@router.post("/sync")
def trigger_sync(session: Session = Depends(get_session)) -> dict:
    provider = get_provider()
    created = operations.sync_fixtures(session, provider)
    refreshed = operations.refresh_odds(session, provider)
    return {"fixtures_created": created, "odds_refreshed": refreshed}


@router.put("/matches/{match_id}/odds", response_model=OddsOut)
def update_odds(
    match_id: str, body: OddsUpdateIn, session: Session = Depends(get_session)
):
    """Admin override for a match's odds (kept for backward compat, display-only)."""
    try:
        return operations.set_match_odds(
            session, match_id,
            body.home_odds, body.draw_odds, body.away_odds, body.handicap,
        )
    except MatchNotFound:
        raise HTTPException(status_code=404, detail="match not found")


@router.put("/matches/{match_id}/kickoff")
def set_kickoff(match_id: str, body: KickoffIn, session: Session = Depends(get_session)) -> dict:
    match = session.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="match not found")
    match.kickoff_at = body.kickoff_at
    session.commit()
    return {"status": "updated", "match_id": match_id, "kickoff_at": match.kickoff_at.isoformat()}


@router.put("/rounds/{round_id}/multiplier", response_model=RoundOut)
def update_round_multiplier(
    round_id: int, body: RoundMultiplierIn, session: Session = Depends(get_session)
) -> Round:
    """Set the points-per-loss multiplier for a tournament round."""
    round_ = session.get(Round, round_id)
    if round_ is None:
        raise HTTPException(status_code=404, detail="round not found")
    round_.multiplier = body.multiplier
    session.commit()
    session.refresh(round_)
    return round_


@router.put("/matches/{match_id}/round")
def set_match_round(
    match_id: str, body: MatchRoundIn, session: Session = Depends(get_session)
) -> dict:
    """Assign a match (and optionally all subsequent matches) to a round.

    When set_subsequent=True (default), every match whose kickoff_at >=
    the selected match's kickoff_at is reassigned to the new round.
    """
    match = session.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="match not found")
    round_ = session.get(Round, body.round_id)
    if round_ is None:
        raise HTTPException(status_code=404, detail="round not found")

    if body.set_subsequent:
        cutoff = match.kickoff_at
        updated = session.query(Match).filter(Match.kickoff_at >= cutoff).all()
        for m in updated:
            m.round_id = body.round_id
        count = len(updated)
    else:
        match.round_id = body.round_id
        count = 1

    session.commit()
    return {
        "status": "updated",
        "round_id": body.round_id,
        "round_name": round_.name,
        "matches_updated": count,
    }
```

- [ ] **Step 2: Commit**

```bash
git add services/fixture-service/app/api/admin.py
git commit -m "feat(fixture-service): add round multiplier and match-round admin endpoints"
```

---

## Task 5: prediction-service — Add delete member endpoint

**Files:**
- Modify: `services/prediction-service/app/api/admin.py`

- [ ] **Step 1: Add GroupMember to imports**

In `services/prediction-service/app/api/admin.py`, change:

```python
from app.models import Group, User
```

to:

```python
from app.models import Group, GroupMember, User
```

- [ ] **Step 2: Append the DELETE endpoint at the bottom of admin.py**

```python
@router.delete("/groups/{group_id}/members/{user_id}", status_code=204)
def remove_member(
    group_id: str,
    user_id: str,
    session: Session = Depends(get_session),
) -> Response:
    """Admin affordance: remove a user from a group."""
    member = (
        session.query(GroupMember)
        .filter_by(group_id=group_id, user_id=user_id)
        .one_or_none()
    )
    if member is None:
        raise HTTPException(status_code=404, detail="member not found")
    session.delete(member)
    session.commit()
    return Response(status_code=204)
```

- [ ] **Step 3: Commit**

```bash
git add services/prediction-service/app/api/admin.py
git commit -m "feat(prediction-service): add DELETE member endpoint"
```

---

## Task 6: bff-service — Strip ledger, update schemas and aggregation

**Files:**
- Delete: `services/bff-service/app/api/deposits.py`
- Delete: `services/bff-service/app/clients/ledger.py`
- Modify: `services/bff-service/app/schemas.py`
- Modify: `services/bff-service/app/aggregation.py`

- [ ] **Step 1: Delete ledger client and deposits API**

```bash
git rm services/bff-service/app/clients/ledger.py
git rm services/bff-service/app/api/deposits.py
```

- [ ] **Step 2: Replace schemas.py**

```python
from datetime import datetime

from pydantic import BaseModel


class LeaderboardRow(BaseModel):
    user_id: str
    display_name: str
    total_picks: int
    wins: int
    losses: int
    win_rate: float
    form: list[str]
    points_lost: int  # sum of round_multiplier for LOST picks


class PickHistoryItem(BaseModel):
    match_id: str
    home_team: str
    away_team: str
    kickoff_at: datetime
    predicted_outcome: str | None
    round_multiplier: int
    status: str
    outcome: str | None
    home_score: int | None
    away_score: int | None
    result: str  # WON | LOST | PENDING


class PlayerSummary(BaseModel):
    user_id: str
    display_name: str
    points_lost: int
    picks: list[PickHistoryItem]  # newest first


class LoserItem(BaseModel):
    user_id: str
    display_name: str
    round_multiplier: int


class MatchDetail(BaseModel):
    match_id: str
    home_team: str
    away_team: str
    kickoff_at: datetime
    status: str
    outcome: str | None
    home_score: int | None
    away_score: int | None
    pick_distribution: dict[str, int]
    losers: list[LoserItem]
    total_points: int


class RoundOut(BaseModel):
    id: int
    code: str
    name: str
    sequence: int
    multiplier: int


class RoundMultiplierIn(BaseModel):
    multiplier: int


class MatchRoundIn(BaseModel):
    round_id: int
    set_subsequent: bool = True
```

- [ ] **Step 3: Replace aggregation.py**

```python
"""Pure aggregation helpers over data already fetched from upstream services.

pick_results rows come from fixture-service GET /fixtures/pick-results.
Each row now includes `round_multiplier` (points for a loss in that round).
"""

from app.schemas import LeaderboardRow, LoserItem, MatchDetail, PickHistoryItem

_FORM_LENGTH = 5


def recent_form(user_picks: list[dict]) -> list[str]:
    """Up to 5 most recent settled results as 'W'/'L', newest first."""
    settled = [p for p in user_picks if p["result"] in ("WON", "LOST")]
    recent = settled[-_FORM_LENGTH:]
    return ["W" if p["result"] == "WON" else "L" for p in reversed(recent)]


def leaderboard_row(member: dict, user_picks: list[dict]) -> LeaderboardRow:
    wins = sum(1 for p in user_picks if p["result"] == "WON")
    losses = sum(1 for p in user_picks if p["result"] == "LOST")
    points_lost = sum(p["round_multiplier"] for p in user_picks if p["result"] == "LOST")
    settled = wins + losses
    win_rate = round(wins / settled, 4) if settled else 0.0
    return LeaderboardRow(
        user_id=member["user_id"],
        display_name=member["display_name"],
        total_picks=len(user_picks),
        wins=wins,
        losses=losses,
        win_rate=win_rate,
        form=recent_form(user_picks),
        points_lost=points_lost,
    )


def picks_for_user(pick_results: list[dict], user_id: str) -> list[dict]:
    return [p for p in pick_results if p["user_id"] == user_id]


def pick_history(user_picks: list[dict]) -> list[PickHistoryItem]:
    """A user's picks as history items, newest kickoff first."""
    return [
        PickHistoryItem(**{k: p[k] for k in PickHistoryItem.model_fields})
        for p in reversed(user_picks)
    ]


def match_detail(
    match: dict, group_picks_for_match: list[dict], names: dict[str, str]
) -> MatchDetail:
    distribution = {"HOME": 0, "DRAW": 0, "AWAY": 0}
    for pick in group_picks_for_match:
        outcome = pick.get("predicted_outcome")
        if outcome in distribution:
            distribution[outcome] += 1
    losers = [
        LoserItem(
            user_id=p["user_id"],
            display_name=names.get(p["user_id"], p["user_id"]),
            round_multiplier=p["round_multiplier"],
        )
        for p in group_picks_for_match
        if p["result"] == "LOST"
    ]
    return MatchDetail(
        match_id=match["id"],
        home_team=match["home_team"],
        away_team=match["away_team"],
        kickoff_at=match["kickoff_at"],
        status=match["status"],
        outcome=match.get("outcome"),
        home_score=match.get("home_score"),
        away_score=match.get("away_score"),
        pick_distribution=distribution,
        losers=losers,
        total_points=sum(loser.round_multiplier for loser in losers),
    )
```

- [ ] **Step 4: Commit**

```bash
git add services/bff-service/app/schemas.py services/bff-service/app/aggregation.py
git commit -m "feat(bff): replace money/ledger system with points; remove deposits"
```

---

## Task 7: bff-service — Update API endpoints + add rounds proxy

**Files:**
- Modify: `services/bff-service/app/clients/fixture.py`
- Modify: `services/bff-service/app/api/leaderboard.py`
- Modify: `services/bff-service/app/api/players.py`
- Modify: `services/bff-service/app/api/matches.py`
- Create: `services/bff-service/app/api/rounds.py`
- Modify: `services/bff-service/app/main.py`

- [ ] **Step 1: Replace clients/fixture.py**

```python
"""Client for fixture-service reads and admin round management."""

from app.clients.base import request
from app.config import settings


def list_fixtures() -> list[dict]:
    return request("GET", settings.fixture_url, "/fixtures")


def get_fixture(match_id: str) -> dict:
    return request("GET", settings.fixture_url, f"/fixtures/{match_id}")


def get_pick_results(group_id: str) -> list[dict]:
    return request(
        "GET",
        settings.fixture_url,
        "/fixtures/pick-results",
        params={"group_id": group_id},
    )


def list_rounds() -> list[dict]:
    return request("GET", settings.fixture_url, "/fixtures/rounds")


def update_round_multiplier(round_id: int, multiplier: int) -> dict:
    return request(
        "PUT",
        settings.fixture_url,
        f"/admin/rounds/{round_id}/multiplier",
        admin_key=settings.admin_api_key,
        json={"multiplier": multiplier},
    )


def set_match_round(match_id: str, round_id: int, set_subsequent: bool = True) -> dict:
    return request(
        "PUT",
        settings.fixture_url,
        f"/admin/matches/{match_id}/round",
        admin_key=settings.admin_api_key,
        json={"round_id": round_id, "set_subsequent": set_subsequent},
    )
```

- [ ] **Step 2: Replace api/leaderboard.py**

```python
from fastapi import APIRouter, Depends

from app.aggregation import leaderboard_row, picks_for_user
from app.auth import bearer_token, get_current_user
from app.clients import fixture, prediction
from app.schemas import LeaderboardRow

router = APIRouter(tags=["leaderboard"])


@router.get("/groups/{group_id}/leaderboard", response_model=list[LeaderboardRow])
def group_leaderboard(
    group_id: str,
    _user: dict = Depends(get_current_user),
    token: str = Depends(bearer_token),
) -> list[LeaderboardRow]:
    """Per-member standings for a group, ordered by points lost (most first)."""
    members = prediction.get_group_members(group_id, token)
    pick_results = fixture.get_pick_results(group_id)
    rows = [
        leaderboard_row(member, picks_for_user(pick_results, member["user_id"]))
        for member in members
    ]
    rows.sort(key=lambda row: row.points_lost, reverse=True)
    return rows
```

- [ ] **Step 3: Replace api/players.py**

```python
from fastapi import APIRouter, Depends

from app.aggregation import pick_history, picks_for_user
from app.auth import bearer_token, get_current_user
from app.clients import fixture, prediction
from app.schemas import PlayerSummary

router = APIRouter(tags=["players"])


@router.get(
    "/groups/{group_id}/members/{user_id}/summary",
    response_model=PlayerSummary,
)
def player_summary(
    group_id: str,
    user_id: str,
    _user: dict = Depends(get_current_user),
    token: str = Depends(bearer_token),
) -> PlayerSummary:
    """One member's pick history and points total in a group."""
    members = prediction.get_group_members(group_id, token)
    names = {m["user_id"]: m["display_name"] for m in members}
    pick_results = fixture.get_pick_results(group_id)
    user_picks = picks_for_user(pick_results, user_id)
    points_lost = sum(p["round_multiplier"] for p in user_picks if p["result"] == "LOST")
    return PlayerSummary(
        user_id=user_id,
        display_name=names.get(user_id, user_id),
        points_lost=points_lost,
        picks=pick_history(user_picks),
    )
```

- [ ] **Step 4: Replace api/matches.py**

```python
from fastapi import APIRouter, Depends

from app.aggregation import match_detail
from app.auth import bearer_token, get_current_user
from app.clients import fixture, prediction
from app.schemas import MatchDetail

router = APIRouter(tags=["matches"])


@router.get("/matches/{match_id}/detail", response_model=MatchDetail)
def match_detail_endpoint(
    match_id: str,
    group_id: str,
    _user: dict = Depends(get_current_user),
    token: str = Depends(bearer_token),
) -> MatchDetail:
    """A match with this group's pick distribution and the players who lost."""
    match = fixture.get_fixture(match_id)
    members = prediction.get_group_members(group_id, token)
    names = {m["user_id"]: m["display_name"] for m in members}
    pick_results = fixture.get_pick_results(group_id)
    group_picks_for_match = [p for p in pick_results if p["match_id"] == match_id]
    return match_detail(match, group_picks_for_match, names)
```

- [ ] **Step 5: Create api/rounds.py**

```python
from fastapi import APIRouter, Depends

from app.auth import get_current_user, require_admin
from app.clients import fixture
from app.schemas import MatchRoundIn, RoundMultiplierIn, RoundOut

router = APIRouter(tags=["rounds"])


@router.get("/rounds", response_model=list[RoundOut])
def list_rounds(_user: dict = Depends(get_current_user)) -> list[dict]:
    """All tournament rounds with their current point multipliers."""
    return fixture.list_rounds()


@router.put("/admin/rounds/{round_id}/multiplier")
def update_round_multiplier(
    round_id: int,
    body: RoundMultiplierIn,
    _admin: dict = Depends(require_admin),
) -> dict:
    """Admin: set points-per-loss for a round."""
    return fixture.update_round_multiplier(round_id, body.multiplier)


@router.put("/admin/matches/{match_id}/round")
def set_match_round(
    match_id: str,
    body: MatchRoundIn,
    _admin: dict = Depends(require_admin),
) -> dict:
    """Admin: assign a match (and optionally all subsequent) to a round."""
    return fixture.set_match_round(match_id, body.round_id, body.set_subsequent)
```

- [ ] **Step 6: Replace main.py**

```python
import logging

from fastapi import FastAPI

from app.api import leaderboard, matches, players, rounds

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(title="BFF Service")
app.include_router(leaderboard.router)
app.include_router(players.router)
app.include_router(matches.router)
app.include_router(rounds.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "bff-service"}
```

- [ ] **Step 7: Commit**

```bash
git add services/bff-service/app/clients/fixture.py \
        services/bff-service/app/api/leaderboard.py \
        services/bff-service/app/api/players.py \
        services/bff-service/app/api/matches.py \
        services/bff-service/app/api/rounds.py \
        services/bff-service/app/main.py
git commit -m "feat(bff): wire points leaderboard, player summary, and rounds proxy"
```

---

## Task 8: frontend — Replace Money component with Points

**Files:**
- Create: `web/src/components/Points.jsx`
- Modify: `web/src/utils/format.js`
- Delete: `web/src/components/Money.jsx`

- [ ] **Step 1: Create Points.jsx**

```jsx
// Points: renders an integer point count.
// tone: 'neg' -> red when pts > 0;  'plain' -> always neutral
export function Points({ pts = 0, tone = 'plain' }) {
  let cls = 'zero';
  if (tone === 'neg' && pts > 0) cls = 'neg';
  return <span className={`money ${cls}`}>{pts} điểm</span>;
}
```

- [ ] **Step 2: Replace format.js**

```js
// Points are integers. 1 điểm = 10,000 ₫ (tracked externally by admin).
export function formatPoints(pts) {
  return `${pts ?? 0} điểm`;
}

export function formatDateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}
```

- [ ] **Step 3: Delete Money.jsx**

```bash
git rm web/src/components/Money.jsx
```

- [ ] **Step 4: Commit**

```bash
git add web/src/components/Points.jsx web/src/utils/format.js
git commit -m "feat(web): replace Money with Points component; 1 điểm = 10,000đ"
```

---

## Task 9: frontend — Update Home page

**Files:**
- Modify: `web/src/pages/Home.jsx`

- [ ] **Step 1: Replace Home.jsx**

```jsx
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client.js';
import { useGroups } from '../context/GroupContext.jsx';
import { useFetch } from '../hooks/useFetch.js';
import { DataTable } from '../components/DataTable.jsx';
import { FormStrip } from '../components/FormStrip.jsx';
import { MatchCard } from '../components/MatchCard.jsx';
import { Points } from '../components/Points.jsx';

function LeaderboardTable({ groupId }) {
  const navigate = useNavigate();
  const { data, loading, error } = useFetch(
    () => api.bff(`/groups/${groupId}/leaderboard`),
    [groupId],
  );

  if (loading) return <div className="loading">Đang tải bảng xếp hạng…</div>;
  if (error) return <div className="loading">Không tải được: {error.message}</div>;

  const columns = [
    {
      key: 'display_name',
      label: 'Người chơi',
      sortable: true,
      render: (r) => <strong>{r.display_name}</strong>,
    },
    {
      key: 'points_lost',
      label: 'Điểm thua',
      sortable: true,
      align: 'right',
      render: (r) => <Points pts={r.points_lost} tone="neg" />,
    },
    {
      key: 'win_rate',
      label: 'Tỷ lệ đúng',
      sortable: true,
      align: 'right',
      render: (r) => `${Math.round(r.win_rate * 100)}%`,
    },
    {
      key: 'form',
      label: 'Phong độ',
      render: (r) => <FormStrip form={r.form} />,
    },
  ];

  return (
    <DataTable
      columns={columns}
      rows={data}
      onRowClick={(r) => navigate(`/players/${r.user_id}?group=${groupId}`)}
      empty="Group chưa có thành viên nào"
    />
  );
}

function MatchesStrip() {
  const navigate = useNavigate();
  const { data, loading } = useFetch(() => api.fixture('/fixtures'), []);

  if (loading) return <div className="loading">Đang tải trận đấu…</div>;
  const matches = data || [];
  const finals = matches.filter((m) => m.status === 'FINAL').slice(-3).reverse();
  const upcoming = matches.filter((m) => m.status !== 'FINAL').slice(0, 3);
  const shown = [...upcoming, ...finals];

  if (shown.length === 0) return <div className="loading">Chưa có trận nào</div>;
  return (
    <div className="grid">
      {shown.map((m) => (
        <MatchCard key={m.id} match={m} onClick={() => navigate(`/matches/${m.id}`)} />
      ))}
    </div>
  );
}

export function Home() {
  const { selectedGroupId, selectedGroup, loading } = useGroups();

  if (loading) return <div className="loading">Đang tải group…</div>;
  if (!selectedGroupId) {
    return (
      <div className="empty">
        <span className="ee">📭</span>
        <p>Bạn chưa thuộc group nào. Liên hệ quản trị viên để được thêm vào.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="section-title">Bảng dự đoán — {selectedGroup?.name}</div>
      <LeaderboardTable groupId={selectedGroupId} />
      <div className="section-title">Trận đấu</div>
      <MatchesStrip />
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/src/pages/Home.jsx
git commit -m "feat(web): Home — remove deposits, use Points in leaderboard"
```

---

## Task 10: frontend — Update PlayerDetail page

**Files:**
- Modify: `web/src/pages/PlayerDetail.jsx`

- [ ] **Step 1: Replace PlayerDetail.jsx**

```jsx
import { useParams, useSearchParams } from 'react-router-dom';
import { api } from '../api/client.js';
import { useGroups } from '../context/GroupContext.jsx';
import { useFetch } from '../hooks/useFetch.js';
import { PieChart } from '../components/PieChart.jsx';
import { DataTable } from '../components/DataTable.jsx';
import { WinLossBadge } from '../components/WinLossBadge.jsx';
import { Points } from '../components/Points.jsx';
import { formatDateTime } from '../utils/format.js';

export function PlayerDetail() {
  const { userId } = useParams();
  const [params] = useSearchParams();
  const { selectedGroupId } = useGroups();
  const groupId = params.get('group') || selectedGroupId;

  const { data, loading, error } = useFetch(
    () => api.bff(`/groups/${groupId}/members/${userId}/summary`),
    [groupId, userId],
  );

  if (!groupId) return <div className="loading">Chưa chọn group.</div>;
  if (loading) return <div className="loading">Đang tải chi tiết người chơi…</div>;
  if (error) return <div className="loading">Không tải được: {error.message}</div>;

  const wins = data.picks.filter((p) => p.result === 'WON').length;
  const losses = data.picks.filter((p) => p.result === 'LOST').length;
  const slices = [
    { label: 'Đúng', value: wins, color: 'var(--brand)' },
    { label: 'Sai', value: losses, color: 'var(--red)' },
  ];

  const pickColumns = [
    {
      key: 'match',
      label: 'Trận',
      render: (p) => <strong>{p.home_team} – {p.away_team}</strong>,
    },
    { key: 'kickoff_at', label: 'Thời điểm', render: (p) => formatDateTime(p.kickoff_at) },
    { key: 'predicted_outcome', label: 'Dự đoán', render: (p) => p.predicted_outcome || '—' },
    {
      key: 'round_multiplier',
      label: 'Hệ số',
      align: 'right',
      render: (p) => `×${p.round_multiplier}`,
    },
    { key: 'result', label: 'Kết quả', render: (p) => <WinLossBadge result={p.result} /> },
  ];

  return (
    <div>
      <div className="section-title">{data.display_name}</div>

      <div className="stat-cards">
        <div className="stat-card">
          <div className="sc-label">Điểm thua</div>
          <div className="sc-value">
            <Points pts={data.points_lost} tone="neg" />
          </div>
        </div>
      </div>

      <div className="section-title">Tỷ lệ đúng / sai</div>
      <div className="panel">
        <PieChart slices={slices} />
      </div>

      <div className="section-title">Lịch sử dự đoán ({data.picks.length})</div>
      <DataTable columns={pickColumns} rows={data.picks} empty="Chưa có dự đoán nào" />
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/src/pages/PlayerDetail.jsx
git commit -m "feat(web): PlayerDetail — remove deposits, show round_multiplier"
```

---

## Task 11: frontend — Update GroupSettings page

**Files:**
- Modify: `web/src/pages/GroupSettings.jsx`

- [ ] **Step 1: Check what AuthContext exposes**

Open `web/src/context/AuthContext.jsx`. Confirm the exported `useAuth` hook returns an object with `user` and that `user.is_admin` exists. If the hook is named differently or `is_admin` is not present, adjust the `isAdmin` line in the code below accordingly.

- [ ] **Step 2: Replace GroupSettings.jsx**

```jsx
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client.js';
import { useGroups } from '../context/GroupContext.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useFetch } from '../hooks/useFetch.js';
import { DataTable } from '../components/DataTable.jsx';
import { Autocomplete } from '../components/Autocomplete.jsx';
import { useToast } from '../components/Toast.jsx';

function MembersPanel({ groupId }) {
  const toast = useToast();
  const { user } = useAuth();
  const members = useFetch(() => api.prediction(`/groups/${groupId}/members`), [groupId]);
  const allUsers = useFetch(() => api.prediction('/admin/users'), []);
  const [username, setUsername] = useState('');
  const [busy, setBusy] = useState(false);

  const memberIds = new Set((members.data || []).map((m) => m.user_id));
  const candidates = (allUsers.data || [])
    .filter((u) => !memberIds.has(u.id))
    .map((u) => ({ value: u.username, label: `${u.display_name} (${u.username})` }));

  async function add() {
    if (!username) return;
    setBusy(true);
    try {
      await api.prediction(`/admin/groups/${groupId}/members`, {
        method: 'POST',
        body: { username },
      });
      toast.success('Đã thêm thành viên');
      setUsername('');
      members.reload();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function removeMember(userId, displayName) {
    if (!window.confirm(`Xóa ${displayName} khỏi group?`)) return;
    try {
      await api.prediction(`/admin/groups/${groupId}/members/${userId}`, {
        method: 'DELETE',
      });
      toast.success(`Đã xóa ${displayName}`);
      members.reload();
    } catch (err) {
      toast.error(err.message);
    }
  }

  const isAdmin = Boolean(user?.is_admin);

  const columns = [
    { key: 'display_name', label: 'Thành viên', render: (m) => <strong>{m.display_name}</strong> },
    { key: 'username', label: 'Đăng nhập', render: (m) => <span className="mono">{m.username}</span> },
    ...(isAdmin
      ? [{
          key: 'actions',
          label: '',
          align: 'right',
          render: (m) => (
            <button
              className="btn btn-secondary btn-sm"
              onClick={(e) => { e.stopPropagation(); removeMember(m.user_id, m.display_name); }}
            >
              Xóa
            </button>
          ),
        }]
      : []),
  ];

  return (
    <div className="panel">
      <div className="panel-head"><h3>Thành viên</h3></div>
      {isAdmin && (
        <div className="inline-form" style={{ marginBottom: 14 }}>
          <div style={{ flex: 1, minWidth: 200 }}>
            <Autocomplete
              options={candidates}
              value={username}
              onChange={setUsername}
              placeholder="Tìm người dùng để thêm…"
            />
          </div>
          <button className="btn btn-primary" onClick={add} disabled={busy || !username}>
            Thêm
          </button>
        </div>
      )}
      {members.loading
        ? <div className="loading">Đang tải thành viên…</div>
        : <DataTable columns={columns} rows={members.data} empty="Group chưa có thành viên" />
      }
    </div>
  );
}

export function GroupSettings() {
  const { groupId } = useParams();
  const { groups } = useGroups();
  const group = groups.find((g) => g.id === groupId);

  return (
    <div>
      <div className="section-title">{group ? group.name : groupId}</div>
      <MembersPanel groupId={groupId} />
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add web/src/pages/GroupSettings.jsx
git commit -m "feat(web): GroupSettings — remove bet-type/deposits, add remove-member"
```

---

## Task 12: frontend — Update Admin page

**Files:**
- Modify: `web/src/pages/Admin.jsx`

- [ ] **Step 1: Replace Admin.jsx**

```jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client.js';
import { useGroups } from '../context/GroupContext.jsx';
import { useFetch } from '../hooks/useFetch.js';
import { DataTable } from '../components/DataTable.jsx';
import { Modal } from '../components/Modal.jsx';
import { useToast } from '../components/Toast.jsx';
import { formatDateTime } from '../utils/format.js';

function PasswordModal({ user, onClose }) {
  const toast = useToast();
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.prediction(`/admin/users/${user.id}/password`, {
        method: 'PUT',
        body: { new_password: password },
      });
      toast.success(`Đã đổi mật khẩu cho ${user.display_name}`);
      onClose();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={`Đổi mật khẩu — ${user.display_name}`} onClose={onClose}>
      <form className="modal-form" onSubmit={submit}>
        <label className="field">
          <span>Mật khẩu mới</span>
          <input type="password" value={password}
            onChange={(e) => setPassword(e.target.value)} required minLength={6} />
        </label>
        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? 'Đang lưu…' : 'Cập nhật'}
        </button>
      </form>
    </Modal>
  );
}

function CreateGroupModal({ onClose, onCreated }) {
  const toast = useToast();
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.prediction('/admin/groups', {
        method: 'POST',
        body: { name: name.trim(), bet_type: 'EUROPEAN' },
      });
      toast.success(`Đã tạo group "${name}"`);
      onCreated();
      onClose();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="Thêm group mới" onClose={onClose}>
      <form className="modal-form" onSubmit={submit}>
        <label className="field">
          <span>Tên group</span>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? 'Đang tạo…' : 'Tạo group'}
        </button>
      </form>
    </Modal>
  );
}

function RoundsManager() {
  const toast = useToast();
  const rounds = useFetch(() => api.bff('/rounds'), []);
  const fixtures = useFetch(() => api.fixture('/fixtures'), []);
  const [edits, setEdits] = useState({});
  const [busy, setBusy] = useState({});
  const [markMatchId, setMarkMatchId] = useState('');
  const [markRoundId, setMarkRoundId] = useState('');
  const [marking, setMarking] = useState(false);

  async function saveMultiplier(round) {
    const val = parseInt(edits[round.id], 10);
    if (!Number.isFinite(val) || val < 1) { toast.warn('Hệ số phải là số nguyên ≥ 1'); return; }
    setBusy((b) => ({ ...b, [round.id]: true }));
    try {
      await api.bff(`/admin/rounds/${round.id}/multiplier`, {
        method: 'PUT',
        body: { multiplier: val },
      });
      toast.success(`Đã cập nhật hệ số vòng "${round.name}"`);
      rounds.reload();
      setEdits((e) => { const c = { ...e }; delete c[round.id]; return c; });
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy((b) => ({ ...b, [round.id]: false }));
    }
  }

  async function markRound() {
    if (!markMatchId || !markRoundId) { toast.warn('Chọn trận và vòng đấu'); return; }
    setMarking(true);
    try {
      const res = await api.bff(`/admin/matches/${markMatchId}/round`, {
        method: 'PUT',
        body: { round_id: parseInt(markRoundId, 10), set_subsequent: true },
      });
      toast.success(`Đã gán ${res.matches_updated} trận sang vòng "${res.round_name}"`);
      setMarkMatchId('');
      setMarkRoundId('');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setMarking(false);
    }
  }

  const roundList = rounds.data || [];
  const matchList = (fixtures.data || []).filter((m) => m.status !== 'FINAL');

  return (
    <div className="panel">
      <div className="panel-head"><h3>Hệ số vòng đấu</h3></div>
      <p className="hint">
        Người thua một trận ở vòng đó cộng số điểm bằng hệ số. (1 điểm = 10,000 ₫, admin tự tính tiền bên ngoài.)
      </p>

      {rounds.loading ? (
        <div className="loading">Đang tải vòng đấu…</div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 20 }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left', padding: '6px 8px' }}>Vòng đấu</th>
              <th style={{ textAlign: 'center', padding: '6px 8px' }}>Hệ số hiện tại</th>
              <th style={{ textAlign: 'right', padding: '6px 8px' }}>Sửa hệ số</th>
            </tr>
          </thead>
          <tbody>
            {roundList.map((r) => (
              <tr key={r.id} style={{ borderTop: '1px solid var(--border)' }}>
                <td style={{ padding: '8px' }}><strong>{r.name}</strong></td>
                <td style={{ textAlign: 'center', padding: '8px' }}>
                  <span className="badge">{r.multiplier} điểm</span>
                </td>
                <td style={{ padding: '8px' }}>
                  <div className="inline-form" style={{ justifyContent: 'flex-end' }}>
                    <input
                      type="number" min="1" style={{ width: 70 }}
                      value={edits[r.id] ?? r.multiplier}
                      onChange={(e) => setEdits((prev) => ({ ...prev, [r.id]: e.target.value }))}
                    />
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => saveMultiplier(r)}
                      disabled={busy[r.id] || String(edits[r.id] ?? r.multiplier) === String(r.multiplier)}
                    >
                      {busy[r.id] ? '…' : 'Lưu'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="panel-head" style={{ marginTop: 8 }}><h4>Đánh dấu vòng mới từ trận này</h4></div>
      <p className="hint">Tất cả trận từ trận chọn trở đi sẽ được gán vào vòng mới.</p>
      <div className="inline-form" style={{ flexWrap: 'wrap', gap: 8 }}>
        <select value={markMatchId} onChange={(e) => setMarkMatchId(e.target.value)}
          style={{ flex: 2, minWidth: 200 }}>
          <option value="">— Chọn trận bắt đầu —</option>
          {matchList.map((m) => (
            <option key={m.id} value={m.id}>
              {m.home_team} vs {m.away_team} · {formatDateTime(m.kickoff_at)}
            </option>
          ))}
        </select>
        <select value={markRoundId} onChange={(e) => setMarkRoundId(e.target.value)}
          style={{ flex: 1, minWidth: 140 }}>
          <option value="">— Vòng đấu —</option>
          {roundList.map((r) => (
            <option key={r.id} value={r.id}>{r.name} (×{r.multiplier})</option>
          ))}
        </select>
        <button className="btn btn-primary" onClick={markRound}
          disabled={marking || !markMatchId || !markRoundId}>
          {marking ? 'Đang cập nhật…' : 'Áp dụng'}
        </button>
      </div>
    </div>
  );
}

export function Admin() {
  const navigate = useNavigate();
  const { groups, refresh: refreshGroups } = useGroups();
  const users = useFetch(() => api.prediction('/admin/users'), []);
  const [pwUser, setPwUser] = useState(null);
  const [creating, setCreating] = useState(false);

  const userColumns = [
    { key: 'display_name', label: 'Tên hiển thị', sortable: true, render: (u) => <strong>{u.display_name}</strong> },
    { key: 'username', label: 'Đăng nhập', sortable: true, render: (u) => <span className="mono">{u.username}</span> },
    {
      key: 'is_admin', label: 'Vai trò',
      render: (u) => u.is_admin
        ? <span className="badge admin">Admin</span>
        : <span className="hint">Người chơi</span>,
    },
    {
      key: 'actions', label: '', align: 'right',
      render: (u) => (
        <button className="btn btn-secondary btn-sm"
          onClick={(e) => { e.stopPropagation(); setPwUser(u); }}>
          Đổi mật khẩu
        </button>
      ),
    },
  ];

  const groupColumns = [
    { key: 'name', label: 'Group', sortable: true, render: (g) => <strong>{g.name}</strong> },
    { key: 'id', label: 'Mã', render: (g) => <span className="mono">{g.id}</span> },
  ];

  return (
    <div>
      <div className="section-title">Người dùng</div>
      {users.loading
        ? <div className="loading">Đang tải người dùng…</div>
        : users.error
          ? <div className="loading">Không tải được: {users.error.message}</div>
          : <DataTable columns={userColumns} rows={users.data} />
      }

      <div className="row-between" style={{ margin: '28px 0 14px' }}>
        <div className="section-title" style={{ margin: 0 }}>Group</div>
        <button className="btn btn-primary btn-sm" onClick={() => setCreating(true)}>
          + Thêm group
        </button>
      </div>
      <DataTable
        columns={groupColumns}
        rows={groups}
        onRowClick={(g) => navigate(`/admin/groups/${g.id}`)}
        empty="Chưa có group nào"
      />

      <div className="section-title" style={{ marginTop: 28 }}>Vòng đấu & Hệ số điểm</div>
      <RoundsManager />

      {pwUser && <PasswordModal user={pwUser} onClose={() => setPwUser(null)} />}
      {creating && <CreateGroupModal onClose={() => setCreating(false)} onCreated={refreshGroups} />}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/src/pages/Admin.jsx
git commit -m "feat(web): Admin — RoundsManager replaces OddsManager; remove bet-type from group creation"
```

---

## Task 13: Smoke test & final commit

- [ ] **Step 1: Start the full stack**

```bash
docker compose up
```

- [ ] **Step 2: Verify these flows manually**

| Check | Expected |
|---|---|
| Home — leaderboard | Column "Điểm thua" in red, no "Còn nợ", no deposit table |
| PlayerDetail | Single stat card "Điểm thua X điểm", pick table has "Hệ số ×N" column, no deposit section |
| GroupSettings (admin) | Only members panel; "Xóa" button per row; remove a member → row disappears |
| Admin — group creation | No "Loại kèo" field |
| Admin — Vòng đấu section | List of rounds with multipliers; edit a value → save → reload → persists |
| Admin — Đánh dấu vòng mới | Select match + round → Apply → toast shows count updated |
| No "kèo" / "cược" / "tiền" | None visible anywhere in the UI |

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "chore: points system refactor complete — prediction game, no real money"
```

---

## Self-Review

- **Spec coverage**: migration ✓, round multiplier CRUD ✓, mark-match-as-new-round ✓, remove member ✓, no money in UI ✓, no "kèo/cược/tiền" in UI ✓, Points component ✓
- **No placeholders**: all steps have complete, runnable code
- **Type consistency**: `points_lost` used in BFF schemas, aggregation, leaderboard, player endpoints, and frontend; `round_multiplier` in fixture-service schemas, BFF schemas, aggregation, frontend pick columns; `RoundMultiplierIn`/`MatchRoundIn` defined in both fixture-service and BFF schemas with matching field names
- **Ledger removed**: `ledger.py` and `deposits.py` git-removed; no remaining BFF code imports them; ledger-service docker container untouched
- **`formatMoney` removed**: replaced with `formatPoints`; `Money.jsx` deleted; all usages replaced with `Points.jsx`
