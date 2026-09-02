package com.aashray.ingestion.importer;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import com.aashray.entity.DataSource;
import com.aashray.ingestion.model.IngestionError;
import com.aashray.ingestion.model.IngestionFormat;
import com.aashray.ingestion.model.IngestionResult;
import com.aashray.ingestion.model.IngestionStatus;
import com.aashray.ingestion.model.IngestionTarget;
import com.aashray.ingestion.model.RasterMetadataDto;
import com.aashray.ingestion.validator.IngestionValidator;
import com.aashray.repository.DataSourceRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@Component
public class RasterMetadataImporter implements DataImporter {

    private final DataSourceRepository dataSourceRepository;
    private final IngestionValidator validator;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public RasterMetadataImporter(DataSourceRepository dataSourceRepository, IngestionValidator validator) {
        this.dataSourceRepository = dataSourceRepository;
        this.validator = validator;
    }

    @Override
    public boolean supports(IngestionFormat format, IngestionTarget target) {
        return format == IngestionFormat.RASTER_METADATA ||
                (target == IngestionTarget.DATA_SOURCE && (format == IngestionFormat.JSON || format == IngestionFormat.CSV));
    }

    @Override
    @Transactional
    public IngestionResult importData(String content, IngestionTarget target, Map<String, Object> options) {
        if (content == null || content.isBlank()) {
            return IngestionResult.failed(IngestionTarget.DATA_SOURCE, IngestionFormat.RASTER_METADATA,
                    "Payload must not be empty", List.of(IngestionError.general("Empty content")));
        }

        try {
            JsonNode root = objectMapper.readTree(content);
            List<JsonNode> items = new ArrayList<>();
            if (root.isArray()) {
                root.forEach(items::add);
            } else {
                items.add(root);
            }

            List<IngestionError> errors = new ArrayList<>();
            List<UUID> savedIds = new ArrayList<>();

            for (int i = 0; i < items.size(); i++) {
                int rowNumber = i + 1;
                JsonNode node = items.get(i);

                String provider = node.hasNonNull("provider") ? node.get("provider").asText().trim() : null;
                String dataset = node.hasNonNull("dataset") ? node.get("dataset").asText().trim() : null;

                if (provider == null || provider.isBlank()) {
                    errors.add(IngestionError.row(rowNumber, "provider", "provider is required", null));
                    continue;
                }
                if (dataset == null || dataset.isBlank()) {
                    errors.add(IngestionError.row(rowNumber, "dataset", "dataset is required", null));
                    continue;
                }

                String crs = node.hasNonNull("crs") ? node.get("crs").asText().trim() : "EPSG:4326";
                errors.addAll(validator.validateCrs(crs, rowNumber));
                if (!errors.isEmpty()) {
                    continue;
                }

                String sourceType = node.hasNonNull("sourceType") ? node.get("sourceType").asText().trim()
                        : (node.hasNonNull("source_type") ? node.get("source_type").asText().trim() : "RASTER_GEOTIFF");
                String coverage = node.hasNonNull("coverage") ? node.get("coverage").asText().trim() : null;
                String resolution = node.hasNonNull("resolution") ? node.get("resolution").asText().trim() : null;
                String url = node.hasNonNull("url") ? node.get("url").asText().trim() : null;
                String license = node.hasNonNull("license") ? node.get("license").asText().trim() : null;
                String freshnessClass = node.hasNonNull("freshnessClass") ? node.get("freshnessClass").asText().trim()
                        : (node.hasNonNull("freshness_class") ? node.get("freshness_class").asText().trim() : null);
                String notes = node.hasNonNull("notes") ? node.get("notes").asText().trim() : null;

                OffsetDateTime fetchTime = null;
                if (node.hasNonNull("fetchTime") || node.hasNonNull("fetch_time")) {
                    String timeStr = node.hasNonNull("fetchTime") ? node.get("fetchTime").asText() : node.get("fetch_time").asText();
                    try {
                        fetchTime = OffsetDateTime.parse(timeStr);
                    } catch (Exception e) {
                        errors.add(IngestionError.row(rowNumber, "fetchTime", "Invalid ISO-8601 timestamp: " + timeStr, timeStr));
                        continue;
                    }
                }

                OffsetDateTime effectiveTime = null;
                if (node.hasNonNull("effectiveTime") || node.hasNonNull("effective_time")) {
                    String timeStr = node.hasNonNull("effectiveTime") ? node.get("effectiveTime").asText() : node.get("effective_time").asText();
                    try {
                        effectiveTime = OffsetDateTime.parse(timeStr);
                    } catch (Exception e) {
                        errors.add(IngestionError.row(rowNumber, "effectiveTime", "Invalid ISO-8601 timestamp: " + timeStr, timeStr));
                        continue;
                    }
                }

                Optional<DataSource> existing = dataSourceRepository.findByProviderAndDataset(provider, dataset);
                DataSource ds = existing.orElseGet(DataSource::new);
                ds.setProvider(provider);
                ds.setDataset(dataset);
                ds.setSourceType(sourceType);
                ds.setCoverage(coverage);
                ds.setResolution(resolution);
                ds.setUrl(url);
                ds.setCrs(crs);
                ds.setLicense(license);
                ds.setFetchTime(fetchTime != null ? fetchTime : OffsetDateTime.now());
                ds.setEffectiveTime(effectiveTime);
                ds.setFreshnessClass(freshnessClass);
                ds.setNotes(notes);

                ds = dataSourceRepository.save(ds);
                savedIds.add(ds.getId());
            }

            if (!errors.isEmpty()) {
                IngestionResult result = IngestionResult.failed(IngestionTarget.DATA_SOURCE, IngestionFormat.RASTER_METADATA,
                        "Validation failed for raster metadata import", errors);
                result.setImportedIds(savedIds);
                result.setTotalRecords(items.size());
                result.setImportedCount(savedIds.size());
                result.setFailedCount(errors.size());
                if (!savedIds.isEmpty()) {
                    result.setStatus(IngestionStatus.PARTIAL_SUCCESS);
                }
                return result;
            }

            return IngestionResult.success(IngestionTarget.DATA_SOURCE, IngestionFormat.RASTER_METADATA, savedIds.size(), savedIds);

        } catch (Exception e) {
            return IngestionResult.failed(IngestionTarget.DATA_SOURCE, IngestionFormat.RASTER_METADATA,
                    "Failed to parse raster metadata JSON: " + e.getMessage(),
                    List.of(IngestionError.general(e.getMessage())));
        }
    }

