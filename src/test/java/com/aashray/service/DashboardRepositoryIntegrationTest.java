package com.aashray.service;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.SQLException;
import java.time.OffsetDateTime;
import java.util.List;

import javax.sql.DataSource;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.LinearRing;
import org.locationtech.jts.geom.MultiPolygon;
import org.locationtech.jts.geom.Polygon;
import org.locationtech.jts.geom.PrecisionModel;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import com.aashray.dto.dashboard.DashboardHotspotDto;
import com.aashray.dto.dashboard.DashboardSummaryDto;
import com.aashray.entity.AdminBoundary;
import com.aashray.entity.Habitation;
import com.aashray.entity.RiskAssessment;
import com.aashray.repository.AdminBoundaryRepository;
import com.aashray.repository.HabitationRepository;
import com.aashray.repository.RiskAssessmentRepository;

@SpringBootTest
@ActiveProfiles("test")
class DashboardRepositoryIntegrationTest {

    private static final GeometryFactory GEOMETRY_FACTORY = new GeometryFactory(new PrecisionModel(), 4326);
    private static final OffsetDateTime BASE_TIME = OffsetDateTime.parse("2026-08-31T10:00:00Z");

    @Autowired
    private DashboardService dashboardService;

    @Autowired
    private AdminBoundaryRepository adminBoundaryRepository;

    @Autowired
    private HabitationRepository habitationRepository;

    @Autowired
    private RiskAssessmentRepository riskAssessmentRepository;

    @Autowired
    private DataSource dataSource;

    @BeforeEach
    void setUp() {
        assumeDashboardTablesAvailable();
        cleanDashboardData();
    }

    @AfterEach
    void tearDown() {
        try {
            cleanDashboardData();
        } catch (RuntimeException ignored) {
            // Integration tests are skipped when the local PostgreSQL/PostGIS database is unavailable.
        }
    }

    @Test
    void summaryCountsLatestAssessmentPerHabitationAndIgnoresUnknownPriority() {
        AdminBoundary north = adminBoundary("North");

        Habitation historical = habitation("Historical Latest", north, 77.0);
        risk(historical, "P1", "0.90", BASE_TIME.plusHours(1));
        risk(historical, "P2", "0.50", BASE_TIME.plusHours(2));

        risk(habitation("P1 Habitation", north, 77.2), "P1", "0.70", BASE_TIME.plusHours(3));
        risk(habitation("P3 Habitation", north, 77.4), "P3", "0.60", BASE_TIME.plusHours(4));
        risk(habitation("P4 Habitation", north, 77.6), "P4", "0.40", BASE_TIME.plusHours(6));
        risk(habitation("Unknown Priority", north, 77.8), "WATCH", "0.99", BASE_TIME.plusHours(5));

        DashboardSummaryDto summary = dashboardService.getSummary(null);

        assertThat(summary.p1Count()).isEqualTo(1);
        assertThat(summary.p2Count()).isEqualTo(1);
        assertThat(summary.p3Count()).isEqualTo(1);
        assertThat(summary.p4Count()).isEqualTo(1);
        assertThat(summary.totalHabitations()).isEqualTo(5);
        assertThat(summary.lastUpdated()).isEqualTo(BASE_TIME.plusHours(6));
    }

    @Test
    void emptyDatabaseReturnsZeroCountSummaryAndEmptyHotspots() {
        DashboardSummaryDto summary = dashboardService.getSummary(null);

        assertThat(summary.p1Count()).isZero();
        assertThat(summary.p2Count()).isZero();
        assertThat(summary.p3Count()).isZero();
        assertThat(summary.p4Count()).isZero();
        assertThat(summary.totalHabitations()).isZero();
        assertThat(summary.lastUpdated()).isNull();
        assertThat(dashboardService.getHotspots(null, 10)).isEmpty();
    }

    @Test
    void hotspotsRankPriorityBeforeRiskScoreAndRiskScoreWithinPriority() {
        AdminBoundary north = adminBoundary("North");
        risk(habitation("P2 High Risk", north, 77.0), "P2", "0.99", BASE_TIME.plusHours(1));
        risk(habitation("P1 Low Risk", north, 77.2), "P1", "0.20", BASE_TIME.plusHours(2));
        risk(habitation("P1 High Risk", north, 77.4), "P1", "0.80", BASE_TIME.plusHours(3));
        risk(habitation("P3 High Risk", north, 77.6), "P3", "0.95", BASE_TIME.plusHours(4));

        List<DashboardHotspotDto> hotspots = dashboardService.getHotspots(null, 10);

        assertThat(hotspots).extracting(DashboardHotspotDto::habitationName)
            .containsExactly("P1 High Risk", "P1 Low Risk", "P2 High Risk", "P3 High Risk");
        assertThat(hotspots.get(0).geometry()).containsEntry("type", "Polygon");
    }

