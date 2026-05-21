package com.predictionleague.ledger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.awaitility.Awaitility.await;

import com.predictionleague.ledger.domain.OwnerType;
import com.predictionleague.ledger.messaging.RabbitConfig;
import com.predictionleague.ledger.repository.AccountRepository;
import com.predictionleague.ledger.repository.AuditLogRepository;
import com.predictionleague.ledger.repository.JournalEntryRepository;
import com.predictionleague.ledger.repository.PostingRepository;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.amqp.core.Message;
import org.springframework.amqp.core.MessageBuilder;
import org.springframework.amqp.core.MessageProperties;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

/**
 * End-to-end integration test against real Postgres and RabbitMQ containers.
 * Covers the settlement consumer, idempotency, and the admin/query API.
 */
/*
 * Connects to the isolated Postgres + RabbitMQ provided by the `test` profile
 * in docker-compose.yml (hosts injected via environment variables).
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class LedgerIT {

    private static final String ADMIN_KEY = "dev-admin-key-change-me";

    private static final String MATCH_SETTLED_JSON = """
            {
              "event": "MatchSettled",
              "event_id": "evt-test-001",
              "event_version": 1,
              "occurred_at": "2026-06-11T21:05:00Z",
              "match_id": "WC2026-GS-TEST",
              "currency": "VND",
              "result": { "home_score": 2, "away_score": 1, "outcome": "HOME" },
              "settlements": [
                { "user_id": "usr_winner", "group_id": "grp_test", "predicted_outcome": "HOME", "result": "WON",  "stake_minor": 10000 },
                { "user_id": "usr_loserA", "group_id": "grp_test", "predicted_outcome": "AWAY", "result": "LOST", "stake_minor": 10000 },
                { "user_id": "usr_loserB", "group_id": "grp_test", "predicted_outcome": null,   "result": "LOST", "stake_minor": 10000 }
              ]
            }
            """;

    private static final String MANUAL_ENTRY_JSON = """
            {
              "idempotency_key": "manual-cash-001",
              "reason": "cash pay-in",
              "actor": "admin:test",
              "lines": [
                { "owner_type": "CASH_RECEIVED", "owner_id": "cash-received", "amount_minor": 40000, "direction": "DEBIT" },
                { "owner_type": "PLAYER", "owner_id": "usr_cashTest", "amount_minor": 40000, "direction": "CREDIT" }
              ]
            }
            """;

    private static final String UNBALANCED_ENTRY_JSON = """
            {
              "idempotency_key": "manual-bad-001",
              "reason": "deliberately unbalanced",
              "actor": "admin:test",
              "lines": [
                { "owner_type": "CASH_RECEIVED", "owner_id": "cash-received", "amount_minor": 40000, "direction": "DEBIT" },
                { "owner_type": "PLAYER", "owner_id": "usr_cashTest", "amount_minor": 30000, "direction": "CREDIT" }
              ]
            }
            """;

    @Autowired
    private RabbitTemplate rabbitTemplate;
    @Autowired
    private TestRestTemplate rest;
    @Autowired
    private AccountRepository accounts;
    @Autowired
    private PostingRepository postings;
    @Autowired
    private JournalEntryRepository journalEntries;
    @Autowired
    private AuditLogRepository auditLog;

    @BeforeEach
    void clean() {
        auditLog.deleteAll();
        postings.deleteAll();
        journalEntries.deleteAll();
        accounts.findAll().stream()
                .filter(account -> account.getOwnerType() == OwnerType.PLAYER)
                .forEach(accounts::delete);
    }

    @Test
    void consumesMatchSettledAndPostsBalancedDoubleEntry() {
        publishMatchSettled(MATCH_SETTLED_JSON);

        await().atMost(Duration.ofSeconds(20))
                .untilAsserted(() -> assertThat(journalEntries.count()).isEqualTo(2));

        // two losers debited 10000 each; the group's pool credited 20000 total
        assertThat(balanceOf(OwnerType.POOL, "grp_test")).isEqualTo(20_000L);
        assertThat(balanceOf(OwnerType.PLAYER, "usr_loserA")).isEqualTo(-10_000L);
        assertThat(balanceOf(OwnerType.PLAYER, "usr_loserB")).isEqualTo(-10_000L);
        // the winner is never charged, so no account is created for them
        assertThat(accounts.findByOwnerTypeAndOwnerId(OwnerType.PLAYER, "usr_winner")).isEmpty();
        assertThat(auditLog.count()).isEqualTo(2);
    }

    @Test
    void redeliveredMatchSettledDoesNotDoubleCharge() throws InterruptedException {
        publishMatchSettled(MATCH_SETTLED_JSON);
        await().atMost(Duration.ofSeconds(20))
                .untilAsserted(() -> assertThat(journalEntries.count()).isEqualTo(2));

        // same event_id again -- every per-user idempotency key collides
        publishMatchSettled(MATCH_SETTLED_JSON);
        Thread.sleep(3_000);

        assertThat(journalEntries.count()).isEqualTo(2);
        assertThat(balanceOf(OwnerType.POOL, "grp_test")).isEqualTo(20_000L);
    }

    @Test
    void manualBalancedEntryIsAccepted() {
        ResponseEntity<String> response = postAdmin("/admin/journal-entries", MANUAL_ENTRY_JSON, ADMIN_KEY);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(balanceOf(OwnerType.PLAYER, "usr_cashTest")).isEqualTo(40_000L);
    }

    @Test
    void manualUnbalancedEntryIsRejectedWith422() {
        ResponseEntity<String> response = postAdmin("/admin/journal-entries", UNBALANCED_ENTRY_JSON, ADMIN_KEY);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.UNPROCESSABLE_ENTITY);
        assertThat(journalEntries.findByIdempotencyKey("manual-bad-001")).isEmpty();
    }

    @Test
    void adminEndpointRejectsMissingApiKey() {
        ResponseEntity<String> response = postAdmin("/admin/journal-entries", MANUAL_ENTRY_JSON, "wrong-key");

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
    }

    private void publishMatchSettled(String json) {
        Message message = MessageBuilder.withBody(json.getBytes(StandardCharsets.UTF_8))
                .setContentType(MessageProperties.CONTENT_TYPE_JSON)
                .build();
        rabbitTemplate.send(RabbitConfig.EVENTS_EXCHANGE, RabbitConfig.MATCH_SETTLED_ROUTING_KEY, message);
    }

    private long balanceOf(OwnerType ownerType, String ownerId) {
        return accounts.findByOwnerTypeAndOwnerId(ownerType, ownerId)
                .map(account -> postings.balanceOf(account.getId()))
                .orElse(0L);
    }

    private ResponseEntity<String> postAdmin(String path, String body, String apiKey) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("X-Admin-Api-Key", apiKey);
        return rest.postForEntity(path, new HttpEntity<>(body, headers), String.class);
    }
}
