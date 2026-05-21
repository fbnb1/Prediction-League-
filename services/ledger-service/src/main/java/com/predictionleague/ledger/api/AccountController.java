package com.predictionleague.ledger.api;

import com.predictionleague.ledger.api.dto.AccountView;
import com.predictionleague.ledger.api.dto.PlayerAccountView;
import com.predictionleague.ledger.api.dto.PostingView;
import com.predictionleague.ledger.domain.Account;
import com.predictionleague.ledger.domain.Direction;
import com.predictionleague.ledger.domain.OwnerType;
import com.predictionleague.ledger.repository.AccountRepository;
import com.predictionleague.ledger.repository.PostingRepository;
import com.predictionleague.ledger.service.LedgerNotFoundException;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/accounts")
public class AccountController {

    private final AccountRepository accounts;
    private final PostingRepository postings;

    public AccountController(AccountRepository accounts, PostingRepository postings) {
        this.accounts = accounts;
        this.postings = postings;
    }

    @GetMapping
    public List<AccountView> all() {
        return accounts.findAll().stream()
                .map(account -> AccountView.of(account, postings.balanceOf(account.getId())))
                .toList();
    }

    /**
     * A player's per-group balance ({@code userId:groupId}), split into deposits
     * (credits) and losses (debits). Returns zeros if the account has no
     * postings yet, so callers need not special-case new players.
     */
    @GetMapping("/player")
    public PlayerAccountView player(
            @RequestParam String userId, @RequestParam String groupId) {
        String ownerId = userId + ":" + groupId;
        return accounts.findByOwnerTypeAndOwnerId(OwnerType.PLAYER, ownerId)
                .map(account -> {
                    long credit = postings.sumByAccountIdAndDirection(
                            account.getId(), Direction.CREDIT);
                    long debit = postings.sumByAccountIdAndDirection(
                            account.getId(), Direction.DEBIT);
                    return new PlayerAccountView(ownerId, debit, credit, credit - debit);
                })
                .orElse(new PlayerAccountView(ownerId, 0, 0, 0));
    }

    @GetMapping("/{ownerType}/{ownerId}")
    public AccountView one(@PathVariable OwnerType ownerType, @PathVariable String ownerId) {
        Account account = requireAccount(ownerType, ownerId);
        return AccountView.of(account, postings.balanceOf(account.getId()));
    }

    @GetMapping("/{ownerType}/{ownerId}/postings")
    public List<PostingView> postingsOf(@PathVariable OwnerType ownerType, @PathVariable String ownerId) {
        Account account = requireAccount(ownerType, ownerId);
        return postings.findByAccountIdOrderByIdAsc(account.getId()).stream()
                .map(PostingView::of)
                .toList();
    }

    private Account requireAccount(OwnerType ownerType, String ownerId) {
        return accounts.findByOwnerTypeAndOwnerId(ownerType, ownerId)
                .orElseThrow(() -> new LedgerNotFoundException(
                        "account " + ownerType + "/" + ownerId + " not found"));
    }
}
