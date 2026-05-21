# Prediction service

Owns users, groups, picks and the pick-lock lifecycle. Python 3.12 / FastAPI.

## Responsibilities

- Owns `users`, `groups`, `group_members`, `picks` and a `match_ref` cache.
- Registration and login with JWT auth (bcrypt password hashing).
- Pick submission, enforcing the lock window: a pick is rejected once it is
  within T-15min of kickoff.
- Syncs fixture schedules from the Fixture service over REST (read-path).
- A lock job locks every pick for a match at its lock time, marks non-pickers
  as automatic losses, and publishes one `PickLocked` event per group.

## HTTP API

| Method | Path | Notes |
|--------|------|-------|
| POST | `/auth/register` | register, returns a JWT |
| POST | `/auth/login` | login, returns a JWT |
| POST | `/groups` | create a group (auth) |
| POST | `/groups/{id}/join` | join a group (auth) |
| GET  | `/groups/mine` | groups the caller belongs to (auth) |
| POST | `/picks` | submit/update a pick (auth) |
| GET  | `/picks/mine` | the caller's picks (auth) |
| GET  | `/fixtures` | the local fixture cache |
| POST | `/admin/matches/{id}/force-lock` | lock a match now, for demos (admin key) |

Authenticated routes require a `Bearer` token. Through the gateway the service
is reachable under `/api/prediction/`.

## Running and testing

```
docker compose up -d prediction-service
docker compose --profile test run --rm prediction-tests
```

The `LOCK_OFFSET_MINUTES` setting (default 15) is configurable, and the lock
logic accepts an injected clock, so the timing-sensitive behaviour is testable
and the `force-lock` endpoint makes it demoable.
