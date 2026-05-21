package com.predictionleague.ledger.api.dto;

import com.predictionleague.ledger.domain.Account;
import com.predictionleague.ledger.domain.OwnerType;
import java.time.Instant;

public record AccountView(
        Long id,
        OwnerType ownerType,
        String ownerId,
        String currency,
        long balanceMinor,
        Instant createdAt) {

    public static AccountView of(Account account, long balanceMinor) {
        return new AccountView(
                account.getId(),
                account.getOwnerType(),
                account.getOwnerId(),
                account.getCurrency(),
                balanceMinor,
                account.getCreatedAt());
    }
}
