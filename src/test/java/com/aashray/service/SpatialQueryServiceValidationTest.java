package com.aashray.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.PrecisionModel;

import com.aashray.exception.ApiException;
import com.aashray.repository.AdminBoundaryRepository;
import com.aashray.repository.HabitationRepository;
import com.aashray.repository.InfrastructureRepository;
import com.aashray.repository.RelocationSiteRepository;

import static org.mockito.Mockito.mock;

class SpatialQueryServiceValidationTest {

    private static final GeometryFactory GEOMETRY_FACTORY = new GeometryFactory(new PrecisionModel(), 4326);

    private final SpatialQueryService service = new SpatialQueryService(
            mock(HabitationRepository.class),
            mock(InfrastructureRepository.class),
            mock(RelocationSiteRepository.class),
            mock(AdminBoundaryRepository.class));

    @Test
    void rejectsInvalidLongitudeRange() {
        ApiException exception = assertThrows(ApiException.class, () ->
                service.findHabitationsWithinBoundingBox(-181.0, 0.0, -170.0, 10.0));
        assertEquals("VALIDATION_ERROR", exception.getCode());
    }

    @Test
    void rejectsInvalidLatitudeRange() {
        ApiException exception = assertThrows(ApiException.class, () ->
                service.findHabitationsWithinBoundingBox(0.0, -91.0, 10.0, 10.0));
        assertEquals("VALIDATION_ERROR", exception.getCode());
    }

    @Test
    void rejectsInvertedBoundingBox() {
        ApiException exception = assertThrows(ApiException.class, () ->
                service.findHabitationsWithinBoundingBox(10.0, 0.0, 5.0, 10.0));
        assertEquals("VALIDATION_ERROR", exception.getCode());
    }

    @Test
    void rejectsZeroDistance() {
        ApiException exception = assertThrows(ApiException.class, () ->
                service.findHabitationsWithinRadius(77.6, 12.9, 0.0));
        assertEquals("VALIDATION_ERROR", exception.getCode());
    }

    @Test
    void rejectsNegativeDistance() {
        ApiException exception = assertThrows(ApiException.class, () ->
                service.findHabitationsWithinRadius(77.6, 12.9, -1.0));
        assertEquals("VALIDATION_ERROR", exception.getCode());
    }

    @Test
    void rejectsGeometryWithWrongSrid() {
        Point point = GEOMETRY_FACTORY.createPoint(new Coordinate(77.6, 12.9));
        point.setSRID(3857);

        ApiException exception = assertThrows(ApiException.class, () ->
                service.findHabitationsIntersectingGeometry(point));
        assertEquals("VALIDATION_ERROR", exception.getCode());
    }
}
