package com.predictionleague.ledger.service;

/** Thrown when a requested account or journal entry does not exist. Maps to HTTP 404. */
public class LedgerNotFoundException extends RuntimeException {

    public LedgerNotFoundException(String message) {
        super(message);
    }
}
