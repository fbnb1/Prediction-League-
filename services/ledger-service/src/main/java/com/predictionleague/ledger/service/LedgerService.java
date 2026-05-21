package com.predictionleague.ledger.service;

import com.predictionleague.ledger.domain.Account;
import com.predictionleague.ledger.domain.Direction;
import com.predictionleague.ledger.domain.JournalEntry;
import com.predictionleague.ledger.domain.Posting;
import com.predictionleague.ledger.repository.AccountRepository;
import com.predictionleague.ledger.repository.JournalEntryRepository;
import com.predictionleague.ledger.repository.PostingRepository;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Admin-initiated ledger operations: manual entries and reversals. */
@Service
public class LedgerService {

    private final PostingService postingService;
    private final JournalEntryRepository journalEntries;
    private final PostingRepository postings;
    private final AccountRepository accounts;

    public LedgerService(PostingService postingService,
                         JournalEntryRepository journalEntries,
                         PostingRepository postings,
                         AccountRepository accounts) {
        this.postingService = postingService;
        this.journalEntries = journalEntries;
        this.postings = postings;
        this.accounts = accounts;
    }

    /**
     * Records a cash pay-in: a player funds their own balance in a group. Posts
     * a balanced entry -- debit CASH_RECEIVED, credit the depositor's per-group
     * PLAYER account ({@code userId:groupId}) -- so that account's credit total
     * is the amount that player has deposited into the group.
     */
    @Transactional
    public JournalEntry deposit(String groupId, String depositor, long amountMinor) {
        if (amountMinor <= 0) {
            throw new UnbalancedEntryException("deposit amount must be a positive number of minor units");
        }
        String idempotencyKey = "deposit:" + UUID.randomUUID();
        JournalEntryCommand command = new JournalEntryCommand(
                idempotencyKey,
                "DEPOSIT group=" + groupId + " by=" + depositor,
                null,
                "deposit:" + depositor,
                "DEPOSIT",
                List.of(
                        new PostingLine(AccountRef.cashReceived(), amountMinor, com.predictionleague.ledger.domain.Direction.DEBIT),
                        new PostingLine(AccountRef.player(depositor, groupId), amountMinor, com.predictionleague.ledger.domain.Direction.CREDIT)));
        return postingService.post(command);
    }

    /** Posts a manually-supplied balanced entry (e.g. a cash pay-in, or spending the pool). */
    @Transactional
    public JournalEntry postManualEntry(JournalEntryCommand command) {
        if (journalEntries.existsByIdempotencyKey(command.idempotencyKey())) {
            throw new DuplicateIdempotencyKeyException(command.idempotencyKey());
        }
        return postingService.post(command);
    }

    /**
     * Reverses a journal entry by posting an equal-and-opposite balanced entry.
     * The original is never mutated or deleted -- a correction is itself a posting.
     */
    @Transactional
    public JournalEntry reverse(Long journalEntryId, String actor) {
        JournalEntry original = journalEntries.findById(journalEntryId)
                .orElseThrow(() -> new LedgerNotFoundException("journal entry " + journalEntryId + " not found"));

        String idempotencyKey = "reverse:" + journalEntryId;
        if (journalEntries.existsByIdempotencyKey(idempotencyKey)) {
            throw new DuplicateIdempotencyKeyException(idempotencyKey);
        }

        List<PostingLine> reversedLines = postings.findByJournalEntryIdOrderByIdAsc(journalEntryId).stream()
                .map(this::flip)
                .toList();

        JournalEntryCommand command = new JournalEntryCommand(
                idempotencyKey,
                "REVERSAL of journal entry " + journalEntryId,
                original.getMatchId(),
                actor,
                "REVERSE",
                reversedLines);

        return postingService.post(command);
    }

    private PostingLine flip(Posting posting) {
        Account account = accounts.findById(posting.getAccountId())
                .orElseThrow(() -> new LedgerNotFoundException("account " + posting.getAccountId() + " not found"));
        Direction flipped = posting.getDirection() == Direction.DEBIT ? Direction.CREDIT : Direction.DEBIT;
        return new PostingLine(
                new AccountRef(account.getOwnerType(), account.getOwnerId()),
                posting.getAmountMinor(),
                flipped);
    }
}
