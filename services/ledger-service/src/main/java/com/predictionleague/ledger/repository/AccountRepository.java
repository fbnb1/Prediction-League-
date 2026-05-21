package com.predictionleague.ledger.repository;

import com.predictionleague.ledger.domain.Account;
import com.predictionleague.ledger.domain.OwnerType;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AccountRepository extends JpaRepository<Account, Long> {

    Optional<Account> findByOwnerTypeAndOwnerId(OwnerType ownerType, String ownerId);
}
