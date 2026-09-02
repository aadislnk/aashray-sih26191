package com.aashray.service;

import static org.assertj.core.api.Assertions.assertThat;

import java.sql.Connection;
import java.sql.SQLException;
import java.time.OffsetDateTime;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.Test;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.Geometry;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.LinearRing;
import org.locationtech.jts.geom.MultiPolygon;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.Polygon;
import org.locationtech.jts.geom.PrecisionModel;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import javax.sql.DataSource;

import com.aashray.entity.AdminBoundary;
import com.aashray.entity.Habitation;
import com.aashray.entity.Infrastructure;
import com.aashray.entity.RelocationSite;
import com.aashray.repository.AdminBoundaryRepository;
import com.aashray.repository.HabitationRepository;
import com.aashray.repository.InfrastructureRepository;
import com.aashray.repository.RelocationSiteRepository;
import com.aashray.repository.RiskAssessmentRepository;

@SpringBootTest
@ActiveProfiles("test")
class SpatialQueryIntegrationTest {

    private static final GeometryFactory GEOMETRY_FACTORY = new GeometryFactory(new PrecisionModel(), 4326);
    private static final OffsetDateTime NOW = OffsetDateTime.parse("2026-08-31T12:00:00Z");

    @Autowired
    private SpatialQueryService spatialQueryService;

    @Autowired
    private AdminBoundaryRepository adminBoundaryRepository;

    @Autowired
    private HabitationRepository habitationRepository;

    @Autowired
    private InfrastructureRepository infrastructureRepository;

    @Autowired
    private RelocationSiteRepository relocationSiteRepository;

    @Autowired
    private RiskAssessmentRepository riskAssessmentRepository;

    @Autowired
    private DataSource dataSource;

    @BeforeEach
    void setUp() {
        assumeDatabaseAvailable();
        riskAssessmentRepository.deleteAll();
        relocationSiteRepository.deleteAll();
        infrastructureRepository.deleteAll();
        habitationRepository.deleteAll();
        adminBoundaryRepository.deleteAll();

        AdminBoundary adminBoundary = new AdminBoundary();
        adminBoundary.setName("Test Boundary");
        adminBoundary.setBoundaryType("district");
        adminBoundary.setGeometry(multiPolygon(square(77.0, 12.0, 78.0, 13.0)));
        adminBoundary.setCreatedAt(NOW);
        adminBoundary.setUpdatedAt(NOW);
        adminBoundary = adminBoundaryRepository.saveAndFlush(adminBoundary);

        Habitation habitationInside = new Habitation();
        habitationInside.setLgdCode("HAB-001");
        habitationInside.setName("Habitation Inside");
        habitationInside.setAdminBoundary(adminBoundary);
        habitationInside.setGeometry(square(77.2, 12.2, 77.4, 12.4));
        habitationInside.setCreatedAt(NOW);
        habitationInside.setUpdatedAt(NOW);
        habitationRepository.saveAndFlush(habitationInside);

        Habitation habitationOutside = new Habitation();
        habitationOutside.setLgdCode("HAB-002");
        habitationOutside.setName("Habitation Outside");
        habitationOutside.setAdminBoundary(adminBoundary);
        habitationOutside.setGeometry(square(79.0, 14.0, 79.2, 14.2));
        habitationOutside.setCreatedAt(NOW);
        habitationOutside.setUpdatedAt(NOW);
        habitationRepository.saveAndFlush(habitationOutside);

        Infrastructure infrastructureNear = new Infrastructure();
        infrastructureNear.setHabitation(habitationInside);
        infrastructureNear.setInfrastructureType("school");
        infrastructureNear.setStatus("OPEN");
        infrastructureNear.setGeometry(point(77.601, 12.901));
        infrastructureNear.setCapacity(100);
        infrastructureNear.setUpdatedAt(NOW);
        infrastructureRepository.saveAndFlush(infrastructureNear);

        Infrastructure infrastructureOutside = new Infrastructure();
        infrastructureOutside.setHabitation(habitationInside);
        infrastructureOutside.setInfrastructureType("hospital");
        infrastructureOutside.setStatus("CLOSED");
        infrastructureOutside.setGeometry(point(77.75, 13.05));
        infrastructureOutside.setCapacity(50);
        infrastructureOutside.setUpdatedAt(NOW);
        infrastructureRepository.saveAndFlush(infrastructureOutside);

        RelocationSite relocationSiteIntersecting = new RelocationSite();
        relocationSiteIntersecting.setName("Relocation Intersecting");
        relocationSiteIntersecting.setGeometry(square(77.85, 12.85, 78.15, 13.15));
        relocationSiteIntersecting.setStatus("AVAILABLE");
        relocationSiteIntersecting.setUpdatedAt(NOW);
        relocationSiteRepository.saveAndFlush(relocationSiteIntersecting);

        RelocationSite relocationSiteOutside = new RelocationSite();
        relocationSiteOutside.setName("Relocation Outside");
        relocationSiteOutside.setGeometry(square(79.5, 14.5, 79.8, 14.8));
        relocationSiteOutside.setStatus("AVAILABLE");
        relocationSiteOutside.setUpdatedAt(NOW);
        relocationSiteRepository.saveAndFlush(relocationSiteOutside);
    }

