package com.predictionleague.ledger.api;

import com.predictionleague.ledger.service.DuplicateIdempotencyKeyException;
import com.predictionleague.ledger.service.LedgerNotFoundException;
import com.predictionleague.ledger.service.UnbalancedEntryException;
import java.util.stream.Collectors;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(UnbalancedEntryException.class)
    @ResponseStatus(HttpStatus.UNPROCESSABLE_ENTITY)
    public ErrorResponse unbalanced(UnbalancedEntryException ex) {
        return new ErrorResponse("unbalanced_entry", ex.getMessage());
    }

    @ExceptionHandler(DuplicateIdempotencyKeyException.class)
    @ResponseStatus(HttpStatus.CONFLICT)
    public ErrorResponse duplicate(DuplicateIdempotencyKeyException ex) {
        return new ErrorResponse("duplicate_idempotency_key", ex.getMessage());
    }

    @ExceptionHandler(LedgerNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse notFound(LedgerNotFoundException ex) {
        return new ErrorResponse("not_found", ex.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse invalid(MethodArgumentNotValidException ex) {
        String detail = ex.getBindingResult().getFieldErrors().stream()
                .map(fieldError -> fieldError.getField() + " " + fieldError.getDefaultMessage())
                .collect(Collectors.joining("; "));
        return new ErrorResponse("validation_failed", detail);
    }

    public record ErrorResponse(String error, String message) {
    }
}
