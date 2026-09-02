package com.aashray.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.aashray.dto.dashboard.DashboardHotspotDto;
import com.aashray.dto.dashboard.DashboardSummaryDto;
import com.aashray.exception.ApiException;
import com.aashray.repository.RiskAssessmentRepository;
import com.aashray.repository.RiskAssessmentRepository.DashboardHotspotProjection;
import com.aashray.repository.RiskAssessmentRepository.DashboardSummaryProjection;

@ExtendWith(MockitoExtension.class)
class DashboardServiceTest {

    private static final OffsetDateTime UPDATED_AT = OffsetDateTime.parse("2026-08-31T12:30:00Z");

    @Mock
    private RiskAssessmentRepository riskAssessmentRepository;

    @Test
    void summaryMapsNullCountsToZeroForEmptyDatabase() {
        DashboardService service = new DashboardService(riskAssessmentRepository);
        when(riskAssessmentRepository.summarizeLatestRisk()).thenReturn(summary(null, null, null, null, null, null));

        DashboardSummaryDto dashboardSummary = service.getSummary(null);

        assertThat(dashboardSummary.p1Count()).isZero();
        assertThat(dashboardSummary.p2Count()).isZero();
        assertThat(dashboardSummary.p3Count()).isZero();
        assertThat(dashboardSummary.p4Count()).isZero();
        assertThat(dashboardSummary.totalHabitations()).isZero();
        assertThat(dashboardSummary.lastUpdated()).isNull();
    }

    @Test
    void hotspotsParseGeoJsonGeometry() {
        DashboardService service = new DashboardService(riskAssessmentRepository);
        when(riskAssessmentRepository.findTopHotspots(10)).thenReturn(List.of(hotspot(
            "8b75c68d-559f-4213-8dac-8e7b5e94a486",
            "Habitation One",
            "P1",
            new BigDecimal("0.95"),
            "{\"type\":\"Polygon\",\"coordinates\":[[[77.0,12.0],[77.1,12.0],[77.1,12.1],[77.0,12.1],[77.0,12.0]]]}",
            UPDATED_AT
        )));

        List<DashboardHotspotDto> hotspots = service.getHotspots(null, 10);

        assertThat(hotspots).hasSize(1);
        assertThat(hotspots.get(0).habitationName()).isEqualTo("Habitation One");
        assertThat(hotspots.get(0).geometry()).containsEntry("type", "Polygon");
        assertThat(hotspots.get(0).assessmentTime()).isEqualTo(UPDATED_AT);
    }

    @Test
    void hotspotsRejectInvalidLimit() {
        DashboardService service = new DashboardService(riskAssessmentRepository);

        assertThatThrownBy(() -> service.getHotspots(null, 0))
            .isInstanceOf(ApiException.class)
            .hasMessage("limit must be greater than 0");

        assertThatThrownBy(() -> service.getHotspots(null, 101))
            .isInstanceOf(ApiException.class)
            .hasMessage("limit must be less than or equal to 100");
    }

    private DashboardSummaryProjection summary(Long p1Count, Long p2Count, Long p3Count, Long p4Count,
                                               Long totalHabitations, OffsetDateTime lastUpdated) {
        return new DashboardSummaryProjection() {
            @Override
            public Long getP1Count() {
                return p1Count;
            }

            @Override
            public Long getP2Count() {
                return p2Count;
            }

            @Override
            public Long getP3Count() {
                return p3Count;
            }

            @Override
            public Long getP4Count() {
                return p4Count;
            }

            @Override
            public Long getTotalHabitations() {
                return totalHabitations;
            }

            @Override
            public OffsetDateTime getLastUpdated() {
                return lastUpdated;
            }
        };
    }

    private DashboardHotspotProjection hotspot(String habitationId, String habitationName, String priority,
                                               BigDecimal riskScore, String geometry, OffsetDateTime assessmentTime) {
        return new DashboardHotspotProjection() {
            @Override
            public String getHabitationId() {
                return habitationId;
            }

            @Override
            public String getHabitationName() {
                return habitationName;
            }

            @Override
            public String getPriority() {
                return priority;
            }

            @Override
            public BigDecimal getRiskScore() {
                return riskScore;
            }

            @Override
            public String getGeometry() {
                return geometry;
            }

            @Override
            public OffsetDateTime getAssessmentTime() {
                return assessmentTime;
            }
        };
    }
}
