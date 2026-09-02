package com.aashray.ingestion.model;

public enum IngestionTarget {
    ADMIN_BOUNDARY,
    HABITATION,
    INFRASTRUCTURE,
    POPULATION,
    RELOCATION_SITE,
    DATA_SOURCE,
    VULNERABILITY,
    HAZARD_ASSESSMENT,
    RISK_ASSESSMENT,
    CARRYING_CAPACITY,
    MODEL_VERSION;

    public static IngestionTarget fromString(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        String normalized = value.trim().toUpperCase().replace("-", "_");
        for (IngestionTarget target : values()) {
            if (target.name().equals(normalized)) {
                return target;
            }
        }
        return null;
    }
}
