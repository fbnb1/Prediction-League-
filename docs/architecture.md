# Prediction League — Architecture & Design Document

> A group prediction pool platform featuring a double-entry ledger, idempotent
> settlement engine, and event-driven fixture synchronization.
>
> Built for the 2026 FIFA World Cup as a portfolio project demonstrating
> fintech-grade transaction handling, microservice boundaries, and
> event-driven design.

---

## 1. What this is (and what it isn't)

A platform where members of a private group make predictions on football
matches. Each match has a configurable stake. Members must lock in a prediction
before kickoff (no pick = automatic loss). After the match, the system settles
results and adjusts each member's balance through a double-entry ledger, with a
full audit trail of every transaction.

**Framing note for interviews / CV:** this is described as a *prediction pool*
or *points league* — the same category as Fantasy Premier League or an ESPN
bracket challenge. The technical substance (stakes, settlement, ledger) is what
matters and maps directly to fintech systems.

---

## 2. Core technical themes (the "why this project" pitch)

| Theme | Where it shows up | Why fintech cares |
|---|---|---|
| Double-entry ledger | Ledger service | Money correctness, no lost/created funds |
| Idempotency | Settlement consumer | Retries must not double-charge |
| Transactional outbox | Fixture -> event bus | Atomic "save + publish" |
| Eventual consistency / saga | Across services | Decouple business logic from money |
| Database-per-service | All services | True service isolation, no shared DB |
| Bounded contexts | Service boundaries | Clean domain separation |
| Money as integer minor units | Ledger schema | Never float for money |

---

## 2b. Diagrams (ASCII)

### Overall architecture

```
                        +-----------------+
                        |   API gateway   |
                        +--------+--------+
            +--------------------+--------------------+
            v                    v                    v
  +------------------+ +------------------+ +------------------+
  | Prediction svc   | |  Fixture svc     | |  Ledger svc      |
  | Python.FastAPI   | |  Python.FastAPI  | |  Java.Spring     |
  | picks,lock,users | |  sync,odds,result| |  money,audit     |
  +--------+---------+ +--------+---------+ +--------+---------+
           |                    |                    : (listens only)
           v                    v                    :
        +-----------------------------------------v--+
        |                  Event bus                  |
        |       MatchSettled, PickLocked events       |
        +---------------------+-----------------------+
                              v
                     +------------------+
                     | Notification svc |
                     | Python.Telegram  |
                     +------------------+

  Database-per-service:
  [prediction db]   [fixture db]   [ledger db <- owned by ledger only]
```

The dashed line from Ledger means Ledger never actively calls another service —
it only listens for MatchSettled, then posts money itself (choreography-based
saga + eventual consistency).

### Settlement saga

```
  Admin enters score (or auto from fixture API)
        |
        v
  Fixture svc evaluates picks (win / lose)
        |
        v
  Publish "MatchSettled"  <-- via transactional outbox
        |
        v
  Ledger consumes event
        |
        v
  Check idempotency key --- already processed? ---+
        | (new)                       (seen)       |
        v                                          v
  Post double-entry                  Skip + ack (NO double charge)
  (debit loser, credit pool)
        |
        v
  Write audit log (append-only: who/when/why)
        |
        v
  Balance view = sum of postings
        |
        v
  Notify players (Telegram, optional)
```

### Double-entry ledger schema

```
  +-------------------+         +------------------------+
  |     accounts      |         |    journal_entries     |
  +-------------------+         +------------------------+
  | id            PK  |         | id                PK   |
  | owner_type        |         | idempotency_key   UK   | <- guards double
  | owner_id          |         | reason                 |    posting at DB
  | currency          |         | match_id               |
  | created_at        |         | posted_at              |
  +---------+---------+         +-----------+------------+
            | 1                             | 1
            | N           +-----------------+ N
            v             v
        +---------------------------+      +--------------------+
        |        postings           |      |     audit_log      |
        +---------------------------+      +--------------------+
        | id                   PK   |      | id            PK   |
        | journal_entry_id     FK   |      | journal_entry_id FK|
        | account_id           FK   |      | actor              |
        | amount_minor  (bigint)    |      | action             |
        | direction (debit/credit)  |      | created_at         |
        +---------------------------+      +--------------------+

  Each journal_entry has 1..N postings; total debit = total credit (always).
  Money is amount_minor (bigint, smallest unit) — NEVER float.
```

### Bounded context ownership

