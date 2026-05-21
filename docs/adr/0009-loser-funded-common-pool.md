# ADR-0009 — Loser-funded common pool

- Status: Accepted
- Date: 2026-05-21

## Context

The design doc's worked example shows only the losing leg of a settlement
(debit the loser, credit the pool). What a winner receives was left
unspecified.

## Decision

When a match settles, each losing member is debited their stake and the pool
("common fund") account is credited. Winners receive **no posting** — they
"win" by not being charged. The pool balance accumulates over the tournament
and is later spent on a group activity, recorded as an ordinary balanced
journal entry (debit pool, credit an activity-expense account).

## Reasoning (interview framing)

"It's a friendly pool: losers chip into a common fund, and the group later
spends it together. Winners aren't paid out, so there's no pot to split — the
ledger stays a plain double-entry of loser-to-pool, and there's no
integer-division remainder problem."

## Consequences

- The ledger stays simple: one balanced journal entry per losing settlement.
- Matches the design doc's worked example exactly.
- Spending the fund is just another balanced manual journal entry — fully
  audited, no special case.
