# ADR-0002 — Java for the ledger, Python for the rest

- Status: Accepted
- Date: 2026-05-21

## Context

The ledger handles money and needs strong ACID guarantees, transaction
integrity, and type safety. The Prediction and Fixture services are I/O-bound —
external calls, scheduled jobs, async work.

## Decision

Implement the Ledger service in Java / Spring Boot; implement Prediction and
Fixture in Python / FastAPI.

## Reasoning (interview framing)

"The ledger needs transaction integrity and type safety, so I put it on the
JVM, where most core banking runs. The other services are I/O-bound, which fits
Python's async model. The split follows the consistency requirement, not
personal preference."

## Consequences

- The money path runs on a statically typed, ACID-friendly stack.
- The team needs both toolchains — mitigated here by Docker-first builds.
