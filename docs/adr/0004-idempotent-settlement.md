# ADR-0004 — Idempotent settlement

- Status: Accepted
- Date: 2026-05-21

## Context

Events are redelivered — network retries, consumer restarts, at-least-once
delivery. Without idempotency the ledger would double-charge.

## Decision

Each `MatchSettled` settlement is processed with a per-user idempotency key
`{event_id}:{user_id}`. The Ledger consumer checks it, and it is also a
`UNIQUE` constraint on `journal_entries.idempotency_key`. A redelivered event
collides on every key; the consumer skips it and acknowledges.

## Reasoning (interview framing)

"Events get redelivered. I use an idempotency key checked in the consumer,
backed by a UNIQUE constraint on the journal table as a final guard at the
database layer — so even a race can't double-post."

## Consequences

- Redelivery is safe and silent.
- The database is the last line of defence, independent of consumer logic.
