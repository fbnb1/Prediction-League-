package com.predictionleague.ledger.service;

/** Thrown when a journal entry reuses an existing idempotency key. Maps to HTTP 409. */
public class DuplicateIdempotencyKeyException extends RuntimeException {

    public DuplicateIdempotencyKeyException(String idempotencyKey) {
        super("a journal entry with idempotency key '" + idempotencyKey + "' already exists");
    }
}
