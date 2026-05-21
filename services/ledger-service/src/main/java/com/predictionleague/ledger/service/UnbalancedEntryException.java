package com.predictionleague.ledger.service;

/** Thrown when a journal entry's postings do not balance. Maps to HTTP 422. */
public class UnbalancedEntryException extends RuntimeException {

    public UnbalancedEntryException(String message) {
        super(message);
    }
}
