package com.predictionleague.ledger.api;

import com.predictionleague.ledger.api.dto.DepositView;
import com.predictionleague.ledger.domain.Account;
import com.predictionleague.ledger.domain.Direction;
import com.predictionleague.ledger.domain.JournalEntry;
import com.predictionleague.ledger.domain.OwnerType;
import com.predictionleague.ledger.domain.Posting;
import com.predictionleague.ledger.repository.AccountRepository;
import com.predictionleague.ledger.repository.JournalEntryRepository;
import com.predictionleague.ledger.repository.PostingRepository;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * Read model for cash pay-ins. A deposit is, by construction, a credit posting
 * on a player's per-group account ({@code userId:groupId}); losses only ever
 * debit those accounts, so credit postings are exactly the deposits.
 */
@RestController
@RequestMapping("/deposits")
public class DepositController {

    private final AccountRepository accounts;
    private final PostingRepository postings;
    private final JournalEntryRepository journalEntries;

    public DepositController(AccountRepository accounts,
                             PostingRepository postings,
                             JournalEntryRepository journalEntries) {
        this.accounts = accounts;
        this.postings = postings;
        this.journalEntries = journalEntries;
    }

    @GetMapping
    public List<DepositView> list(
            @RequestParam String groupId,
            @RequestParam(required = false) String userId) {
        List<Account> playerAccounts;
        if (userId != null && !userId.isBlank()) {
            playerAccounts = accounts
                    .findByOwnerTypeAndOwnerId(OwnerType.PLAYER, userId + ":" + groupId)
                    .map(List::of)
                    .orElseGet(List::of);
        } else {
            playerAccounts = accounts.findByOwnerTypeAndOwnerIdEndingWith(
                    OwnerType.PLAYER, ":" + groupId);
        }

        List<DepositView> deposits = new ArrayList<>();
        for (Account account : playerAccounts) {
            String depositor = account.getOwnerId().split(":", 2)[0];
            for (Posting posting : postings.findByAccountIdAndDirectionOrderByIdAsc(
                    account.getId(), Direction.CREDIT)) {
                Optional<JournalEntry> entry = journalEntries.findById(
                        posting.getJournalEntryId());
                deposits.add(new DepositView(
                        posting.getJournalEntryId(),
                        depositor,
                        groupId,
                        posting.getAmountMinor(),
                        entry.map(JournalEntry::getPostedAt).orElse(null)));
            }
        }
        deposits.sort(Comparator.comparing(
                DepositView::postedAt, Comparator.nullsLast(Comparator.naturalOrder())));
        return deposits;
    }
}
