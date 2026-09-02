package com.aashray.ingestion.controller;

import java.util.Collections;
import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.aashray.entity.DataSource;
import com.aashray.exception.ApiException;
import com.aashray.ingestion.model.IngestionFormat;
import com.aashray.ingestion.model.IngestionResult;
import com.aashray.ingestion.model.IngestionStatus;
import com.aashray.ingestion.model.IngestionTarget;
import com.aashray.ingestion.model.RasterMetadataDto;
import com.aashray.ingestion.service.IngestionService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/v1/ingestion")
@Tag(name = "Data Ingestion", description = "Endpoints for importing pilot spatial, tabular, structured JSON, and raster metadata")
public class IngestionController {

    private final IngestionService ingestionService;

    public IngestionController(IngestionService ingestionService) {
        this.ingestionService = ingestionService;
    }

    @PostMapping(value = "/csv", consumes = {MediaType.TEXT_PLAIN_VALUE, "text/csv", MediaType.APPLICATION_JSON_VALUE})
    @Operation(summary = "Import CSV data", description = "Ingest tabular pilot data in CSV format for a specific domain target")
    public ResponseEntity<IngestionResult> importCsv(
            @RequestBody String csvContent,
            @RequestParam(name = "target", required = false) String targetName) {
        IngestionTarget target = targetName != null ? IngestionTarget.fromString(targetName) : null;
        IngestionResult result = ingestionService.ingest(csvContent, IngestionFormat.CSV, target, Collections.emptyMap());
        return toResponse(result);
    }

    @PostMapping(value = "/geojson", consumes = {MediaType.APPLICATION_JSON_VALUE, MediaType.TEXT_PLAIN_VALUE})
    @Operation(summary = "Import GeoJSON data", description = "Ingest GeoJSON FeatureCollection or Features into PostGIS entities")
    public ResponseEntity<IngestionResult> importGeoJson(
            @RequestBody String geoJsonContent,
            @RequestParam(name = "target", required = false) String targetName) {
        IngestionTarget target = targetName != null ? IngestionTarget.fromString(targetName) : null;
        IngestionResult result = ingestionService.ingest(geoJsonContent, IngestionFormat.GEOJSON, target, Collections.emptyMap());
        return toResponse(result);
    }

    @PostMapping(value = "/json", consumes = {MediaType.APPLICATION_JSON_VALUE})
    @Operation(summary = "Import JSON data", description = "Ingest structured JSON records into domain models")
    public ResponseEntity<IngestionResult> importJson(
            @RequestBody String jsonContent,
            @RequestParam(name = "target", required = true) String targetName) {
        IngestionTarget target = IngestionTarget.fromString(targetName);
        if (target == null) {
            throw ApiException.validation("Invalid or missing target: " + targetName);
        }
        IngestionResult result = ingestionService.ingest(jsonContent, IngestionFormat.JSON, target, Collections.emptyMap());
        return toResponse(result);
    }

    @PostMapping(value = "/raster-metadata", consumes = {MediaType.APPLICATION_JSON_VALUE})
    @Operation(summary = "Register GeoTIFF/Raster metadata", description = "Register metadata for GeoTIFF or derived raster layers into DataSource")
    public ResponseEntity<DataSource> registerRasterMetadata(@Valid @RequestBody RasterMetadataDto dto) {
        DataSource dataSource = ingestionService.registerRasterMetadata(dto);
        return ResponseEntity.status(HttpStatus.CREATED).body(dataSource);
    }

    @PostMapping(value = "/upload", consumes = {MediaType.MULTIPART_FORM_DATA_VALUE})
    @Operation(summary = "Upload and ingest file", description = "Upload CSV or GeoJSON file for automated ingestion")
    public ResponseEntity<IngestionResult> uploadFile(
            @RequestParam("file") MultipartFile file,
            @RequestParam(name = "target", required = false) String targetName) {
        IngestionTarget target = targetName != null ? IngestionTarget.fromString(targetName) : null;
        IngestionResult result = ingestionService.ingestFile(file, target, Collections.emptyMap());
        return toResponse(result);
    }

    private ResponseEntity<IngestionResult> toResponse(IngestionResult result) {
        if (result.getStatus() == IngestionStatus.FAILED) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(result);
        }
        return ResponseEntity.ok(result);
    }
}
