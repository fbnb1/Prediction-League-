import httpx
import respx
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


@respx.mock
def test_leaderboard_aggregates_picks_and_deposits(user_token):
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
                _pick("usr_1", "LOST", 30000),
                _pick("usr_1", "WON", 10000),
                _pick("usr_2", "WON", 10000),
            ],
        )
    )
    respx.get(f"{settings.ledger_url}/accounts/player").mock(
        side_effect=lambda request: httpx.Response(
            200,
            json={
                "ownerId": f"{request.url.params['userId']}:{group_id}",
                "debitMinor": 0,
                "creditMinor": 20000,
                "balanceMinor": 20000,
            },
        )
    )

    response = client.get(
        f"/groups/{group_id}/leaderboard",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    rows = response.json()
    # Ordered by money lost, descending: usr_1 (30000) before usr_2 (0).
    assert [r["user_id"] for r in rows] == ["usr_1", "usr_2"]
    assert rows[0]["money_lost_minor"] == 30000
    assert rows[0]["money_owed_minor"] == 10000  # 30000 lost - 20000 deposited
    assert rows[0]["form"] == ["W", "L"]


def test_leaderboard_requires_auth():
    response = client.get("/groups/grp_1/leaderboard")
    assert response.status_code == 401


def _pick(user_id, result, stake):
    return {
        "match_id": "m1",
        "user_id": user_id,
        "predicted_outcome": "HOME",
        "auto_loss": False,
        "stake_minor": stake,
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
