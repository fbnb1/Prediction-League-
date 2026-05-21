package com.predictionleague.ledger.repository;

import com.predictionleague.ledger.domain.Account;
import com.predictionleague.ledger.domain.OwnerType;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AccountRepository extends JpaRepository<Account, Long> {

    Optional<Account> findByOwnerTypeAndOwnerId(OwnerType ownerType, String ownerId);

    /** Player accounts whose owner id ends with {@code :groupId} -- all members. */
    List<Account> findByOwnerTypeAndOwnerIdEndingWith(OwnerType ownerType, String suffix);
}
