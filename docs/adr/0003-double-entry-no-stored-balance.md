# ADR-0003 — Double-entry ledger, no stored balance

- Status: Accepted
- Date: 2026-05-21

## Context

A single mutable balance column can drift, hides history, and cannot be
audited.

## Decision

Every money movement is a balanced journal entry of two or more postings
(total debits = total credits). An account's balance is the `SUM` of its
postings, computed on read. There is no stored balance column.

## Reasoning (interview framing)

"A mutable balance column can drift and can't be audited. Double-entry makes
every change a balanced pair, makes balance a derived fact, and gives a
complete audit trail — the same model real ledgers use."

## Consequences

- Full, append-only audit trail; balance is always provable from truth.
- Balance is a `SUM` query. If it becomes hot, add a snapshot/cache table later
  — postings remain the source of truth.
