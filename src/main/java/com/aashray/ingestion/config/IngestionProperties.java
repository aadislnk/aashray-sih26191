package com.aashray.ingestion.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "aashray.ingestion")
public class IngestionProperties {

    private int defaultSrid = 4326;
    private int maxBatchSize = 1000;
    private String importDir = "data/imports";
    private boolean strictValidation = true;

    public int getDefaultSrid() {
        return defaultSrid;
    }

    public void setDefaultSrid(int defaultSrid) {
        this.defaultSrid = defaultSrid;
    }

    public int getMaxBatchSize() {
        return maxBatchSize;
    }

    public void setMaxBatchSize(int maxBatchSize) {
        this.maxBatchSize = maxBatchSize;
    }

    public String getImportDir() {
        return importDir;
    }

    public void setImportDir(String importDir) {
        this.importDir = importDir;
    }

    public boolean isStrictValidation() {
        return strictValidation;
    }

    public void setStrictValidation(boolean strictValidation) {
        this.strictValidation = strictValidation;
    }
}
