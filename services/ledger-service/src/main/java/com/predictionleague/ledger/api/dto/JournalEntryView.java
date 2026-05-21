package com.predictionleague.ledger.api.dto;

import java.time.Instant;
import java.util.List;

public record JournalEntryView(
        Long id,
        String idempotencyKey,
        String reason,
        String matchId,
        Instant postedAt,
        List<PostingView> postings) {
}
