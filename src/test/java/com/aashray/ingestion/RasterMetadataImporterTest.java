package com.aashray.ingestion;

import java.util.Collections;
import java.util.Optional;
import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.aashray.entity.DataSource;
import com.aashray.ingestion.importer.RasterMetadataImporter;
import com.aashray.ingestion.model.IngestionFormat;
import com.aashray.ingestion.model.IngestionResult;
import com.aashray.ingestion.model.IngestionStatus;
import com.aashray.ingestion.model.IngestionTarget;
import com.aashray.ingestion.model.RasterMetadataDto;
import com.aashray.ingestion.validator.IngestionValidator;
import com.aashray.repository.DataSourceRepository;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class RasterMetadataImporterTest {

    @Mock
    private DataSourceRepository dataSourceRepository;

    private IngestionValidator validator;
    private RasterMetadataImporter rasterMetadataImporter;

    @BeforeEach
    void setUp() {
        validator = new IngestionValidator();
        rasterMetadataImporter = new RasterMetadataImporter(dataSourceRepository, validator);
    }

    @Test
    @DisplayName("Should successfully register raster metadata via DTO")
    void testRegisterMetadataDto() {
        RasterMetadataDto dto = new RasterMetadataDto();
        dto.setProvider("Sentinel-2");
        dto.setDataset("Flood_Inundation_2026");
        dto.setCrs("EPSG:4326");
        dto.setResolution("10m");
        dto.setCoverage("BBOX(77.0, 12.0, 78.0, 13.0)");
        dto.setUrl("s3://aashray-rasters/flood_2026.tif");

        when(dataSourceRepository.findByProviderAndDataset("Sentinel-2", "Flood_Inundation_2026"))
                .thenReturn(Optional.empty());
        when(dataSourceRepository.save(any(DataSource.class))).thenAnswer(inv -> {
            DataSource ds = inv.getArgument(0);
            ds.setId(UUID.randomUUID());
            return ds;
        });

        DataSource result = rasterMetadataImporter.registerMetadata(dto);

        assertThat(result).isNotNull();
        assertThat(result.getProvider()).isEqualTo("Sentinel-2");
        assertThat(result.getDataset()).isEqualTo("Flood_Inundation_2026");
        assertThat(result.getResolution()).isEqualTo("10m");
        assertThat(result.getSourceType()).isEqualTo("RASTER_GEOTIFF");
    }

    @Test
    @DisplayName("Should import raster metadata JSON payload")
    void testImportRasterMetadataJson() {
        String json = """
                [
                  {
                    "provider": "SRTM",
                    "dataset": "DEM_30M",
                    "sourceType": "RASTER_GEOTIFF",
                    "resolution": "30m",
                    "coverage": "WGS84_BOUNDS",
                    "crs": "EPSG:4326"
                  }
                ]
                """;

        when(dataSourceRepository.findByProviderAndDataset("SRTM", "DEM_30M"))
                .thenReturn(Optional.empty());
        when(dataSourceRepository.save(any(DataSource.class))).thenAnswer(inv -> {
            DataSource ds = inv.getArgument(0);
            ds.setId(UUID.randomUUID());
            return ds;
        });

        IngestionResult result = rasterMetadataImporter.importData(json, IngestionTarget.DATA_SOURCE, Collections.emptyMap());

        assertThat(result.getStatus()).isEqualTo(IngestionStatus.SUCCESS);
        assertThat(result.getImportedCount()).isEqualTo(1);
    }
}
