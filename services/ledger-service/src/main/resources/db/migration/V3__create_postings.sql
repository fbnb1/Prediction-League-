-- Postings. One debit or credit against one account, in integer minor units.
-- A journal entry's postings always sum to zero (total debit = total credit);
-- that invariant is enforced in the application layer before insert.
CREATE TABLE postings (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    journal_entry_id  BIGINT     NOT NULL REFERENCES journal_entries (id),
    account_id        BIGINT     NOT NULL REFERENCES accounts (id),
    amount_minor      BIGINT     NOT NULL,
    direction         VARCHAR(6) NOT NULL,
    CONSTRAINT chk_postings_amount_positive CHECK (amount_minor > 0),
    CONSTRAINT chk_postings_direction CHECK (direction IN ('DEBIT', 'CREDIT'))
);

CREATE INDEX idx_postings_account_id ON postings (account_id);
CREATE INDEX idx_postings_journal_entry_id ON postings (journal_entry_id);
