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
    WON if the pick matched the actual outcome, otherwise LOST.
    A missing pick (None) is always LOST.
    """
    return "WON" if predicted_outcome == actual_outcome else "LOST"