    @Transactional
    public DataSource registerMetadata(RasterMetadataDto dto) {
        if (dto.getProvider() == null || dto.getProvider().isBlank()) {
            throw new IllegalArgumentException("provider is required");
        }
        if (dto.getDataset() == null || dto.getDataset().isBlank()) {
            throw new IllegalArgumentException("dataset is required");
        }

        Optional<DataSource> existing = dataSourceRepository.findByProviderAndDataset(dto.getProvider(), dto.getDataset());
        DataSource ds = existing.orElseGet(DataSource::new);
        ds.setProvider(dto.getProvider());
        ds.setDataset(dto.getDataset());
        ds.setSourceType(dto.getSourceType() != null ? dto.getSourceType() : "RASTER_GEOTIFF");
        ds.setCoverage(dto.getCoverage());
        ds.setResolution(dto.getResolution());
        ds.setUrl(dto.getUrl());
        ds.setCrs(dto.getCrs() != null ? dto.getCrs() : "EPSG:4326");
        ds.setLicense(dto.getLicense());
        ds.setFetchTime(dto.getFetchTime() != null ? dto.getFetchTime() : OffsetDateTime.now());
        ds.setEffectiveTime(dto.getEffectiveTime());
        ds.setFreshnessClass(dto.getFreshnessClass());
        ds.setNotes(dto.getNotes());

        return dataSourceRepository.save(ds);
    }
}
