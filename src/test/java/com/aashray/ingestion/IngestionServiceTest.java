package com.aashray.ingestion;

import java.util.Collections;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.aashray.exception.ApiException;
import com.aashray.ingestion.config.IngestionProperties;
import com.aashray.ingestion.importer.CsvDataImporter;
import com.aashray.ingestion.importer.GeoJsonDataImporter;
import com.aashray.ingestion.importer.JsonDataImporter;
import com.aashray.ingestion.importer.RasterMetadataImporter;
import com.aashray.ingestion.model.IngestionFormat;
import com.aashray.ingestion.model.IngestionResult;
import com.aashray.ingestion.model.IngestionTarget;
import com.aashray.ingestion.service.IngestionService;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class IngestionServiceTest {

    @Mock
    private CsvDataImporter csvDataImporter;
    @Mock
    private GeoJsonDataImporter geoJsonDataImporter;
    @Mock
    private JsonDataImporter jsonDataImporter;
    @Mock
    private RasterMetadataImporter rasterMetadataImporter;

    private IngestionService ingestionService;

    @BeforeEach
    void setUp() {
        IngestionProperties properties = new IngestionProperties();
        ingestionService = new IngestionService(
                List.of(csvDataImporter, geoJsonDataImporter, jsonDataImporter, rasterMetadataImporter),
                rasterMetadataImporter,
                properties
        );
    }

    @Test
    @DisplayName("Should route CSV content to CsvDataImporter")
    void testRouteToCsvImporter() {
        String csv = "name,lgd_code\nVillage1,LGD01\n";
        when(csvDataImporter.supports(IngestionFormat.CSV, IngestionTarget.HABITATION)).thenReturn(true);
        when(csvDataImporter.importData(eq(csv), eq(IngestionTarget.HABITATION), any()))
                .thenReturn(IngestionResult.success(IngestionTarget.HABITATION, IngestionFormat.CSV, 1, List.of()));

        IngestionResult result = ingestionService.ingest(csv, IngestionFormat.CSV, IngestionTarget.HABITATION, Collections.emptyMap());

        assertThat(result).isNotNull();
        assertThat(result.getImportedCount()).isEqualTo(1);
    }

    @Test
    @DisplayName("Should auto-detect GeoJSON format and route accordingly")
    void testAutoDetectGeoJson() {
        String geojson = "{\"type\": \"FeatureCollection\", \"features\": []}";
        when(geoJsonDataImporter.supports(IngestionFormat.GEOJSON, IngestionTarget.HABITATION)).thenReturn(true);
        when(geoJsonDataImporter.importData(eq(geojson), eq(IngestionTarget.HABITATION), any()))
                .thenReturn(IngestionResult.success(IngestionTarget.HABITATION, IngestionFormat.GEOJSON, 0, List.of()));

        IngestionResult result = ingestionService.ingest(geojson, null, IngestionTarget.HABITATION, Collections.emptyMap());

        assertThat(result).isNotNull();
    }

    @Test
    @DisplayName("Should reject empty content with ApiException")
    void testRejectEmptyContent() {
        assertThatThrownBy(() -> ingestionService.ingest("", IngestionFormat.CSV, IngestionTarget.HABITATION, Collections.emptyMap()))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("must not be empty");
    }
}
