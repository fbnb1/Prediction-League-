-- Append-only audit log: who/what/when for every journal entry.
CREATE TABLE audit_log (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    journal_entry_id  BIGINT       NOT NULL REFERENCES journal_entries (id),
    actor             VARCHAR(128) NOT NULL,
    action            VARCHAR(64)  NOT NULL,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_log_journal_entry_id ON audit_log (journal_entry_id);
