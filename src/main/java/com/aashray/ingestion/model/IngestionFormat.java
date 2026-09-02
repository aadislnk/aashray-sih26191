package com.aashray.ingestion.model;

public enum IngestionFormat {
    CSV,
    GEOJSON,
    JSON,
    RASTER_METADATA;

    public static IngestionFormat fromFilename(String filename) {
        if (filename == null) {
            return null;
        }
        String lower = filename.toLowerCase();
        if (lower.endsWith(".csv")) {
            return CSV;
        } else if (lower.endsWith(".geojson") || lower.endsWith(".json")) {
            return GEOJSON; // Can be GEOJSON or JSON; default to GEOJSON if geospatial extension or detect inside
        } else if (lower.endsWith(".tif") || lower.endsWith(".tiff")) {
            return RASTER_METADATA;
        }
        return null;
    }
}