```
  +------------------------------+    +------------------------------+
  | Prediction context (Python)  |    |  Fixture context (Python)    |
  | Owns: users, groups, picks   |    |  Owns: matches, rounds, odds |
  | Owns: pick status, lock      |<---|  Owns: scores, sync schedule |
  | Knows match_id (ref only)    |odds|  Source of truth: results    |
  +------------------------------+    +---------------+--------------+
                                                      | MatchSettled
            +------------------------------------------+ event
            v
  +------------------------------+    +------------------------------+
  |   Ledger context (Java)      |    | Notification context (Python)|
  | Owns: accounts, postings     |--->|  Owns: delivery log, prefs   |
  | Owns: journal, audit         |evts|  Owns: Telegram chat mapping |
  | Knows user_id (ref only)     |    |  Stateless consumer          |
  +------------------------------+    +------------------------------+

  Shared kernel: minimal — only IDs and event contracts cross boundaries.
```

Each context only holds reference IDs of other contexts, never their data.
This is the data-ownership rule that prevents a "distributed monolith".

---

## 3. Service decomposition

Four services, split by **bounded context**, not by language. Language is then
assigned to fit each context.

### Prediction service — Python / FastAPI

Owns users, groups, picks, pick lock state. Handles registration, login,
prediction submission, and enforces the lock window (T-15min before kickoff).
Holds `match_id` only as a reference — never match details.

### Fixture service — Python / FastAPI

Owns matches, rounds, odds, scores, and the sync schedule. Pulls World Cup
fixtures, refreshes Asian-handicap odds every 15 minutes (or on admin trigger),
and is the **source of truth for match results**. Pulls next-round fixtures
once a round completes (knockout matchups are only known after the prior round).

### Ledger service — Java / Spring Boot

Owns accounts, journal entries, postings, and audit log. The only service that
touches money. Consumes settlement events and posts balanced double-entry
transactions idempotently. Holds `user_id` only as a reference.

### Notification service — Python / FastAPI

Owns delivery log and Telegram chat mappings. Stateless event consumer. Sends
"you haven't picked yet" reminders at T-30min and result notifications after
settlement. Entirely optional to the core flow.

---

## 4. Match lifecycle

1. **Fixture sync job** pulls matches into the Fixture DB (status: scheduled),
   refreshes odds on a 15-minute schedule or admin trigger.
2. **Prediction window opens** — players pick until T-15min before kickoff.
3. **Lock job fires** at T-15min — locks all picks; any player with no pick is
   marked as an automatic loss.
4. **Telegram reminder** (optional) at T-30min nudges players who haven't picked.
5. **Result settlement** — admin enters the final score (or it arrives from the
   fixture API); Fixture service evaluates each pick as win/lose.
6. **Ledger posting** — a `MatchSettled` event triggers the ledger to post
   double-entry transactions, idempotently, with an audit log entry.

---

## 5. Settlement saga (the critical path)

```
Admin enters score
   -> Fixture service evaluates picks (win/lose)
   -> Publish MatchSettled  [via transactional outbox]
   -> Ledger consumes event
        -> check idempotency key
             - already seen -> skip + ack (no double charge)
             - new          -> post double-entry, write audit log
   -> Balance view recomputed (sum of postings)
   -> Notify players (optional Telegram)
```

**Transactional outbox:** Fixture service writes the event to an `outbox` table
in the *same DB transaction* as the result. A separate worker reads the outbox
and publishes. This makes "save result" and "publish event" atomic — neither
can succeed without the other.

**Idempotency key:** every settlement event carries a unique key
(e.g. `match_42_settled`). The ledger records processed keys; a repeated event
is skipped but still acknowledged. The key is also a UNIQUE constraint on the
journal table, so the database itself is the last line of defense against
double posting.

---

## 6. Double-entry ledger schema

Tables: `accounts`, `journal_entries`, `postings`, `audit_log`.

- An **account** belongs to a player or to the pool/house.
- A **journal entry** groups a balanced set of postings, carries the
  `idempotency_key` (UNIQUE), a `reason`, and an optional `match_id`.
- Each **posting** is one debit or credit against one account, in
  `amount_minor` (integer, smallest currency unit).
- **audit_log** records who/what/when for every journal entry (append-only).

### Key rules

- **No stored balance column.** A balance is the sum of an account's postings.
  Balance is always *computed from truth*, never updated in place. (Add a
  snapshot/cache table later for speed; postings remain the source of truth.)
- **Every journal entry balances:** total debits = total credits.
- **Money is integer minor units (bigint), never float.** `0.1 + 0.2 != 0.3`
  in floating point — using float for money is a hard fail in fintech.

### Worked example — player A loses a 20k stake

| Posting | Account | Direction | amount_minor |
|---|---|---|---|
| 1 | Player A | debit | 20000 |
| 2 | Pool / house | credit | 20000 |

