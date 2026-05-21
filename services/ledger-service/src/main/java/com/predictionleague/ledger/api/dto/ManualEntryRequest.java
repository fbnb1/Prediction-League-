package com.predictionleague.ledger.api.dto;

import com.predictionleague.ledger.domain.Direction;
import com.predictionleague.ledger.domain.OwnerType;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import java.util.List;

/** Request body for posting a manual balanced journal entry. */
public record ManualEntryRequest(
        @NotBlank String idempotencyKey,
        @NotBlank String reason,
        String matchId,
        @NotBlank String actor,
        @NotEmpty @Valid List<PostingLineRequest> lines) {

    public record PostingLineRequest(
            @NotNull OwnerType ownerType,
            @NotBlank String ownerId,
            @Positive long amountMinor,
            @NotNull Direction direction) {
    }
}
