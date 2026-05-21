package com.predictionleague.ledger.repository;

import com.predictionleague.ledger.domain.Posting;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface PostingRepository extends JpaRepository<Posting, Long> {

    List<Posting> findByAccountIdOrderByIdAsc(Long accountId);

    List<Posting> findByJournalEntryIdOrderByIdAsc(Long journalEntryId);

    /**
     * Balance of an account, computed from its postings -- never stored.
     * Convention: credits add, debits subtract.
     */
    @Query("""
            SELECT COALESCE(SUM(
                CASE WHEN p.direction = com.predictionleague.ledger.domain.Direction.CREDIT
                     THEN p.amountMinor ELSE -p.amountMinor END), 0)
            FROM Posting p
            WHERE p.accountId = :accountId
            """)
    long balanceOf(@Param("accountId") Long accountId);
}
