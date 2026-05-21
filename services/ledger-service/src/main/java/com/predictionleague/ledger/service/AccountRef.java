package com.predictionleague.ledger.service;

import com.predictionleague.ledger.domain.OwnerType;

/** Identifies an account by its natural key, before it may exist in the DB. */
public record AccountRef(OwnerType ownerType, String ownerId) {

    public static final String COMMON_POOL_ID = "common-pool";
    public static final String ACTIVITY_EXPENSE_ID = "activity-expense";
    public static final String CASH_RECEIVED_ID = "cash-received";

    public static AccountRef player(String userId) {
        return new AccountRef(OwnerType.PLAYER, userId);
    }

    public static AccountRef pool() {
        return new AccountRef(OwnerType.POOL, COMMON_POOL_ID);
    }
}
