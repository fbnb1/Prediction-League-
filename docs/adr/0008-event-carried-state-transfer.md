# ADR-0008 — Event-carried state transfer for picks; REST for fixture reads

- Status: Accepted
- Date: 2026-05-21

## Context

The Fixture service must evaluate picks as win/lose, but picks are owned by the
Prediction service, and each context may hold only reference IDs of other
contexts. A synchronous call from Fixture to Prediction on the settlement
write-path would couple money settlement to Prediction's uptime.

## Decision

When Prediction's lock job fires it publishes `PickLocked` carrying every group
member's pick for that match. Fixture consumes it into a `match_picks`
read-model — a CQRS projection of data it was *handed*, not data it owns or
exposes for editing. At settlement, Fixture evaluates that local read-model.

Schedule and odds reads (Prediction reading from Fixture) are a **read-path**
concern, not the money write-path, so they use synchronous REST. The event bus
stays at two events.

## Reasoning (interview framing)

"Fixture needs the picks but doesn't own them. Rather than a synchronous call on
the money path, Prediction publishes the picks as an event and Fixture keeps a
read-model. The settlement write-path then touches only Fixture's own database.
Reads of the schedule are a different matter — those can be a normal REST call."

## Consequences

- The settlement write-path has no synchronous cross-service dependency.
- Fixture holds a projection keyed on `event_id` for idempotent updates.
- Two clear patterns: events for the write-path, REST for the read-path.
