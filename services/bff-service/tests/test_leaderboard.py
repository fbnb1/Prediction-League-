import httpx
import respx
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


@respx.mock
def test_leaderboard_aggregates_picks_and_points(user_token):
    group_id = "grp_1"
    respx.get(f"{settings.prediction_url}/groups/{group_id}/members").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"user_id": "usr_1", "username": "alice", "display_name": "Alice"},
                {"user_id": "usr_2", "username": "bob", "display_name": "Bob"},
            ],
        )
    )
    respx.get(f"{settings.fixture_url}/fixtures/pick-results").mock(
        return_value=httpx.Response(
            200,
            json=[
                _pick("usr_1", "LOST", multiplier=4),
                _pick("usr_1", "WON", multiplier=2),
                _pick("usr_2", "WON", multiplier=2),
            ],
        )
    )

    response = client.get(
        f"/groups/{group_id}/leaderboard",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    rows = response.json()
    # Ordered by points_lost descending: usr_1 (4 pts) before usr_2 (0 pts).
    assert [r["user_id"] for r in rows] == ["usr_1", "usr_2"]
    assert rows[0]["points_lost"] == 4
    assert rows[0]["form"] == ["W", "L"]


def test_leaderboard_requires_auth():
    response = client.get("/groups/grp_1/leaderboard")
    assert response.status_code == 401


def _pick(user_id, result, multiplier=2):
    return {
        "match_id": "m1",
        "user_id": user_id,
        "predicted_outcome": "HOME",
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
