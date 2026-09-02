package com.aashray.ingestion.model;

public record IngestionError(
    Integer rowIndex,
    String identifier,
    String field,
    String message,
    Object rejectedValue
) {
    public static IngestionError row(int rowIndex, String field, String message, Object rejectedValue) {
        return new IngestionError(rowIndex, null, field, message, rejectedValue);
    }

    public static IngestionError general(String message) {
        return new IngestionError(null, null, null, message, null);
    }

    public static IngestionError record(String identifier, String field, String message, Object rejectedValue) {
        return new IngestionError(null, identifier, field, message, rejectedValue);
    }
}
