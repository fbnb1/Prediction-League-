package com.predictionleague.ledger.repository;

import com.predictionleague.ledger.domain.JournalEntry;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface JournalEntryRepository extends JpaRepository<JournalEntry, Long> {

    boolean existsByIdempotencyKey(String idempotencyKey);

    Optional<JournalEntry> findByIdempotencyKey(String idempotencyKey);

    List<JournalEntry> findTop200ByOrderByIdDesc();
}
