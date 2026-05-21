package com.predictionleague.ledger.messaging;

import com.predictionleague.ledger.service.SettlementService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

/**
 * Consumes MatchSettled events and posts a settlement for every losing pick.
 * Each losing pick is settled in its own transaction (see SettlementService),
 * so a redelivered or partially-processed event resumes cleanly.
 */
@Component
public class MatchSettledConsumer {

    private static final Logger log = LoggerFactory.getLogger(MatchSettledConsumer.class);

    private final SettlementService settlementService;

    public MatchSettledConsumer(SettlementService settlementService) {
        this.settlementService = settlementService;
    }

    @RabbitListener(queues = RabbitConfig.MATCH_SETTLED_QUEUE)
    public void onMatchSettled(MatchSettledEvent event) {
        int count = event.settlements() == null ? 0 : event.settlements().size();
        log.info("received MatchSettled event_id={} match_id={} settlements={}",
                event.eventId(), event.matchId(), count);

        if (event.settlements() == null) {
            return;
        }
        for (MatchSettledEvent.SettlementLine line : event.settlements()) {
            if (line.result() == MatchSettledEvent.SettlementResult.LOST) {
                settlementService.settleLosingPick(
                        event.eventId(),
                        event.matchId(),
                        line.groupId(),
                        line.userId(),
                        line.stakeMinor());
            }
        }
    }
}
