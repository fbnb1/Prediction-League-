package com.predictionleague.ledger.api.dto;

/**
 * A player's per-group balance, split into its parts. For a player account
 * ({@code userId:groupId}) credits are deposits and debits are losses, so:
 * {@code creditMinor} is money paid in, {@code debitMinor} is money lost,
 * and {@code balanceMinor = creditMinor - debitMinor} (negative = still owed).
 */
public record PlayerAccountView(
        String ownerId,
        long debitMinor,
        long creditMinor,
        long balanceMinor) {
}
