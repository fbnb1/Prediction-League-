package com.predictionleague.ledger.api;

import com.predictionleague.ledger.api.dto.DepositRequest;
import com.predictionleague.ledger.api.dto.ManualEntryRequest;
import com.predictionleague.ledger.domain.JournalEntry;
import com.predictionleague.ledger.service.AccountRef;
import com.predictionleague.ledger.service.JournalEntryCommand;
import com.predictionleague.ledger.service.LedgerService;
import com.predictionleague.ledger.service.PostingLine;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/** Admin operations. Guarded by {@link AdminApiKeyFilter}. */
@RestController
@RequestMapping("/admin")
public class AdminController {

    private final LedgerService ledgerService;

    public AdminController(LedgerService ledgerService) {
        this.ledgerService = ledgerService;
    }

    @PostMapping("/journal-entries")
    @ResponseStatus(HttpStatus.CREATED)
    public JournalEntryRef create(@Valid @RequestBody ManualEntryRequest request) {
        List<PostingLine> lines = request.lines().stream()
                .map(line -> new PostingLine(
                        new AccountRef(line.ownerType(), line.ownerId()),
                        line.amountMinor(),
                        line.direction()))
                .toList();
        JournalEntryCommand command = new JournalEntryCommand(
                request.idempotencyKey(),
                request.reason(),
                request.matchId(),
                request.actor(),
                "MANUAL_ENTRY",
                lines);
        JournalEntry entry = ledgerService.postManualEntry(command);
        return new JournalEntryRef(entry.getId(), entry.getIdempotencyKey());
    }

    @PostMapping("/deposits")
    @ResponseStatus(HttpStatus.CREATED)
    public JournalEntryRef deposit(@Valid @RequestBody DepositRequest request) {
        JournalEntry entry = ledgerService.deposit(
                request.groupId(), request.depositor(), request.amountMinor());
        return new JournalEntryRef(entry.getId(), entry.getIdempotencyKey());
    }

    @PostMapping("/journal-entries/{id}/reverse")
    @ResponseStatus(HttpStatus.CREATED)
    public JournalEntryRef reverse(@PathVariable Long id, @RequestParam(defaultValue = "admin") String actor) {
        JournalEntry entry = ledgerService.reverse(id, "admin:" + actor);
        return new JournalEntryRef(entry.getId(), entry.getIdempotencyKey());
    }

    public record JournalEntryRef(Long id, String idempotencyKey) {
    }
}
