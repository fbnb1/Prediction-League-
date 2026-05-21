package com.predictionleague.ledger.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * One debit or credit against one account, in integer minor units.
 * Money is never a floating-point value.
 */
@Entity
@Table(name = "postings")
public class Posting {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "journal_entry_id", nullable = false)
    private Long journalEntryId;

    @Column(name = "account_id", nullable = false)
    private Long accountId;

    @Column(name = "amount_minor", nullable = false)
    private long amountMinor;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 6)
    private Direction direction;

    protected Posting() {
        // for JPA
    }

    public Posting(Long journalEntryId, Long accountId, long amountMinor, Direction direction) {
        this.journalEntryId = journalEntryId;
        this.accountId = accountId;
        this.amountMinor = amountMinor;
        this.direction = direction;
    }

    public Long getId() {
        return id;
    }

    public Long getJournalEntryId() {
        return journalEntryId;
    }

    public Long getAccountId() {
        return accountId;
    }

    public long getAmountMinor() {
        return amountMinor;
    }

    public Direction getDirection() {
        return direction;
    }
}