    @Test
    void regionFilterUsesExistingAdminBoundaryName() {
        AdminBoundary north = adminBoundary("North");
        AdminBoundary south = adminBoundary("South");
        risk(habitation("North P1", north, 77.0), "P1", "0.90", BASE_TIME.plusHours(1));
        risk(habitation("South P2", south, 78.0), "P2", "0.90", BASE_TIME.plusHours(2));

        DashboardSummaryDto summary = dashboardService.getSummary("North");
        List<DashboardHotspotDto> hotspots = dashboardService.getHotspots("North", 10);

        assertThat(summary.p1Count()).isEqualTo(1);
        assertThat(summary.p2Count()).isZero();
        assertThat(summary.totalHabitations()).isEqualTo(1);
        assertThat(hotspots).extracting(DashboardHotspotDto::habitationName).containsExactly("North P1");
    }

    private void assumeDashboardTablesAvailable() {
        try (Connection connection = dataSource.getConnection();
             var statement = connection.createStatement()) {
            statement.executeQuery("select 1 from risk_assessment limit 1");
        } catch (SQLException exception) {
            Assumptions.assumeTrue(false, "PostgreSQL/PostGIS dashboard tables are not available for integration tests");
        }
    }

    private void cleanDashboardData() {
        riskAssessmentRepository.deleteAll();
        habitationRepository.deleteAll();
        adminBoundaryRepository.deleteAll();
    }

    private AdminBoundary adminBoundary(String name) {
        AdminBoundary adminBoundary = new AdminBoundary();
        adminBoundary.setName(name);
        adminBoundary.setBoundaryType("region");
        adminBoundary.setGeometry(multiPolygon(square(76.0, 11.0, 80.0, 15.0)));
        adminBoundary.setCreatedAt(BASE_TIME);
        adminBoundary.setUpdatedAt(BASE_TIME);
        return adminBoundaryRepository.saveAndFlush(adminBoundary);
    }

    private Habitation habitation(String name, AdminBoundary adminBoundary, double longitude) {
        Habitation habitation = new Habitation();
        habitation.setLgdCode(name.toUpperCase().replace(" ", "-"));
        habitation.setName(name);
        habitation.setAdminBoundary(adminBoundary);
        habitation.setGeometry(square(longitude, 12.0, longitude + 0.1, 12.1));
        habitation.setCreatedAt(BASE_TIME);
        habitation.setUpdatedAt(BASE_TIME);
        return habitationRepository.saveAndFlush(habitation);
    }

    private RiskAssessment risk(Habitation habitation, String priority, String riskScore, OffsetDateTime assessmentTime) {
        RiskAssessment riskAssessment = new RiskAssessment();
        riskAssessment.setHabitation(habitation);
        riskAssessment.setPriority(priority);
        riskAssessment.setRiskScore(new BigDecimal(riskScore));
        riskAssessment.setRiskBand("test");
        riskAssessment.setAssessmentTime(assessmentTime);
        return riskAssessmentRepository.saveAndFlush(riskAssessment);
    }

    private Polygon square(double minLongitude, double minLatitude, double maxLongitude, double maxLatitude) {
        Coordinate[] coordinates = new Coordinate[] {
            new Coordinate(minLongitude, minLatitude),
            new Coordinate(maxLongitude, minLatitude),
            new Coordinate(maxLongitude, maxLatitude),
            new Coordinate(minLongitude, maxLatitude),
            new Coordinate(minLongitude, minLatitude)
        };
        LinearRing shell = GEOMETRY_FACTORY.createLinearRing(coordinates);
        Polygon polygon = GEOMETRY_FACTORY.createPolygon(shell);
        polygon.setSRID(4326);
        return polygon;
    }

    private MultiPolygon multiPolygon(Polygon polygon) {
        MultiPolygon multiPolygon = GEOMETRY_FACTORY.createMultiPolygon(new Polygon[] { polygon });
        multiPolygon.setSRID(4326);
        return multiPolygon;
    }
}
