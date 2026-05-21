# Event Contracts

The contract between services. **Frozen** — a breaking change requires an
`event_version` bump and an ADR. Sample payloads live in `sample-events/` and
double as manual demo inputs for the RabbitMQ management UI.

## Transport — RabbitMQ topology

| Object               | Name                         | Notes                                      |
|----------------------|------------------------------|--------------------------------------------|
| Exchange             | `prediction-league.events`   | type `topic`, durable                      |
| Routing key          | `pick.locked`                | carries `PickLocked`                       |
| Routing key          | `match.settled`              | carries `MatchSettled`                     |
| Queue                | `fixture.pick-locked`        | bound to `pick.locked`; consumed by Fixture|
| Queue                | `ledger.match-settled`       | bound to `match.settled`; consumed by Ledger|
| Dead-letter exchange | `prediction-league.dlx`      | type `fanout`, durable                     |
| DLQ                  | `fixture.pick-locked.dlq`    | dead letters from `fixture.pick-locked`    |
| DLQ                  | `ledger.match-settled.dlq`   | dead letters from `ledger.match-settled`   |

Each consumer declares-and-binds its own queue idempotently on startup. Work
queues are `durable`, messages are published `persistent`, and queues set
`x-dead-letter-exchange` to `prediction-league.dlx`. A message that fails
processing repeatedly is routed to its DLQ rather than being lost or requeued
forever.

## Envelope

Every event shares a common envelope:

| Field           | Type                  | Notes                                  |
|-----------------|-----------------------|----------------------------------------|
| `event`         | string                | event name (`PickLocked`, `MatchSettled`) |
| `event_id`      | string (UUID)         | unique per event; the idempotency key  |
| `event_version` | integer               | contract version, currently `1`        |
| `occurred_at`   | string (ISO-8601 UTC) | when the event occurred                |
| `currency`      | string                | ISO currency code; `VND` for this build |

## PickLocked

Published by **Prediction**, once per match, when the lock job fires (T-15min
before kickoff). Consumed by **Fixture** into its `match_picks` read-model.
Routing key `pick.locked`.

```json
{
  "event": "PickLocked",
  "event_id": "9f1c2e7a-3b8d-4c21-9a5e-2d6f0b1c4e88",
  "event_version": 1,
  "occurred_at": "2026-06-11T18:45:00Z",
  "match_id": "WC2026-GS-A1",
  "group_id": "grp_01HXYZ",
  "kickoff_at": "2026-06-11T19:00:00Z",
  "currency": "VND",
  "picks": [
    { "user_id": "usr_01HAAA", "predicted_outcome": "HOME", "stake_minor": 10000, "auto_loss": false },
    { "user_id": "usr_01HBBB", "predicted_outcome": null,   "stake_minor": 10000, "auto_loss": true  }
  ]
}
```

| Field                       | Type                       | Notes                                          |
|------------------------------|----------------------------|------------------------------------------------|
| `match_id`                   | string                     | reference to a Fixture match                   |
| `group_id`                   | string                     | the predicting group                           |
| `kickoff_at`                 | string (ISO-8601 UTC)      | match kickoff time                             |
| `picks[].user_id`            | string                     | opaque reference to a Prediction user          |
| `picks[].predicted_outcome`  | `HOME` \| `DRAW` \| `AWAY` \| `null` | `null` means no pick was made        |
| `picks[].stake_minor`        | integer                    | stake in minor units, in effect at lock time   |
| `picks[].auto_loss`          | boolean                    | `true` iff `predicted_outcome` is `null`       |

## MatchSettled

Published by **Fixture** via the transactional outbox, once per match, when an
admin enters the result. Consumed by **Ledger**. Routing key `match.settled`.

```json
{
  "event": "MatchSettled",
  "event_id": "c4d5e6f7-1234-4abc-9def-567890abcdef",
  "event_version": 1,
  "occurred_at": "2026-06-11T21:05:00Z",
  "match_id": "WC2026-GS-A1",
  "currency": "VND",
  "result": { "home_score": 2, "away_score": 1, "outcome": "HOME" },
  "settlements": [
    { "user_id": "usr_01HAAA", "predicted_outcome": "HOME", "result": "WON",  "stake_minor": 10000 },
    { "user_id": "usr_01HBBB", "predicted_outcome": null,   "result": "LOST", "stake_minor": 10000 }
  ]
}
```

| Field                            | Type                          | Notes                                  |
|-----------------------------------|-------------------------------|----------------------------------------|
| `match_id`                        | string                        | reference to a Fixture match           |
| `result.home_score`               | integer                       | final home score                       |
| `result.away_score`               | integer                       | final away score                       |
| `result.outcome`                  | `HOME` \| `DRAW` \| `AWAY`     | derived match outcome                  |
| `settlements[].user_id`           | string                        | opaque reference to a Prediction user  |
| `settlements[].predicted_outcome` | `HOME` \| `DRAW` \| `AWAY` \| `null` | the member's locked pick        |
| `settlements[].result`            | `WON` \| `LOST`               | evaluation against `result.outcome`    |
| `settlements[].stake_minor`       | integer                       | stake in minor units                   |

The Ledger posts a journal entry **only for `LOST`** settlements (debit the
loser, credit the pool). `WON` settlements produce no posting — see
[ADR-0009](adr/0009-loser-funded-common-pool.md).

## Idempotency

- **PickLocked** — Fixture upserts its `match_picks` projection keyed on
  `event_id` (stored as `source_event_id`, UNIQUE). Redelivery is a no-op.
- **MatchSettled** — Ledger derives a per-user idempotency key
  `{event_id}:{user_id}` and writes it to `journal_entries.idempotency_key`
  (UNIQUE). A redelivered event collides on every key and is skipped + acked,
  so it can never double-charge.

## Versioning

The contract is frozen at `event_version: 1`. A breaking change bumps the
version; consumers handle the versions they know explicitly. See
[ADR-0008](adr/0008-event-carried-state-transfer.md).
