package com.predictionleague.ledger.service;

import com.predictionleague.ledger.domain.Direction;

/** One requested posting within a journal entry command. */
public record PostingLine(AccountRef account, long amountMinor, Direction direction) {
}
