# Fixture service

Owns matches, rounds, odds and results for the Prediction League platform.
Python 3.12 / FastAPI. The source of truth for match results.

## Responsibilities

- Owns `rounds`, `matches`, `odds`, the `match_picks` read-model and the `outbox`.
- Seeds the 72 World Cup 2026 group-stage matches from a bundled mock provider
  (a real football API can be dropped in behind the same `FixtureProvider`).
- Refreshes odds on a schedule (every 15 min) or on admin trigger.
- Consumes `PickLocked` events into the `match_picks` read-model.
- On result entry, evaluates each pick win/lose and stages a `MatchSettled`
  event in the **transactional outbox** in the same transaction as the result;
  a background worker publishes it.

## HTTP API

| Method | Path | Notes |
|--------|------|-------|
| GET  | `/fixtures` | all matches |
| GET  | `/fixtures/{id}` | one match |
| GET  | `/fixtures/{id}/odds` | latest odds |
| POST | `/admin/matches/{id}/result` | enter the final result (admin key) |
| POST | `/admin/sync` | re-sync fixtures + odds (admin key) |
| PUT  | `/admin/matches/{id}/kickoff` | move a kickoff time, for demos (admin key) |

Admin endpoints require the `X-Admin-Api-Key` header. Through the gateway the
service is reachable under `/api/fixture/`.

## Running and testing

```
docker compose up -d fixture-service
docker compose --profile test run --rm fixture-tests
```
