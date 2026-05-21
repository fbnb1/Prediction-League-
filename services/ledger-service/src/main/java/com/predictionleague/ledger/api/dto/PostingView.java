package com.predictionleague.ledger.api.dto;

import com.predictionleague.ledger.domain.Direction;
import com.predictionleague.ledger.domain.Posting;

public record PostingView(
        Long id,
        Long journalEntryId,
        Long accountId,
        long amountMinor,
        Direction direction) {

    public static PostingView of(Posting posting) {
        return new PostingView(
                posting.getId(),
                posting.getJournalEntryId(),
                posting.getAccountId(),
                posting.getAmountMinor(),
                posting.getDirection());
    }
}
