package com.aashray.ingestion.model;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class IngestionResult {

    private IngestionStatus status;
    private IngestionTarget target;
    private IngestionFormat format;
    private int totalRecords;
    private int importedCount;
    private int failedCount;
    private String message;
    private List<IngestionError> errors = new ArrayList<>();
    private List<UUID> importedIds = new ArrayList<>();

    public IngestionResult() {
    }

    public IngestionResult(IngestionStatus status, IngestionTarget target, IngestionFormat format,
                           int totalRecords, int importedCount, int failedCount, String message) {
        this.status = status;
        this.target = target;
        this.format = format;
        this.totalRecords = totalRecords;
        this.importedCount = importedCount;
        this.failedCount = failedCount;
        this.message = message;
    }

    public static IngestionResult success(IngestionTarget target, IngestionFormat format, int importedCount, List<UUID> ids) {
        IngestionResult result = new IngestionResult(IngestionStatus.SUCCESS, target, format, importedCount, importedCount, 0,
                "Successfully imported " + importedCount + " " + (target != null ? target.name() : "data") + " records.");
        if (ids != null) {
            result.setImportedIds(ids);
        }
        return result;
    }

    public static IngestionResult failed(IngestionTarget target, IngestionFormat format, String message, List<IngestionError> errors) {
        IngestionResult result = new IngestionResult(IngestionStatus.FAILED, target, format,
                errors != null ? errors.size() : 0, 0, errors != null ? errors.size() : 0, message);
        if (errors != null) {
            result.setErrors(errors);
        }
        return result;
    }

    public IngestionStatus getStatus() {
        return status;
    }

    public void setStatus(IngestionStatus status) {
        this.status = status;
    }

    public IngestionTarget getTarget() {
        return target;
    }

    public void setTarget(IngestionTarget target) {
        this.target = target;
    }

    public IngestionFormat getFormat() {
        return format;
    }

    public void setFormat(IngestionFormat format) {
        this.format = format;
    }

    public int getTotalRecords() {
        return totalRecords;
    }

    public void setTotalRecords(int totalRecords) {
        this.totalRecords = totalRecords;
    }

    public int getImportedCount() {
        return importedCount;
    }

    public void setImportedCount(int importedCount) {
        this.importedCount = importedCount;
    }

    public int getFailedCount() {
        return failedCount;
    }

    public void setFailedCount(int failedCount) {
        this.failedCount = failedCount;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public List<IngestionError> getErrors() {
        return errors;
    }

    public void setErrors(List<IngestionError> errors) {
        this.errors = errors != null ? errors : new ArrayList<>();
    }

    public void addError(IngestionError error) {
        this.errors.add(error);
    }

    public List<UUID> getImportedIds() {
        return importedIds;
    }

    public void setImportedIds(List<UUID> importedIds) {
        this.importedIds = importedIds != null ? importedIds : new ArrayList<>();
    }

    public void addImportedId(UUID id) {
        this.importedIds.add(id);
    }
}
