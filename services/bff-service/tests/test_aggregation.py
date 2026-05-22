from app.aggregation import leaderboard_row, match_detail, recent_form


def _pick(result, multiplier=2, outcome="HOME", match_id="m1"):
    return {
        "match_id": match_id,
        "user_id": "usr_1",
        "predicted_outcome": outcome,
        "auto_loss": False,
        "round_multiplier": multiplier,
        "bet_type": "EUROPEAN",
        "home_team": "A",
        "away_team": "B",
        "kickoff_at": "2026-06-11T18:00:00Z",
        "status": "FINAL",
        "outcome": "HOME",
        "home_score": 1,
        "away_score": 0,
        "result": result,
    }


def test_recent_form_is_newest_first_and_capped_at_five():
    picks = [_pick("WON"), _pick("LOST"), _pick("PENDING"), _pick("WON")]
    # PENDING is excluded; newest settled pick comes first.
    assert recent_form(picks) == ["W", "L", "W"]

    long_run = [_pick("WON") for _ in range(7)]
    assert len(recent_form(long_run)) == 5


def test_leaderboard_row_totals():
    picks = [_pick("WON", multiplier=2), _pick("LOST", multiplier=4), _pick("PENDING")]
    row = leaderboard_row({"user_id": "usr_1", "display_name": "Alice"}, picks)
    assert row.wins == 1
    assert row.losses == 1
    assert row.total_picks == 3
    assert row.win_rate == 0.5
    assert row.points_lost == 4  # only the LOST pick's multiplier counts


def test_leaderboard_win_rate_zero_when_nothing_settled():
    row = leaderboard_row(
        {"user_id": "usr_1", "display_name": "Alice"}, [_pick("PENDING")]
    )
    assert row.win_rate == 0.0


def test_match_detail_distribution_and_losers():
    picks = [
        _pick("LOST", multiplier=2, outcome="HOME"),
        _pick("WON", multiplier=2, outcome="AWAY"),
        _pick("LOST", multiplier=4, outcome="AWAY"),
    ]
    detail = match_detail(
        {
            "id": "m1",
            "home_team": "A",
            "away_team": "B",
            "kickoff_at": "2026-06-11T18:00:00Z",
            "status": "FINAL",
            "outcome": "HOME",
            "home_score": 1,
            "away_score": 0,
        },
        picks,
        names={"usr_1": "Alice"},
    )
    assert detail.pick_distribution == {"HOME": 1, "DRAW": 0, "AWAY": 2}
    assert len(detail.losers) == 2
    assert detail.total_points == 6  # 2 + 4
