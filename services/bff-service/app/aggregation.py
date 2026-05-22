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
