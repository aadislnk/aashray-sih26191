package com.aashray.ingestion;

import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.aashray.entity.AdminBoundary;
import com.aashray.entity.Habitation;
import com.aashray.entity.RelocationSite;
import com.aashray.ingestion.importer.GeoJsonDataImporter;
import com.aashray.ingestion.model.IngestionResult;
import com.aashray.ingestion.model.IngestionStatus;
import com.aashray.ingestion.model.IngestionTarget;
import com.aashray.ingestion.validator.IngestionValidator;
import com.aashray.repository.AdminBoundaryRepository;
import com.aashray.repository.DataSourceRepository;
import com.aashray.repository.HabitationRepository;
import com.aashray.repository.InfrastructureRepository;
import com.aashray.repository.RelocationSiteRepository;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class GeoJsonDataImporterTest {

    @Mock
    private HabitationRepository habitationRepository;
    @Mock
    private AdminBoundaryRepository adminBoundaryRepository;
    @Mock
    private RelocationSiteRepository relocationSiteRepository;
    @Mock
    private InfrastructureRepository infrastructureRepository;
    @Mock
    private DataSourceRepository dataSourceRepository;

    private IngestionValidator validator;
    private GeoJsonDataImporter geoJsonDataImporter;

    @BeforeEach
    void setUp() {
        validator = new IngestionValidator();
        geoJsonDataImporter = new GeoJsonDataImporter(
                habitationRepository,
                adminBoundaryRepository,
                relocationSiteRepository,
                infrastructureRepository,
                dataSourceRepository,
                validator
        );
    }

    @Test
    @DisplayName("Should import valid GeoJSON FeatureCollection into Habitations")
    void testValidGeoJsonFeatureCollection() {
        String geojson = """
                {
                  "type": "FeatureCollection",
                  "features": [
                    {
                      "type": "Feature",
                      "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                          [[77.5, 12.9], [77.6, 12.9], [77.6, 13.0], [77.5, 13.0], [77.5, 12.9]]
                        ]
                      },
                      "properties": {
                        "name": "Geo Village 1",
                        "lgd_code": "GEO_001"
                      }
                    }
                  ]
                }
                """;

        when(habitationRepository.findByLgdCode(any())).thenReturn(Optional.empty());
        when(habitationRepository.findByName(any())).thenReturn(Optional.empty());
        when(adminBoundaryRepository.findByName(any())).thenReturn(Optional.of(new AdminBoundary()));
        when(habitationRepository.save(any(Habitation.class))).thenAnswer(inv -> {
            Habitation h = inv.getArgument(0);
            h.setId(UUID.randomUUID());
            return h;
        });

        IngestionResult result = geoJsonDataImporter.importData(geojson, IngestionTarget.HABITATION, Collections.emptyMap());

        assertThat(result.getStatus()).isEqualTo(IngestionStatus.SUCCESS);
        assertThat(result.getImportedCount()).isEqualTo(1);
        assertThat(result.getImportedIds()).hasSize(1);
    }

    @Test
    @DisplayName("Should reject GeoJSON with unsupported CRS")
    void testUnsupportedCrs() {
        String geojson = """
                {
                  "type": "FeatureCollection",
                  "crs": {
                    "type": "name",
                    "properties": {
                      "name": "EPSG:3857"
                    }
                  },
                  "features": []
                }
                """;

        IngestionResult result = geoJsonDataImporter.importData(geojson, IngestionTarget.HABITATION, Collections.emptyMap());

        assertThat(result.getStatus()).isEqualTo(IngestionStatus.FAILED);
        assertThat(result.getMessage()).contains("Unsupported CRS");
    }

    @Test
    @DisplayName("Should reject GeoJSON with invalid coordinate bounds")
    void testInvalidCoordinatesInGeoJson() {
        String geojson = """
                {
                  "type": "FeatureCollection",
                  "features": [
                    {
                      "type": "Feature",
                      "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                          [[200.0, 12.9], [200.1, 12.9], [200.1, 13.0], [200.0, 13.0], [200.0, 12.9]]
                        ]
                      },
                      "properties": {
                        "name": "Out of bounds Village"
                      }
                    }
                  ]
                }
                """;

        IngestionResult result = geoJsonDataImporter.importData(geojson, IngestionTarget.HABITATION, Collections.emptyMap());

        assertThat(result.getStatus()).isEqualTo(IngestionStatus.FAILED);
        assertThat(result.getErrors()).anyMatch(e -> "longitude".equals(e.field()));
    }

    @Test
    @DisplayName("Should reject self-intersecting polygon geometry in GeoJSON")
    void testInvalidGeometryTopology() {
        String geojson = """
                {
                  "type": "FeatureCollection",
                  "features": [
                    {
                      "type": "Feature",
                      "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                          [[77.0, 12.0], [77.0, 12.2], [77.2, 12.0], [77.2, 12.2], [77.0, 12.0]]
                        ]
                      },
                      "properties": {
                        "name": "Self Intersecting Village"
                      }
                    }
                  ]
                }
                """;

        IngestionResult result = geoJsonDataImporter.importData(geojson, IngestionTarget.HABITATION, Collections.emptyMap());

        assertThat(result.getStatus()).isEqualTo(IngestionStatus.FAILED);
        assertThat(result.getErrors()).anyMatch(e -> e.message().contains("Geometry is invalid") || e.message().contains("Self-intersection"));
    }
}
