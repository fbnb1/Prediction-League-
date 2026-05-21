package com.predictionleague.ledger.service;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.predictionleague.ledger.domain.Direction;
import java.util.List;
import org.junit.jupiter.api.Test;

/**
 * Unit tests for the balancing invariant. Validation runs before any repository
 * access, so the service can be exercised with null repositories here.
 */
class PostingServiceTest {

    private final PostingService service = new PostingService(null, null, null, null);

    private static JournalEntryCommand command(List<PostingLine> lines) {
        return new JournalEntryCommand("idem-1", "test entry", null, "tester", "TEST", lines);
    }

    @Test
    void rejectsUnbalancedEntry() {
        JournalEntryCommand cmd = command(List.of(
                new PostingLine(AccountRef.pool(), 100, Direction.CREDIT),
                new PostingLine(AccountRef.player("u1"), 90, Direction.DEBIT)));

        assertThatThrownBy(() -> service.post(cmd))
                .isInstanceOf(UnbalancedEntryException.class);
    }

    @Test
    void rejectsEntryWithFewerThanTwoPostings() {
        JournalEntryCommand cmd = command(List.of(
                new PostingLine(AccountRef.pool(), 100, Direction.CREDIT)));

        assertThatThrownBy(() -> service.post(cmd))
                .isInstanceOf(UnbalancedEntryException.class);
    }

    @Test
    void rejectsNonPositiveAmount() {
        JournalEntryCommand cmd = command(List.of(
                new PostingLine(AccountRef.pool(), 0, Direction.CREDIT),
                new PostingLine(AccountRef.player("u1"), 0, Direction.DEBIT)));

        assertThatThrownBy(() -> service.post(cmd))
                .isInstanceOf(UnbalancedEntryException.class);
    }

    @Test
    void acceptsBalancedInputDuringValidation() {
        // a balanced command passes validation; persistence is covered by LedgerIT
        JournalEntryCommand cmd = command(List.of(
                new PostingLine(AccountRef.player("u1"), 100, Direction.DEBIT),
                new PostingLine(AccountRef.pool(), 100, Direction.CREDIT)));

        // fails later with NPE on the null repositories, never with UnbalancedEntryException
        assertThatCode(() -> service.post(cmd))
                .isNotInstanceOf(UnbalancedEntryException.class);
    }
}
