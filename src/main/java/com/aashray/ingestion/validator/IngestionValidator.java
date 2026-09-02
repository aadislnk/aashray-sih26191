package com.aashray.ingestion.validator;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;

import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.Geometry;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.Polygon;
import org.locationtech.jts.geom.MultiPolygon;
import org.locationtech.jts.operation.valid.IsValidOp;
import org.locationtech.jts.operation.valid.TopologyValidationError;
import org.springframework.stereotype.Component;

import com.aashray.ingestion.model.IngestionError;
import com.aashray.ingestion.model.IngestionTarget;

@Component
public class IngestionValidator {

    private static final int EXPECTED_SRID = 4326;
    private static final Set<String> ALLOWED_CRS_NAMES = Set.of(
        "EPSG:4326",
        "4326",
        "URN:OGC:DEF:CRS:OGC:1.3:CRS84",
        "URN:OGC:DEF:CRS:EPSG::4326",
        "CRS84",
        "WGS84",
        "WGS 84"
    );

    public List<IngestionError> validateCoordinates(Coordinate coordinate, int rowNumber) {
        List<IngestionError> errors = new ArrayList<>();
        if (coordinate == null) {
            errors.add(IngestionError.row(rowNumber, "coordinates", "Coordinates cannot be null", null));
            return errors;
        }

        if (Double.isNaN(coordinate.x) || coordinate.x < -180.0 || coordinate.x > 180.0) {
            errors.add(IngestionError.row(rowNumber, "longitude",
                    "Longitude must be between -180.0 and 180.0", coordinate.x));
        }

        if (Double.isNaN(coordinate.y) || coordinate.y < -90.0 || coordinate.y > 90.0) {
            errors.add(IngestionError.row(rowNumber, "latitude",
                    "Latitude must be between -90.0 and 90.0", coordinate.y));
        }

        return errors;
    }

    public List<IngestionError> validateGeometry(Geometry geometry, IngestionTarget target, int rowNumber) {
        List<IngestionError> errors = new ArrayList<>();

        if (geometry == null || geometry.isEmpty()) {
            errors.add(IngestionError.row(rowNumber, "geometry", "Geometry must not be null or empty", null));
            return errors;
        }

        // SRID validation
        if (geometry.getSRID() != 0 && geometry.getSRID() != EXPECTED_SRID) {
            errors.add(IngestionError.row(rowNumber, "srid",
                    "Unsupported SRID " + geometry.getSRID() + ". Expected " + EXPECTED_SRID, geometry.getSRID()));
        }

        // Coordinate bound checks on all vertices
        for (Coordinate coord : geometry.getCoordinates()) {
            errors.addAll(validateCoordinates(coord, rowNumber));
        }

        // Geometry validity via JTS IsValidOp
        IsValidOp validOp = new IsValidOp(geometry);
        TopologyValidationError topoErr = validOp.getValidationError();
        if (topoErr != null) {
            errors.add(IngestionError.row(rowNumber, "geometry",
                    "Geometry is invalid: " + topoErr.getMessage() + " at coordinate " + topoErr.getCoordinate(),
                    geometry.toText()));
        }

        // Target geometry type check
        if (target != null) {
            switch (target) {
                case HABITATION, RELOCATION_SITE -> {
                    if (!(geometry instanceof Polygon) && !(geometry instanceof MultiPolygon)) {
                        errors.add(IngestionError.row(rowNumber, "geometry",
                                "Target " + target + " requires a Polygon or MultiPolygon geometry, but got "
                                        + geometry.getGeometryType(), geometry.getGeometryType()));
                    }
                }
                case ADMIN_BOUNDARY -> {
                    if (!(geometry instanceof MultiPolygon) && !(geometry instanceof Polygon)) {
                        errors.add(IngestionError.row(rowNumber, "geometry",
                                "Target ADMIN_BOUNDARY requires MultiPolygon or Polygon geometry, but got "
                                        + geometry.getGeometryType(), geometry.getGeometryType()));
                    }
                }
                case INFRASTRUCTURE -> {
                    if (!(geometry instanceof Point)) {
                        errors.add(IngestionError.row(rowNumber, "geometry",
                                "Target INFRASTRUCTURE requires a Point geometry, but got "
                                        + geometry.getGeometryType(), geometry.getGeometryType()));
                    }
                }
                default -> {}
            }
        }

        return errors;
    }

    public List<IngestionError> validateCrs(String crsName, int rowNumber) {
        List<IngestionError> errors = new ArrayList<>();
        if (crsName == null || crsName.isBlank()) {
            return errors; // Default CRS84 / 4326 will be assumed
        }

        String normalized = crsName.trim().toUpperCase();
        if (!ALLOWED_CRS_NAMES.contains(normalized)) {
            errors.add(IngestionError.row(rowNumber, "crs",
                    "Unsupported CRS '" + crsName + "'. Expected EPSG:4326 or CRS84", crsName));
        }
        return errors;
    }

    public List<IngestionError> validateNonNegativeInteger(Integer value, String fieldName, int rowNumber) {
        List<IngestionError> errors = new ArrayList<>();
        if (value != null && value < 0) {
            errors.add(IngestionError.row(rowNumber, fieldName,
                    fieldName + " must be non-negative (>= 0), got " + value, value));
        }
        return errors;
    }

    public List<IngestionError> validateYear(Integer year, int rowNumber) {
        List<IngestionError> errors = new ArrayList<>();
        if (year != null && (year < 1900 || year > 2100)) {
            errors.add(IngestionError.row(rowNumber, "year",
                    "Year must be between 1900 and 2100, got " + year, year));
        }
        return errors;
    }

    public List<IngestionError> validateScore(BigDecimal score, String fieldName, int rowNumber) {
        List<IngestionError> errors = new ArrayList<>();
        if (score != null) {
            double val = score.doubleValue();
            if (val < 0.0 || val > 100.0) {
                errors.add(IngestionError.row(rowNumber, fieldName,
                        fieldName + " must be within valid range [0.0, 1.0] or [0, 100], got " + score, score));
            }
        }
        return errors;
    }

    public List<IngestionError> validateRequiredField(Object value, String fieldName, int rowNumber) {
        List<IngestionError> errors = new ArrayList<>();
        if (value == null || (value instanceof String str && str.isBlank())) {
            errors.add(IngestionError.row(rowNumber, fieldName,
                    "Required field '" + fieldName + "' is missing or empty", value));
        }
        return errors;
    }
}
