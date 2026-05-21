package com.predictionleague.ledger.api;

import com.predictionleague.ledger.api.dto.AuditLogView;
import com.predictionleague.ledger.repository.AuditLogRepository;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/audit-log")
public class AuditController {

    private final AuditLogRepository auditLog;

    public AuditController(AuditLogRepository auditLog) {
        this.auditLog = auditLog;
    }

    @GetMapping
    public List<AuditLogView> recent() {
        return auditLog.findTop200ByOrderByIdDesc().stream().map(AuditLogView::of).toList();
    }
}
