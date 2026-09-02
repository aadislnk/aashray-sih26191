package com.aashray.exception;

public class ApiException extends RuntimeException {

    private final String code;
    private final String message;

    public ApiException(String code, String message) {
        super(message);
        this.code = code;
        this.message = message;
    }

    public String getCode() {
        return code;
    }

    @Override
    public String getMessage() {
        return message;
    }

    public static ApiException notFound(String message) {
        return new ApiException("RESOURCE_NOT_FOUND", message);
    }

    public static ApiException validation(String message) {
        return new ApiException("VALIDATION_ERROR", message);
    }

    public static ApiException conflict(String message) {
        return new ApiException("CONFLICT", message);
    }

    public static ApiException internal(String message) {
        return new ApiException("INTERNAL_ERROR", message);
    }
}
