# Ledger service

The double-entry ledger for the Prediction League platform. Java 21 /
Spring Boot. The only service that touches money.

## Responsibilities

- Owns `accounts`, `journal_entries`, `postings`, `audit_log`.
- Consumes `MatchSettled` events and posts balanced double-entry transactions
  idempotently (debit the losing player, credit the common pool).
- Exposes a read API for balances, postings, journal entries and the audit log,
  plus an admin API for manual balanced entries.

## Key rules

- **Money is integer minor units** (`BIGINT`), never a float.
- **Balances are computed**, never stored: an account's balance is
  `sum(CREDIT amounts) - sum(DEBIT amounts)` over its postings.
- **Every journal entry balances**: total debits = total credits. `PostingService`
  refuses to persist an unbalanced entry.
- **Settlement is idempotent**: the per-user key `{event_id}:{user_id}` is a
  `UNIQUE` constraint on `journal_entries`; a redelivered event is skipped.

## HTTP API

| Method | Path | Notes |
|--------|------|-------|
| GET  | `/accounts` | all accounts with balances |
| GET  | `/accounts/{ownerType}/{ownerId}` | one account with balance |
| GET  | `/accounts/{ownerType}/{ownerId}/postings` | an account's postings |
| GET  | `/journal-entries` | recent journal entries |
| GET  | `/journal-entries/{id}` | one entry with its postings |
| GET  | `/audit-log` | recent audit log entries |
| POST | `/admin/journal-entries` | post a manual balanced entry (admin key) |
| POST | `/admin/journal-entries/{id}/reverse` | reverse an entry (admin key) |

Admin endpoints require the `X-Admin-Api-Key` header. Through the gateway the
service is reachable under `/api/ledger/`.

## Running and testing

The service runs in Docker via the root `docker-compose.yml`:

```
docker compose up -d ledger-service
```

Tests (unit + integration) run in a one-off container against isolated
Postgres + RabbitMQ instances:

```
docker compose --profile test run --rm ledger-tests
```
