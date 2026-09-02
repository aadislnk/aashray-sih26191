package com.aashray.entity;

import java.time.OffsetDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;

@Entity
@Table(name = "data_source")
public class DataSource extends BaseUuidEntity {

    @Column(nullable = false)
    private String provider;

    @Column(nullable = false)
    private String dataset;

    @Column
    private String license;

    @Column(name = "fetch_time")
    private OffsetDateTime fetchTime;

    @Column(name = "freshness_class")
    private String freshnessClass;

    @Column(name = "source_type")
    private String sourceType;

    @Column(name = "effective_time")
    private OffsetDateTime effectiveTime;

    @Column
    private String coverage;

    @Column
    private String resolution;

    @Column
    private String url;

    @Column
    private String crs;

    @Column
    private String notes;

    // Getters and setters
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

    public String getFreshnessClass() {
        return freshnessClass;
    }

    public void setFreshnessClass(String freshnessClass) {
        this.freshnessClass = freshnessClass;
    }

    public String getSourceType() {
        return sourceType;
    }

    public void setSourceType(String sourceType) {
        this.sourceType = sourceType;
    }

    public OffsetDateTime getEffectiveTime() {
        return effectiveTime;
    }

    public void setEffectiveTime(OffsetDateTime effectiveTime) {
        this.effectiveTime = effectiveTime;
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

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }
}
