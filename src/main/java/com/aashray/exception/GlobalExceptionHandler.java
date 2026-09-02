package com.aashray.exception;

import java.util.Map;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ErrorResponse> handleApiException(ApiException exception) {
        HttpStatus status = mapStatus(exception.getCode());
        ErrorResponse body = new ErrorResponse(exception.getCode(), exception.getMessage(), Map.of());
        return ResponseEntity.status(status).body(body);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleMethodArgumentNotValid(MethodArgumentNotValidException exception) {
        Map<String, Object> details = exception.getBindingResult().getFieldErrors().stream()
            .collect(java.util.stream.Collectors.toMap(
                FieldError::getField,
                FieldError::getDefaultMessage,
                (first, second) -> first
            ));
        ErrorResponse body = new ErrorResponse("VALIDATION_ERROR", "Request validation failed", details);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(body);
    }

    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<ErrorResponse> handleDataIntegrityViolation(DataIntegrityViolationException exception) {
        ErrorResponse body = new ErrorResponse("CONFLICT", "Database constraint violation", Map.of());
        return ResponseEntity.status(HttpStatus.CONFLICT).body(body);
    }

    private HttpStatus mapStatus(String code) {
        if ("RESOURCE_NOT_FOUND".equals(code)) {
            return HttpStatus.NOT_FOUND;
        }
        if ("VALIDATION_ERROR".equals(code)) {
            return HttpStatus.BAD_REQUEST;
        }
        if ("CONFLICT".equals(code)) {
            return HttpStatus.CONFLICT;
        }
        if ("INTERNAL_ERROR".equals(code)) {
            return HttpStatus.INTERNAL_SERVER_ERROR;
        }
        return HttpStatus.INTERNAL_SERVER_ERROR;
    }
}
