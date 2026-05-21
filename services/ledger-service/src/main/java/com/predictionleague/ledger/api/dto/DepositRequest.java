package com.predictionleague.ledger.api.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

/** Request body for recording a player's cash pay-in into a group pool. */
public record DepositRequest(
        @NotBlank String groupId,
        @NotBlank String depositor,
        @Positive long amountMinor) {
}
