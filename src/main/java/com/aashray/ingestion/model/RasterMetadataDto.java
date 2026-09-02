package com.aashray.ingestion.model;

import java.time.OffsetDateTime;

import jakarta.validation.constraints.NotBlank;

public class RasterMetadataDto {

    @NotBlank(message = "provider is required")
    private String provider;

    @NotBlank(message = "dataset is required")
    private String dataset;

    private String sourceType = "RASTER_GEOTIFF";
    private String coverage;
    private String resolution;
    private String url;
    private String crs = "EPSG:4326";
    private String license;
    private OffsetDateTime fetchTime;
    private OffsetDateTime effectiveTime;
    private String freshnessClass;
    private String notes;

    public String getProvider() {
        return provider;
    }

    public void setProvider(String provider) {
        this.provider = provider;
    }

    public String getDataset() {
        return dataset;
    }

    public void setDataset(String dataset) {
        this.dataset = dataset;
    }

    public String getSourceType() {
        return sourceType;
    }

    public void setSourceType(String sourceType) {
        this.sourceType = sourceType;
    }

    public String getCoverage() {
        return coverage;
    }

    public void setCoverage(String coverage) {
        this.coverage = coverage;
    }

    public String getResolution() {
        return resolution;
    }

    public void setResolution(String resolution) {
        this.resolution = resolution;
    }

    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public String getCrs() {
        return crs;
    }

    public void setCrs(String crs) {
        this.crs = crs;
    }

    public String getLicense() {
        return license;
    }

    public void setLicense(String license) {
        this.license = license;
    }

    public OffsetDateTime getFetchTime() {
        return fetchTime;
    }

    public void setFetchTime(OffsetDateTime fetchTime) {
        this.fetchTime = fetchTime;
    }

    public OffsetDateTime getEffectiveTime() {
        return effectiveTime;
    }

    public void setEffectiveTime(OffsetDateTime effectiveTime) {
        this.effectiveTime = effectiveTime;
    }

    public String getFreshnessClass() {
        return freshnessClass;
    }

    public void setFreshnessClass(String freshnessClass) {
        this.freshnessClass = freshnessClass;
    }

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }
}
