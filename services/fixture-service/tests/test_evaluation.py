from app.domain.evaluation import outcome_from_scores, settle_pick


def test_outcome_home_win():
    assert outcome_from_scores(2, 1) == "HOME"


def test_outcome_away_win():
    assert outcome_from_scores(0, 3) == "AWAY"


def test_outcome_draw():
    assert outcome_from_scores(1, 1) == "DRAW"


def test_pick_matching_outcome_wins():
    assert settle_pick("HOME", "HOME") == "WON"


def test_pick_not_matching_outcome_loses():
    assert settle_pick("AWAY", "HOME") == "LOST"


def test_missing_pick_always_loses():
    assert settle_pick(None, "DRAW") == "LOST"
