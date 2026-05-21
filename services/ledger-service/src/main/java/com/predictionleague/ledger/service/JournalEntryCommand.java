package com.predictionleague.ledger.service;

import java.util.List;

/**
 * A request to post one balanced journal entry. {@code matchId} may be null.
 * The {@code lines} must balance: total debits == total credits.
 */
public record JournalEntryCommand(
        String idempotencyKey,
        String reason,
        String matchId,
        String actor,
        String action,
        List<PostingLine> lines) {
}
