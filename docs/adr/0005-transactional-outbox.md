# ADR-0005 — Transactional outbox

- Status: Accepted
- Date: 2026-05-21

## Context

Writing to the database and publishing an event are two separate systems and
cannot be a single atomic operation. A naive "save then publish" loses events
on a crash between the two, or publishes events for writes that later roll back.

## Decision

The Fixture service writes the `MatchSettled` event into an `outbox` table in
the *same database transaction* as the match result. A separate worker polls
the outbox and publishes to RabbitMQ, marking rows as published afterward.

## Reasoning (interview framing)

"Save and publish can't be atomic across two systems. The outbox writes the
event in the same transaction as the data; a worker publishes it afterward — so
I never lose an event or publish one for a write that rolled back."

## Consequences

- Atomic "save result + record intent to publish".
- Delivery is at-least-once — consumers must be idempotent (see ADR-0004).
