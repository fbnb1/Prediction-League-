package com.predictionleague.ledger.api.dto;

import com.predictionleague.ledger.domain.AuditLog;
import java.time.Instant;

public record AuditLogView(
        Long id,
        Long journalEntryId,
        String actor,
        String action,
        Instant createdAt) {

    public static AuditLogView of(AuditLog auditLog) {
        return new AuditLogView(
                auditLog.getId(),
                auditLog.getJournalEntryId(),
                auditLog.getActor(),
                auditLog.getAction(),
                auditLog.getCreatedAt());
    }
}
