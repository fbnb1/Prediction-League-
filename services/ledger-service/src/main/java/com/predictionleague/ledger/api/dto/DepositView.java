package com.predictionleague.ledger.api.dto;

import java.time.Instant;

/** One recorded cash pay-in: a credit posting on a player's per-group account. */
public record DepositView(
        Long entryId,
        String depositor,
        String groupId,
        long amountMinor,
        Instant postedAt) {
}
