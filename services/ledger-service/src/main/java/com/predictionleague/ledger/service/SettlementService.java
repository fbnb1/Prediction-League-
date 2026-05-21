package com.predictionleague.ledger.service;

import com.predictionleague.ledger.domain.Direction;
import com.predictionleague.ledger.repository.JournalEntryRepository;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Settles one losing pick from a MatchSettled event: debits the loser, credits
 * the common pool. Winners are never passed here -- see ADR-0009.
 *
 * Each call is its own transaction so a partially-processed event resumes
 * cleanly on redelivery; the idempotency key makes already-settled lines no-ops.
 */
@Service
public class SettlementService {

    private static final Logger log = LoggerFactory.getLogger(SettlementService.class);

    private final PostingService postingService;
    private final JournalEntryRepository journalEntries;

    public SettlementService(PostingService postingService, JournalEntryRepository journalEntries) {
        this.postingService = postingService;
        this.journalEntries = journalEntries;
    }

    @Transactional
    public void settleLosingPick(
            String eventId, String matchId, String groupId, String userId, long stakeMinor) {
        // groupId is part of the key: one user may lose the same match in
        // several groups, each its own balanced posting.
        String idempotencyKey = eventId + ":" + groupId + ":" + userId;

        if (journalEntries.existsByIdempotencyKey(idempotencyKey)) {
            log.info("settlement {} already processed -- skipping", idempotencyKey);
            return;
        }

        JournalEntryCommand command = new JournalEntryCommand(
                idempotencyKey,
                "SETTLE_PICK match=" + matchId + " group=" + groupId + " user=" + userId,
                matchId,
                "system:ledger-consumer",
                "SETTLE_PICK",
                List.of(
                        new PostingLine(AccountRef.player(userId), stakeMinor, Direction.DEBIT),
                        new PostingLine(AccountRef.pool(groupId), stakeMinor, Direction.CREDIT)));

        postingService.post(command);
        log.info("settled {}: debit player {} / credit pool {}, {} minor units",
                idempotencyKey, userId, groupId, stakeMinor);
    }
}
