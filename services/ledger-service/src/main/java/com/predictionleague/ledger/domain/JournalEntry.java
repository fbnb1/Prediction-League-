package com.predictionleague.ledger.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;

/**
 * A balanced set of postings. The idempotency_key is UNIQUE in the database,
 * which is the final guard against double posting on event redelivery.
 */
@Entity
@Table(name = "journal_entries")
public class JournalEntry {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "idempotency_key", nullable = false, length = 128, unique = true)
    private String idempotencyKey;

    @Column(nullable = false, length = 255)
    private String reason;

    @Column(name = "match_id", length = 64)
    private String matchId;

    @Column(name = "posted_at", nullable = false)
    private Instant postedAt;

    protected JournalEntry() {
        // for JPA
    }

    public JournalEntry(String idempotencyKey, String reason, String matchId) {
        this.idempotencyKey = idempotencyKey;
        this.reason = reason;
        this.matchId = matchId;
        this.postedAt = Instant.now();
    }

    public Long getId() {
        return id;
    }

    public String getIdempotencyKey() {
        return idempotencyKey;
    }

    public String getReason() {
        return reason;
    }

    public String getMatchId() {
        return matchId;
    }

    public Instant getPostedAt() {
        return postedAt;
    }
}
