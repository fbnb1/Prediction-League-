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
[docs/event-contracts.md](docs/event-contracts.md) for the event contracts, and
[docs/adr/](docs/adr/) for the architecture decision records.

## Running

Everything runs in Docker — no local Python or Java required.

```
cp .env.example .env      # optional — the defaults also work without a .env
docker compose up -d
```

- Gateway:     http://localhost:8080
- RabbitMQ UI: http://localhost:15672  (guest / guest)

Stop with `docker compose down` (add `-v` to also wipe the data volumes).

## Build status

- [x] Phase 0 — monorepo scaffold & infrastructure
- [x] Phase 1 — Ledger service
- [x] Phase 2 — Fixture service
- [ ] Phase 3 — Prediction service
- [ ] Phase 4 — end-to-end integration

## Repository layout

```
docs/         architecture, event contracts, ADRs, diagrams
services/     one isolated service per directory (own DB, build, tests)
gateway/      Nginx reverse proxy
scripts/      operational and demo scripts
```
