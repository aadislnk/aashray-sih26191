package com.aashray.controller;

import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import com.aashray.config.SecurityConfig;
import com.aashray.dto.dashboard.DashboardHotspotDto;
import com.aashray.dto.dashboard.DashboardSummaryDto;
import com.aashray.service.DashboardService;

@WebMvcTest(DashboardController.class)
@Import(SecurityConfig.class)
class DashboardControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private DashboardService dashboardService;

    @Test
    void summaryReturnsDashboardCountsWithoutAuthentication() throws Exception {
        when(dashboardService.getSummary(eq(null))).thenReturn(new DashboardSummaryDto(
            1L,
            2L,
            3L,
            4L,
            10L,
            OffsetDateTime.parse("2026-08-31T12:30:00Z")
        ));

        mockMvc.perform(get("/api/v1/dashboard/summary"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.p1Count").value(1))
            .andExpect(jsonPath("$.p2Count").value(2))
            .andExpect(jsonPath("$.p3Count").value(3))
            .andExpect(jsonPath("$.p4Count").value(4))
            .andExpect(jsonPath("$.totalHabitations").value(10))
            .andExpect(jsonPath("$.lastUpdated").value("2026-08-31T12:30:00Z"));
    }

    @Test
    void hotspotsReturnsDashboardItemsWithGeoJsonGeometry() throws Exception {
        when(dashboardService.getHotspots(eq("North"), eq(5))).thenReturn(List.of(new DashboardHotspotDto(
            UUID.fromString("8b75c68d-559f-4213-8dac-8e7b5e94a486"),
            "Habitation One",
            "P1",
            new BigDecimal("0.95"),
            Map.of("type", "Polygon", "coordinates", List.of()),
            OffsetDateTime.parse("2026-08-31T12:30:00Z")
        )));

        mockMvc.perform(get("/api/v1/dashboard/hotspots")
                .param("region", "North")
                .param("limit", "5"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].habitationId").value("8b75c68d-559f-4213-8dac-8e7b5e94a486"))
            .andExpect(jsonPath("$[0].habitationName").value("Habitation One"))
            .andExpect(jsonPath("$[0].priority").value("P1"))
            .andExpect(jsonPath("$[0].riskScore").value(0.95))
            .andExpect(jsonPath("$[0].geometry.type").value("Polygon"))
            .andExpect(jsonPath("$[0].assessmentTime").value("2026-08-31T12:30:00Z"));
    }
}
