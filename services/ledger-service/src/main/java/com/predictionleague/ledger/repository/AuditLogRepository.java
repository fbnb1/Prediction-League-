package com.predictionleague.ledger.repository;

import com.predictionleague.ledger.domain.AuditLog;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AuditLogRepository extends JpaRepository<AuditLog, Long> {

    List<AuditLog> findTop200ByOrderByIdDesc();

    List<AuditLog> findByJournalEntryIdOrderByIdAsc(Long journalEntryId);
}
