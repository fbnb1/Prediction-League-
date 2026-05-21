package com.predictionleague.ledger.api;

import com.predictionleague.ledger.api.dto.JournalEntryView;
import com.predictionleague.ledger.api.dto.PostingView;
import com.predictionleague.ledger.domain.JournalEntry;
import com.predictionleague.ledger.repository.JournalEntryRepository;
import com.predictionleague.ledger.repository.PostingRepository;
import com.predictionleague.ledger.service.LedgerNotFoundException;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/journal-entries")
public class JournalEntryController {

    private final JournalEntryRepository journalEntries;
    private final PostingRepository postings;

    public JournalEntryController(JournalEntryRepository journalEntries, PostingRepository postings) {
        this.journalEntries = journalEntries;
        this.postings = postings;
    }

    @GetMapping
    public List<JournalEntryView> recent() {
        return journalEntries.findTop200ByOrderByIdDesc().stream().map(this::toView).toList();
    }

    @GetMapping("/{id}")
    public JournalEntryView one(@PathVariable Long id) {
        JournalEntry entry = journalEntries.findById(id)
                .orElseThrow(() -> new LedgerNotFoundException("journal entry " + id + " not found"));
        return toView(entry);
    }

    private JournalEntryView toView(JournalEntry entry) {
        List<PostingView> lines = postings.findByJournalEntryIdOrderByIdAsc(entry.getId()).stream()
                .map(PostingView::of)
                .toList();
        return new JournalEntryView(
                entry.getId(),
                entry.getIdempotencyKey(),
                entry.getReason(),
                entry.getMatchId(),
                entry.getPostedAt(),
                lines);
    }
}
