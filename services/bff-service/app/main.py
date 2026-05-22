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