Sum = 0. Money moved, none created or destroyed.

### Worked example — player A pays in 40k cash (was -20k, becomes +20k)

| Posting | Account | Direction | amount_minor |
|---|---|---|---|
| 1 | Cash received | debit | 40000 |
| 2 | Player A | credit | 40000 |

No manual balance edit. The ledger sums to the new balance automatically, and
the transaction is fully traceable via the audit log.

---

## 7. Bounded context ownership

Each context owns its data and exposes only IDs and event contracts at the
boundary. No shared database between services (that would be a "distributed
monolith" — microservices in name only).

- Prediction owns users/groups/picks; references `match_id`.
- Fixture owns matches/odds/scores; source of truth for results.
- Ledger owns money; references `user_id`.
- Notification owns delivery; stateless consumer.

When the ledger needs to display "who", it asks the Prediction service or
receives the data via event — it never stores player names or emails itself.

---

## 8. Architecture Decision Records (for interviews)

Each ADR is phrased so you can speak it aloud in an interview.

### ADR-001 — Microservices over monolith

**Decision:** Split into four services despite the small scale.

**Reasoning to say:** "For a private group, a monolith is genuinely the correct
choice technically. I deliberately chose microservices to demonstrate
database-per-service, event-driven communication, and separation of the money
context from the business context. I'd flag in a real product that the
operational overhead isn't justified at this scale." — This signals you know
*when not* to use microservices, which is the senior tell.

### ADR-002 — Java for the ledger, Python for the rest

**Decision:** Money-handling service in Java/Spring; everything else in
Python/FastAPI.

**Reasoning to say:** "The ledger needs strong ACID guarantees, transaction
integrity, and type safety, so I put it on the JVM, where most UK core banking
runs. The other services are I/O-bound — external API calls, scheduled jobs,
async — which fits Python's async model. The split follows the consistency
requirement, not personal preference."

### ADR-003 — Double-entry over a single balance column

**Decision:** Balances are computed from postings; no stored balance.

**Reasoning to say:** "A single mutable balance column can drift and can't be
audited. Double-entry makes every change a balanced pair, makes balance a
derived fact, and gives a complete audit trail. It's the same model real
ledgers and accounting systems use."

### ADR-004 — Idempotent settlement

**Decision:** Settlement consumer is idempotent via unique key + DB constraint.

**Reasoning to say:** "Events get redelivered — network retries, consumer
restarts. Without idempotency the ledger would double-charge. I use an
idempotency key checked in the consumer, backed by a UNIQUE constraint on the
journal table as a final guard at the database layer."

### ADR-005 — Transactional outbox

**Decision:** Events published via an outbox table, not directly.

**Reasoning to say:** "Writing to the DB and publishing an event are two
separate systems and can't be a single atomic operation. The outbox pattern
writes the event in the same transaction as the data, and a worker publishes
it afterward, so I never lose an event or publish one for a write that rolled
back."

### ADR-006 — Eventual consistency between business and money

**Decision:** Money settlement is decoupled from result evaluation via events.

**Reasoning to say:** "The result (who won the pick) and the money movement
don't have to be in one transaction across services. I use a choreography-based
saga: Fixture publishes MatchSettled, Ledger reacts. They're eventually
consistent, which is acceptable here and avoids distributed transactions."

---

## 9. World Cup 2026 data notes

- 48 teams, 12 groups of 4. Each team plays 3 group matches.
- Top 2 per group + 8 best third-placed teams advance.
- Stages: Group -> Round of 32 -> Round of 16 -> Quarter-finals ->
  Semi-finals -> Final. 104 matches total; 72 in the group stage.
- Group stage: 11-27 June 2026. Final: 19 July 2026.
- Knockout matchups are only determined after the prior round finishes —
  this is why the fixture sync pulls next-round data once a round completes.

(Stake config example: group stage 10k, R32 20k, quarter-finals 100k, etc.,
configurable per match or per round by admin.)

---

## 10. Build-specific decisions

The following decisions were made when turning this design into an
implementation and are recorded in full as ADRs under `adr/`:

- **Money / currency** — currency is VND; amounts are integer `BIGINT` minor
  units (ADR-0007).
- **Pick evaluation** — Fixture evaluates picks against a local read-model fed
  by `PickLocked` events (event-carried state transfer); schedule/odds reads
  are synchronous REST (ADR-0008).
- **Payout model** — losers fund a common pool; winners receive no posting; the
  pool is later spent on group activities (ADR-0009).
- **Notification service** — deferred; the event contracts already accommodate
  it as a future consumer.
