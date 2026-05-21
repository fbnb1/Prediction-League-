# Notification service — integration hook

The Notification service is **deferred** — it is not built in this project.
This note records exactly where it would attach, so adding it later is a
self-contained phase that touches no other service.

## Role

A stateless event consumer. It would own only its own data — a delivery log
and a Telegram chat-id mapping — and hold `user_id` / `match_id` as opaque
references, consistent with the bounded-context rule.

## Subscriptions

It binds two durable queues to the existing `prediction-league.events` topic
exchange. No producer changes:

| Queue | Routing key | Reacts to |
|-------|-------------|-----------|
| `notification.pick-locked`   | `pick.locked`   | tell players their picks are locked; nudge anyone auto-lossed |
| `notification.match-settled` | `match.settled` | tell each player whether they won or lost, and their new balance |

Each queue gets a dead-letter queue, like every other consumer in the system.

## Why it changes nothing else

`PickLocked` and `MatchSettled` are already published to a **topic exchange**.
Adding a consumer is just a new queue binding — the producers (Prediction,
Fixture) and the Ledger never learn it exists. That decoupling is the payoff of
choreography over orchestration.

## The one gap

A "you haven't picked yet" reminder at T-30min is not covered by the current
two events. It would need either a scheduled job in Notification that reads
Prediction's pick state, or a dedicated `PickWindowOpen` event. Everything else
the Notification service needs is already on the bus.
