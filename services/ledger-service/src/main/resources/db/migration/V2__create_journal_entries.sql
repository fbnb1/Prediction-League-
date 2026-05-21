-- Journal entries. Each entry groups a balanced set of postings.
-- idempotency_key is UNIQUE: it is the database-level guard that makes
-- settlement idempotent -- a redelivered event can never post twice.
CREATE TABLE journal_entries (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    idempotency_key  VARCHAR(128) NOT NULL,
    reason           VARCHAR(255) NOT NULL,
    match_id         VARCHAR(64),
    posted_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uq_journal_entries_idempotency_key UNIQUE (idempotency_key)
);
