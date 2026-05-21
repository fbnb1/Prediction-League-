# ADR-0001 — Microservices over a monolith

- Status: Accepted
- Date: 2026-05-21

## Context

This is a prediction pool for a small private group. At this scale a monolith
is genuinely the correct technical choice.

## Decision

Split the platform into bounded-context services (Prediction, Fixture, Ledger;
Notification deferred), each with its own database.

## Reasoning (interview framing)

"For a private group a monolith is the right call technically. I deliberately
chose microservices to demonstrate database-per-service, event-driven
communication, and isolation of the money context from the business context.
In a real product I'd flag that the operational overhead isn't justified at
this scale." Knowing *when not* to use microservices is the point.

## Consequences

- Demonstrates service isolation, event-driven design, and a clean money
  boundary.
- Real cost: more moving parts, more operational overhead — accepted as a
  deliberate portfolio trade-off.
