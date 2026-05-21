# ADR-0006 — Choreography saga & eventual consistency

- Status: Accepted
- Date: 2026-05-21

## Context

Evaluating a result and moving money span two services. A synchronous
distributed transaction across them would be brittle and tightly coupled.

## Decision

Use a choreography-based saga: Fixture publishes `MatchSettled`, the Ledger
reacts. The Ledger never calls another service — it only listens. The saga is
**forward-only**: there is no business compensation. Reliability comes from
consumer retry, a dead-letter queue, and idempotency.

## Reasoning (interview framing)

"Result evaluation and money movement don't need one cross-service
transaction. Fixture publishes, Ledger reacts — eventually consistent, no
distributed transaction. There's no business 'undo', so the failure strategy is
retry + DLQ + idempotency, not compensation."

## Consequences

- Services are decoupled and independently deployable.
- A correction to a settled entry is itself a new balanced journal entry — the
  ledger is never mutated in place.
