# Prediction League

A group prediction pool platform for the 2026 FIFA World Cup, built as a
portfolio project to demonstrate fintech-grade transaction handling: a
double-entry ledger, idempotent settlement, a transactional outbox, and an
event-driven choreography saga across database-per-service microservices.

> Framing: this is a *prediction pool* / points league — the same category as
> Fantasy Premier League or an ESPN bracket challenge. The technical substance
> (stakes, settlement, double-entry ledger) is the point.

## Architecture

Bounded contexts, database-per-service, communicating over a RabbitMQ event bus
(Notification is deferred):

| Service      | Stack              | Owns                                    |
|--------------|--------------------|-----------------------------------------|
| Prediction   | Python / FastAPI   | users, groups, picks, pick-lock state   |
| Fixture      | Python / FastAPI   | matches, rounds, odds, scores, results  |
| Ledger       | Java / Spring Boot | accounts, journal, postings, audit log  |
| Notification | _(deferred)_       | delivery log, Telegram chat mapping     |

See [docs/architecture.md](docs/architecture.md) for the full design,
[docs/event-contracts.md](docs/event-contracts.md) for the event contracts,
[docs/diagrams/settlement-saga.md](docs/diagrams/settlement-saga.md) for the
saga sequence, and [docs/adr/](docs/adr/) for the architecture decision records.

## The settlement saga

No service calls another on the write path — everything flows through events:

```
Player picks  ->  Prediction lock job (T-15min)  -- PickLocked -->  Fixture
Fixture projects the locked picks into a read-model.
Admin enters the score  ->  Fixture evaluates picks and writes a MatchSettled
  event to its transactional outbox  -- MatchSettled -->  Ledger
Ledger posts a balanced double-entry per losing pick, idempotently.
```

Money model: losers are debited their stake and the common pool is credited;
winners receive no posting (ADR-0009). Balances are always computed from
postings, never stored.

## Running

Everything runs in Docker — no local Python or Java required.

```
cp .env.example .env      # optional — the defaults also work without a .env
docker compose up -d
```

| Endpoint | URL |
|----------|-----|
| API gateway | http://localhost:8080 |
| RabbitMQ UI | http://localhost:15672  (guest / guest) |

Gateway routes: `/api/prediction`, `/api/fixture`, `/api/ledger`.

Stop with `docker compose down` (add `-v` to also wipe the data volumes).

## Demo

With the stack up, run the end-to-end saga demo:

```
bash scripts/e2e-demo.sh
```

It registers players, places picks, locks a match, settles the result, and
asserts the Ledger posted the correct double-entry — exercising all three
services and the event bus in one pass.

## Testing

Each service's tests run in a one-off container against isolated test
infrastructure:

```
docker compose --profile test run --rm ledger-tests       # JUnit + Spring
docker compose --profile test run --rm fixture-tests       # pytest
docker compose --profile test run --rm prediction-tests    # pytest
```

## Build status

- [x] Phase 0 — monorepo scaffold & infrastructure
- [x] Phase 1 — Ledger service
- [x] Phase 2 — Fixture service
- [x] Phase 3 — Prediction service
- [x] Phase 4 — end-to-end integration

## Repository layout

```
docs/         architecture, event contracts, ADRs, diagrams
services/     one isolated service per directory (own DB, build, tests)
gateway/      Nginx reverse proxy
scripts/      operational and demo scripts
```
