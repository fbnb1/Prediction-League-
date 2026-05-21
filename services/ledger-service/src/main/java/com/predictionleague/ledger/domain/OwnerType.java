package com.predictionleague.ledger.domain;

/**
 * What an account belongs to. PLAYER accounts reference a Prediction service
 * user_id; the others are fixed system accounts seeded by migration.
 */
public enum OwnerType {
    PLAYER,
    POOL,
    ACTIVITY_EXPENSE,
    CASH_RECEIVED
}
