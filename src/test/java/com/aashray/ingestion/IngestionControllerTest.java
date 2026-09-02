package com.aashray.ingestion;

import java.util.List;
import java.util.UUID;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import com.aashray.config.SecurityConfig;
import com.aashray.entity.DataSource;
import com.aashray.ingestion.controller.IngestionController;
import com.aashray.ingestion.model.IngestionError;
import com.aashray.ingestion.model.IngestionFormat;
import com.aashray.ingestion.model.IngestionResult;
import com.aashray.ingestion.model.IngestionTarget;
import com.aashray.ingestion.model.RasterMetadataDto;
import com.aashray.ingestion.service.IngestionService;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(IngestionController.class)
@Import(SecurityConfig.class)
class IngestionControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private IngestionService ingestionService;

    @Test
    @DisplayName("POST /api/v1/ingestion/csv - should return 200 on successful CSV import")
    void testImportCsvEndpointSuccess() throws Exception {
        String csv = "name,lgd_code\nVillage1,LGD01";
        when(ingestionService.ingest(eq(csv), eq(IngestionFormat.CSV), eq(IngestionTarget.HABITATION), any()))
                .thenReturn(IngestionResult.success(IngestionTarget.HABITATION, IngestionFormat.CSV, 1, List.of(UUID.randomUUID())));

        mockMvc.perform(post("/api/v1/ingestion/csv")
                        .param("target", "HABITATION")
                        .contentType(MediaType.TEXT_PLAIN)
                        .content(csv))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("SUCCESS"))
                .andExpect(jsonPath("$.importedCount").value(1));
    }

    @Test
    @DisplayName("POST /api/v1/ingestion/geojson - should return 400 when ingestion fails")
    void testImportGeoJsonEndpointFailure() throws Exception {
        String geojson = "{\"type\":\"FeatureCollection\",\"features\":[]}";
        when(ingestionService.ingest(eq(geojson), eq(IngestionFormat.GEOJSON), eq(IngestionTarget.HABITATION), any()))
                .thenReturn(IngestionResult.failed(IngestionTarget.HABITATION, IngestionFormat.GEOJSON,
                        "Validation error", List.of(IngestionError.general("Empty features"))));

        mockMvc.perform(post("/api/v1/ingestion/geojson")
                        .param("target", "HABITATION")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(geojson))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value("FAILED"));
    }

    @Test
    @DisplayName("POST /api/v1/ingestion/raster-metadata - should return 201 Created on valid metadata")
    void testRegisterRasterMetadataEndpoint() throws Exception {
        String payload = """
                {
                  "provider": "Sentinel-2",
                  "dataset": "Flood_Extent_2026",
                  "crs": "EPSG:4326",
                  "resolution": "10m"
                }
                """;

        DataSource ds = new DataSource();
        ds.setProvider("Sentinel-2");
        ds.setDataset("Flood_Extent_2026");
        ds.setId(UUID.randomUUID());

        when(ingestionService.registerRasterMetadata(any(RasterMetadataDto.class))).thenReturn(ds);

        mockMvc.perform(post("/api/v1/ingestion/raster-metadata")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.provider").value("Sentinel-2"))
                .andExpect(jsonPath("$.dataset").value("Flood_Extent_2026"));
    }

    @Test
    @DisplayName("POST /api/v1/ingestion/upload - should accept multipart file upload")
    void testUploadMultipartEndpoint() throws Exception {
        MockMultipartFile file = new MockMultipartFile("file", "habitations.csv", "text/csv",
                "name,lgd_code\nVillage1,LGD01".getBytes());

        when(ingestionService.ingestFile(any(), eq(IngestionTarget.HABITATION), any()))
                .thenReturn(IngestionResult.success(IngestionTarget.HABITATION, IngestionFormat.CSV, 1, List.of(UUID.randomUUID())));

        mockMvc.perform(multipart("/api/v1/ingestion/upload")
                        .file(file)
                        .param("target", "HABITATION"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("SUCCESS"));
    }
}
