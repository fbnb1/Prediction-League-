"""Pure aggregation helpers over data already fetched from upstream services.

Kept free of I/O so they can be unit-tested without mocking HTTP.
`pick_results` rows are the objects returned by fixture-service
`GET /fixtures/pick-results` (oldest kickoff first).
"""

from app.schemas import (
    DepositItem,
    LeaderboardRow,
    LoserItem,
    MatchDetail,
    PickHistoryItem,
)

_FORM_LENGTH = 5


def recent_form(user_picks: list[dict]) -> list[str]:
    """Up to 5 most recent settled results as "W"/"L", newest first.

    `user_picks` is expected oldest-kickoff first; settled means WON or LOST.
    """
    settled = [p for p in user_picks if p["result"] in ("WON", "LOST")]
    recent = settled[-_FORM_LENGTH:]
    return ["W" if p["result"] == "WON" else "L" for p in reversed(recent)]


def leaderboard_row(
    member: dict, user_picks: list[dict], deposited_minor: int
) -> LeaderboardRow:
    """One leaderboard entry for a member, given their picks and deposits."""
    wins = sum(1 for p in user_picks if p["result"] == "WON")
    losses = sum(1 for p in user_picks if p["result"] == "LOST")
    money_lost = sum(p["stake_minor"] for p in user_picks if p["result"] == "LOST")
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
        money_lost_minor=money_lost,
        money_deposited_minor=deposited_minor,
        money_owed_minor=money_lost - deposited_minor,
    )


def picks_for_user(pick_results: list[dict], user_id: str) -> list[dict]:
    """The subset of pick_results belonging to one user (order preserved)."""
    return [p for p in pick_results if p["user_id"] == user_id]


def pick_history(user_picks: list[dict]) -> list[PickHistoryItem]:
    """A user's picks as history items, newest kickoff first."""
    return [
        PickHistoryItem(**{k: p[k] for k in PickHistoryItem.model_fields})
        for p in reversed(user_picks)
    ]


def deposit_items(deposits: list[dict], names: dict[str, str]) -> list[DepositItem]:
    """Ledger deposit rows as DepositItems, newest first, with display names."""
    items = [
        DepositItem(
            user_id=d["depositor"],
            display_name=names.get(d["depositor"], d["depositor"]),
            amount_minor=d["amountMinor"],
            posted_at=d.get("postedAt"),
        )
        for d in deposits
    ]
    items.sort(
        key=lambda i: (i.posted_at is not None, i.posted_at), reverse=True
    )
    return items


def match_detail(
    match: dict, group_picks_for_match: list[dict], names: dict[str, str]
) -> MatchDetail:
    """Match info plus this group's pick distribution and the losers."""
    distribution = {"HOME": 0, "DRAW": 0, "AWAY": 0}
    for pick in group_picks_for_match:
        outcome = pick.get("predicted_outcome")
        if outcome in distribution:
            distribution[outcome] += 1
    losers = [
        LoserItem(
            user_id=p["user_id"],
            display_name=names.get(p["user_id"], p["user_id"]),
            stake_minor=p["stake_minor"],
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
        total_collected_minor=sum(loser.stake_minor for loser in losers),
    )
