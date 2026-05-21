# ADR-0007 — Money as integer minor units

- Status: Accepted
- Date: 2026-05-21

## Context

Floating-point is wrong for money: `0.1 + 0.2 != 0.3`. Using float for money is
a hard fail in fintech.

## Decision

The currency is VND. All amounts are stored and computed as integer `BIGINT`
**minor units**. VND has no circulating sub-unit, so one minor unit equals one
VND; the "integer minor units" pattern is honoured uniformly regardless.

## Reasoning (interview framing)

"Money is never a float. I store integer minor units in BIGINT columns and do
all arithmetic in integers, so there's no rounding drift. VND has no sub-unit,
so a minor unit is just one VND — the modelling stays consistent."

## Consequences

- Exact arithmetic everywhere; no rounding errors.
- Adding a fractional-unit currency later means choosing a minor-unit scale —
  the column type and code already accommodate it.
