package com.predictionleague.ledger.service;

import com.predictionleague.ledger.domain.Account;
import com.predictionleague.ledger.domain.AuditLog;
import com.predictionleague.ledger.domain.Direction;
import com.predictionleague.ledger.domain.JournalEntry;
import com.predictionleague.ledger.domain.Posting;
import com.predictionleague.ledger.repository.AccountRepository;
import com.predictionleague.ledger.repository.AuditLogRepository;
import com.predictionleague.ledger.repository.JournalEntryRepository;
import com.predictionleague.ledger.repository.PostingRepository;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * The core ledger primitive: posts one balanced double-entry journal entry.
 * Refuses to persist anything unless total debits equal total credits.
 */
@Service
public class PostingService {

    private static final String DEFAULT_CURRENCY = "VND";

    private final AccountRepository accounts;
    private final JournalEntryRepository journalEntries;
    private final PostingRepository postings;
    private final AuditLogRepository auditLog;

    public PostingService(AccountRepository accounts,
                          JournalEntryRepository journalEntries,
                          PostingRepository postings,
                          AuditLogRepository auditLog) {
        this.accounts = accounts;
        this.journalEntries = journalEntries;
        this.postings = postings;
        this.auditLog = auditLog;
    }

    @Transactional
    public JournalEntry post(JournalEntryCommand command) {
        validateBalanced(command);

        JournalEntry entry = journalEntries.save(
                new JournalEntry(command.idempotencyKey(), command.reason(), command.matchId()));

        for (PostingLine line : command.lines()) {
            Account account = resolveAccount(line.account());
            postings.save(new Posting(entry.getId(), account.getId(), line.amountMinor(), line.direction()));
        }

        auditLog.save(new AuditLog(entry.getId(), command.actor(), command.action()));
        return entry;
    }

    private void validateBalanced(JournalEntryCommand command) {
        List<PostingLine> lines = command.lines();
        if (lines == null || lines.size() < 2) {
            throw new UnbalancedEntryException("a journal entry needs at least two postings");
        }
        long debit = 0;
        long credit = 0;
        for (PostingLine line : lines) {
            if (line.amountMinor() <= 0) {
                throw new UnbalancedEntryException("posting amount must be a positive number of minor units");
            }
            if (line.direction() == Direction.DEBIT) {
                debit += line.amountMinor();
            } else {
                credit += line.amountMinor();
            }
        }
        if (debit != credit) {
            throw new UnbalancedEntryException(
                    "unbalanced entry: debits (" + debit + ") must equal credits (" + credit + ")");
        }
    }

    /** Player accounts are created lazily on first use; system accounts are seeded. */
    private Account resolveAccount(AccountRef ref) {
        return accounts.findByOwnerTypeAndOwnerId(ref.ownerType(), ref.ownerId())
                .orElseGet(() -> accounts.save(new Account(ref.ownerType(), ref.ownerId(), DEFAULT_CURRENCY)));
    }
}