    private void assumeDatabaseAvailable() {
        try (Connection ignored = dataSource.getConnection()) {
            // The test can proceed.
        } catch (SQLException exception) {
            Assumptions.assumeTrue(false, "PostgreSQL/PostGIS database is not available for integration tests");
        }
    }

    @Test
    void boundingBoxReturnsIntersectingFeaturesAndExcludesOutsideFeatures() {
        List<Habitation> habitations = spatialQueryService.findHabitationsWithinBoundingBox(77.0, 12.0, 78.0, 13.0);
        assertThat(habitations).extracting(Habitation::getName)
                .contains("Habitation Inside")
                .doesNotContain("Habitation Outside");

        List<RelocationSite> relocationSites = spatialQueryService.findRelocationSitesWithinBoundingBox(77.0, 12.0, 78.0, 13.0);
        assertThat(relocationSites).extracting(RelocationSite::getName)
                .contains("Relocation Intersecting")
                .doesNotContain("Relocation Outside");
    }

    @Test
    void radiusReturnsNearbyInfrastructureAndExcludesFarInfrastructure() {
        List<Infrastructure> infrastructure = spatialQueryService.findInfrastructureWithinRadius(77.6, 12.9, 5000.0);
        assertThat(infrastructure).extracting(Infrastructure::getStatus)
                .contains("OPEN")
                .doesNotContain("CLOSED");

        List<Infrastructure> none = spatialQueryService.findInfrastructureWithinRadius(77.6, 12.9, 50.0);
        assertThat(none).isEmpty();
    }

    @Test
    void geometryIntersectionReturnsIntersectingFeaturesAndPreservesSrid() {
        Geometry intersectingQuery = square(77.25, 12.25, 77.35, 12.35);
        List<Habitation> habitations = spatialQueryService.findHabitationsIntersectingGeometry(intersectingQuery);
        assertThat(habitations).extracting(Habitation::getName)
                .contains("Habitation Inside")
                .doesNotContain("Habitation Outside");
        assertThat(habitations).allSatisfy(habitation ->
                assertThat(habitation.getGeometry().getSRID()).isEqualTo(4326));

        Geometry adminQuery = square(77.1, 12.1, 77.3, 12.3);
        List<AdminBoundary> adminBoundaries = spatialQueryService.findAdminBoundariesIntersectingGeometry(adminQuery);
        assertThat(adminBoundaries).hasSize(1);
        assertThat(adminBoundaries.get(0).getGeometry().getSRID()).isEqualTo(4326);

        Geometry outsideQuery = square(80.0, 15.0, 80.5, 15.5);
        assertThat(spatialQueryService.findAdminBoundariesIntersectingGeometry(outsideQuery)).isEmpty();
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

    private Point point(double longitude, double latitude) {
        Point point = GEOMETRY_FACTORY.createPoint(new Coordinate(longitude, latitude));
        point.setSRID(4326);
        return point;
    }
}
