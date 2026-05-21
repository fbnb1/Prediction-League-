"""Pure functions for evaluating a match result and settling picks."""


def outcome_from_scores(home_score: int, away_score: int) -> str:
    """Derive the match outcome (HOME / DRAW / AWAY) from the final score."""
    if home_score > away_score:
        return "HOME"
    if home_score < away_score:
        return "AWAY"
    return "DRAW"


def settle_pick(predicted_outcome: str | None, actual_outcome: str) -> str:
    """
    European (1X2) settlement: WON if the pick matched the actual outcome,
    otherwise LOST. A missing pick (None) is always LOST.
    """
    return "WON" if predicted_outcome == actual_outcome else "LOST"


def settle_pick_asian(
    predicted_outcome: str | None,
    home_score: int,
    away_score: int,
    handicap: float,
) -> str:
    """
    Asian-handicap settlement. `handicap` is applied to the home team's score
    (positive = home gives the line, e.g. Italy -3.5 against France).

    The home side covers when its handicap-adjusted score still beats the away
    score; the away side covers otherwise. Half-point lines mean a push is
    impossible. A missing or draw pick is always LOST.
    """
    if predicted_outcome not in ("HOME", "AWAY"):
        return "LOST"
    home_covers = (home_score - handicap) > away_score
    backed_home = predicted_outcome == "HOME"
    return "WON" if backed_home == home_covers else "LOST"
