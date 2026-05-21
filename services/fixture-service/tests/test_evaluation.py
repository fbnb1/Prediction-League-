from app.domain.evaluation import outcome_from_scores, settle_pick, settle_pick_asian


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


# --- Asian handicap -------------------------------------------------------

def test_asian_favourite_covers_when_winning_margin_beats_the_line():
    # Home -1.5: home wins 3-1, adjusted 1.5-1 -> home covers.
    assert settle_pick_asian("HOME", 3, 1, 1.5) == "WON"
    assert settle_pick_asian("AWAY", 3, 1, 1.5) == "LOST"


def test_asian_favourite_fails_to_cover_a_narrow_win():
    # Home -1.5: home wins only 2-1, adjusted 0.5-1 -> away covers.
    assert settle_pick_asian("HOME", 2, 1, 1.5) == "LOST"
    assert settle_pick_asian("AWAY", 2, 1, 1.5) == "WON"


def test_asian_underdog_receiving_the_line_covers():
    # Home +2.5 (handicap -2.5): home loses 0-2, adjusted 2.5-2 -> home covers.
    assert settle_pick_asian("HOME", 0, 2, -2.5) == "WON"
    assert settle_pick_asian("AWAY", 0, 2, -2.5) == "LOST"


def test_asian_missing_or_draw_pick_loses():
    assert settle_pick_asian(None, 1, 1, 0.5) == "LOST"
    assert settle_pick_asian("DRAW", 1, 1, 0.5) == "LOST"
