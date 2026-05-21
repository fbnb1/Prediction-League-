# Settlement saga — sequence

The full choreography, from a player's pick to the money posting. No service
calls another on the write path; everything flows through the RabbitMQ event
bus. Both events travel on the `prediction-league.events` topic exchange.

```
 Player     Prediction          RabbitMQ           Fixture            Ledger
   |             |                  |                 |                 |
   | submit pick |                  |                 |                 |
   |------------>|                  |                 |                 |
   |             |                  |                 |                 |
   |        lock job fires          |                 |                 |
   |        (T-15min): lock picks,  |                 |                 |
   |        auto-loss non-pickers   |                 |                 |
   |             |   PickLocked     |                 |                 |
   |             |----------------->|                 |                 |
   |             |                  |   PickLocked    |                 |
   |             |                  |---------------->|                 |
   |             |                  |          project picks into       |
   |             |                  |          the match_picks model    |
   |             |                  |                 |                 |
 Admin enters the final score                         |                 |
   |---------------------------------------------------|                 |
   |             |                  |        evaluate picks win/lose;    |
   |             |                  |        write result + MatchSettled |
   |             |                  |        to the OUTBOX in one txn    |
   |             |                  |                 |                 |
   |             |                  |   outbox worker publishes          |
   |             |                  |<----------------|                 |
   |             |                  |          MatchSettled              |
   |             |                  |----------------------------------->|
   |             |                  |                 |       check idempotency key
   |             |                  |                 |       - seen -> skip + ack
   |             |                  |                 |       - new  -> post a
   |             |                  |                 |         balanced double
   |             |                  |                 |         entry + audit log
   |             |                  |                 |                 |
   |             |                  |        balance = sum(postings)     |
```

## Failure handling

- **Forward-only saga.** Once Fixture commits a result, settlement must
  eventually succeed. Reliability comes from consumer retry + dead-letter
  queues + idempotency — not from compensation (ADR-0004, ADR-0006).
- **Transactional outbox.** The result and the `MatchSettled` event are written
  in one database transaction, so the event is never lost and never published
  for a write that rolled back (ADR-0005). A separate worker publishes it.
- **Idempotent settlement.** The Ledger derives a per-user idempotency key
  (`{event_id}:{user_id}`) backed by a `UNIQUE` constraint on `journal_entries`.
  A redelivered event is skipped and acknowledged — never double-charged
  (ADR-0004).
