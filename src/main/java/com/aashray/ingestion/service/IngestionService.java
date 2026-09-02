package com.aashray.ingestion.service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import com.aashray.entity.DataSource;
import com.aashray.exception.ApiException;
import com.aashray.ingestion.config.IngestionProperties;
import com.aashray.ingestion.importer.DataImporter;
import com.aashray.ingestion.importer.RasterMetadataImporter;
import com.aashray.ingestion.model.IngestionError;
import com.aashray.ingestion.model.IngestionFormat;
import com.aashray.ingestion.model.IngestionResult;
import com.aashray.ingestion.model.IngestionTarget;
import com.aashray.ingestion.model.RasterMetadataDto;

@Service
public class IngestionService {

    private final List<DataImporter> importers;
    private final RasterMetadataImporter rasterMetadataImporter;
    private final IngestionProperties properties;

    public IngestionService(List<DataImporter> importers,
                            RasterMetadataImporter rasterMetadataImporter,
                            IngestionProperties properties) {
        this.importers = importers;
        this.rasterMetadataImporter = rasterMetadataImporter;
        this.properties = properties;
    }

    @Transactional
    public IngestionResult ingest(String content, IngestionFormat format, IngestionTarget target, Map<String, Object> options) {
        if (content == null || content.isBlank()) {
            throw ApiException.validation("Content to ingest must not be empty");
        }

        IngestionFormat resolvedFormat = format != null ? format : detectFormat(content);
        if (resolvedFormat == null) {
            throw ApiException.validation("Unable to determine ingestion format for payload");
        }

        DataImporter importer = findImporter(resolvedFormat, target);
        if (importer == null) {
            throw ApiException.validation("No suitable importer found for format " + resolvedFormat
                    + " and target " + (target != null ? target.name() : "AUTO"));
        }

        return importer.importData(content, target, options);
    }

    @Transactional
    public IngestionResult ingestFile(MultipartFile file, IngestionTarget target, Map<String, Object> options) {
        if (file == null || file.isEmpty()) {
            throw ApiException.validation("Uploaded file is empty");
        }

        String filename = file.getOriginalFilename();
        IngestionFormat format = IngestionFormat.fromFilename(filename);

        String content;
        try {
            content = new String(file.getBytes(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw ApiException.internal("Failed to read uploaded file: " + e.getMessage());
        }

        return ingest(content, format, target, options);
    }

    @Transactional
    public DataSource registerRasterMetadata(RasterMetadataDto dto) {
        return rasterMetadataImporter.registerMetadata(dto);
    }

    private DataImporter findImporter(IngestionFormat format, IngestionTarget target) {
        for (DataImporter importer : importers) {
            if (importer.supports(format, target)) {
                return importer;
            }
        }
        return null;
    }

    private IngestionFormat detectFormat(String content) {
        String trimmed = content.trim();
        if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
            if (trimmed.contains("\"FeatureCollection\"") || trimmed.contains("\"Feature\"") || trimmed.contains("\"geometry\"")) {
                return IngestionFormat.GEOJSON;
            }
            return IngestionFormat.JSON;
        }
        if (trimmed.contains(",") && trimmed.contains("\n")) {
            return IngestionFormat.CSV;
        }
        return null;
    }
}
