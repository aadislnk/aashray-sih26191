package com.aashray.ingestion;

import java.math.BigDecimal;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.Polygon;
import org.locationtech.jts.geom.PrecisionModel;

import com.aashray.ingestion.model.IngestionError;
import com.aashray.ingestion.model.IngestionTarget;
import com.aashray.ingestion.validator.IngestionValidator;

import static org.assertj.core.api.Assertions.assertThat;

class IngestionValidatorTest {

    private IngestionValidator validator;
    private GeometryFactory factory;

    @BeforeEach
    void setUp() {
        validator = new IngestionValidator();
        factory = new GeometryFactory(new PrecisionModel(), 4326);
    }

    @Test
    @DisplayName("Should pass valid coordinates")
    void testValidCoordinates() {
        Coordinate coord = new Coordinate(77.5946, 12.9716);
        List<IngestionError> errors = validator.validateCoordinates(coord, 1);
        assertThat(errors).isEmpty();
    }

    @Test
    @DisplayName("Should detect invalid out-of-range coordinates")
    void testInvalidCoordinates() {
        Coordinate invalidLon = new Coordinate(195.0, 12.0);
        List<IngestionError> errorsLon = validator.validateCoordinates(invalidLon, 1);
        assertThat(errorsLon).hasSize(1);
        assertThat(errorsLon.get(0).field()).isEqualTo("longitude");

        Coordinate invalidLat = new Coordinate(77.0, -95.0);
        List<IngestionError> errorsLat = validator.validateCoordinates(invalidLat, 2);
        assertThat(errorsLat).hasSize(1);
        assertThat(errorsLat.get(0).field()).isEqualTo("latitude");
    }

    @Test
    @DisplayName("Should detect unsupported SRID")
    void testUnsupportedSrid() {
        GeometryFactory factory3857 = new GeometryFactory(new PrecisionModel(), 3857);
        Point point = factory3857.createPoint(new Coordinate(0, 0));

        List<IngestionError> errors = validator.validateGeometry(point, IngestionTarget.INFRASTRUCTURE, 1);
        assertThat(errors).anyMatch(e -> "srid".equals(e.field()));
    }

    @Test
    @DisplayName("Should detect self-intersecting invalid polygon (bowtie)")
    void testSelfIntersectingPolygon() {
        Coordinate[] bowtie = new Coordinate[]{
                new Coordinate(0, 0),
                new Coordinate(0, 2),
                new Coordinate(2, 0),
                new Coordinate(2, 2),
                new Coordinate(0, 0)
        };
        Polygon poly = factory.createPolygon(bowtie);

        List<IngestionError> errors = validator.validateGeometry(poly, IngestionTarget.HABITATION, 1);
        assertThat(errors).anyMatch(e -> e.message().contains("Geometry is invalid") || e.message().contains("Self-intersection"));
    }

    @Test
    @DisplayName("Should detect geometry type mismatch for target entity")
    void testGeometryTypeMismatch() {
        Point point = factory.createPoint(new Coordinate(77.0, 12.0));
        List<IngestionError> errors = validator.validateGeometry(point, IngestionTarget.HABITATION, 1);
        assertThat(errors).anyMatch(e -> e.message().contains("requires a Polygon"));
    }

    @Test
    @DisplayName("Should validate numeric bounds and years")
    void testNumericBounds() {
        List<IngestionError> negPopErrors = validator.validateNonNegativeInteger(-10, "populationCount", 1);
        assertThat(negPopErrors).hasSize(1);

        List<IngestionError> invalidYearErrors = validator.validateYear(1850, 1);
        assertThat(invalidYearErrors).hasSize(1);

        List<IngestionError> validYearErrors = validator.validateYear(2026, 1);
        assertThat(validYearErrors).isEmpty();

        List<IngestionError> invalidScoreErrors = validator.validateScore(BigDecimal.valueOf(150.0), "score", 1);
        assertThat(invalidScoreErrors).hasSize(1);
    }
}
