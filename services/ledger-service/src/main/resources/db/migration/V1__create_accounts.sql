-- Accounts. An account belongs to a player or to a system role (pool, etc.).
-- (owner_type, owner_id) is the natural key; owner_id for a PLAYER is the
-- Prediction service user_id, held only as an opaque reference.
CREATE TABLE accounts (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_type  VARCHAR(32)  NOT NULL,
    owner_id    VARCHAR(64)  NOT NULL,
    currency    VARCHAR(3)   NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uq_accounts_owner UNIQUE (owner_type, owner_id),
    CONSTRAINT chk_accounts_owner_type
        CHECK (owner_type IN ('PLAYER', 'POOL', 'ACTIVITY_EXPENSE', 'CASH_RECEIVED'))
);
