package com.predictionleague.ledger.messaging;

import java.time.Instant;
import java.util.List;

/**
 * The MatchSettled event consumed from the bus. JSON is snake_case on the wire
 * and mapped to these camelCase components by the snake-case ObjectMapper.
 * See docs/event-contracts.md.
 */
public record MatchSettledEvent(
        String event,
        String eventId,
        Integer eventVersion,
        Instant occurredAt,
        String matchId,
        String currency,
        MatchResult result,
        List<SettlementLine> settlements) {

    public record MatchResult(Integer homeScore, Integer awayScore, String outcome) {
    }

    public record SettlementLine(
            String userId,
            String groupId,
            String predictedOutcome,
            SettlementResult result,
            Long stakeMinor) {
    }

    public enum SettlementResult {
        WON,
        LOST
    }
}
