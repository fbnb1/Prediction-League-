package com.predictionleague.ledger.domain;

/**
 * The side of a posting. By convention, an account's balance is
 * sum(CREDIT amounts) - sum(DEBIT amounts).
 */
public enum Direction {
    DEBIT,
    CREDIT
}
