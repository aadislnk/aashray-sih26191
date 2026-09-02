package com.aashray.ingestion.parser;

import java.util.ArrayList;
import java.util.List;

import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.Geometry;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.LinearRing;
import org.locationtech.jts.geom.MultiPolygon;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.Polygon;
import org.locationtech.jts.geom.PrecisionModel;
import org.locationtech.jts.io.ParseException;
import org.locationtech.jts.io.WKTReader;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

public class GeoJsonGeometryParser {

    private static final int DEFAULT_SRID = 4326;
    private static final GeometryFactory GEOMETRY_FACTORY = new GeometryFactory(new PrecisionModel(), DEFAULT_SRID);
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    public static Geometry parseGeometry(String geoJsonString) throws Exception {
        if (geoJsonString == null || geoJsonString.isBlank()) {
            throw new IllegalArgumentException("GeoJSON string must not be empty");
        }
        JsonNode node = OBJECT_MAPPER.readTree(geoJsonString);
        return parseGeometryNode(node);
    }

    public static Geometry parseGeometryNode(JsonNode node) {
        if (node == null || node.isNull()) {
            throw new IllegalArgumentException("Geometry JSON node is null");
        }

        // Handle Feature object if passed
        if (node.has("type") && "Feature".equalsIgnoreCase(node.get("type").asText())) {
            JsonNode geomNode = node.get("geometry");
            if (geomNode == null || geomNode.isNull()) {
                throw new IllegalArgumentException("Feature does not contain a geometry object");
            }
            return parseGeometryNode(geomNode);
        }

        String type = node.has("type") ? node.get("type").asText() : "";
        JsonNode coordinates = node.get("coordinates");

        if (coordinates == null || !coordinates.isArray()) {
            throw new IllegalArgumentException("Geometry is missing coordinates array");
        }

        Geometry geometry;
        switch (type.toUpperCase()) {
            case "POINT" -> geometry = parsePoint(coordinates);
            case "POLYGON" -> geometry = parsePolygon(coordinates);
            case "MULTIPOLYGON" -> geometry = parseMultiPolygon(coordinates);
            case "LINESTRING" -> geometry = parseLineString(coordinates);
            case "MULTIPOINT" -> geometry = parseMultiPoint(coordinates);
            case "MULTILINESTRING" -> geometry = parseMultiLineString(coordinates);
            default -> throw new IllegalArgumentException("Unsupported GeoJSON geometry type: " + type);
        }

        geometry.setSRID(DEFAULT_SRID);
        return geometry;
    }

    public static Point createPoint(double longitude, double latitude) {
        Coordinate coordinate = new Coordinate(longitude, latitude);
        Point point = GEOMETRY_FACTORY.createPoint(coordinate);
        point.setSRID(DEFAULT_SRID);
        return point;
    }

    public static Point parsePoint(JsonNode coordinates) {
        Coordinate coord = parseCoordinate(coordinates);
        return GEOMETRY_FACTORY.createPoint(coord);
    }

    public static Polygon parsePolygon(JsonNode coordinates) {
        if (coordinates.size() == 0) {
            throw new IllegalArgumentException("Polygon coordinates cannot be empty");
        }

        JsonNode exteriorRingNode = coordinates.get(0);
        Coordinate[] exteriorCoords = parseCoordinateArray(exteriorRingNode);
        if (exteriorCoords.length < 4) {
            throw new IllegalArgumentException("Polygon exterior ring must have at least 4 coordinates (closed ring)");
        }
        // Ensure ring is closed
        exteriorCoords = ensureClosedRing(exteriorCoords);
        LinearRing shell = GEOMETRY_FACTORY.createLinearRing(exteriorCoords);

        LinearRing[] holes = null;
        if (coordinates.size() > 1) {
            holes = new LinearRing[coordinates.size() - 1];
            for (int i = 1; i < coordinates.size(); i++) {
                Coordinate[] holeCoords = ensureClosedRing(parseCoordinateArray(coordinates.get(i)));
                holes[i - 1] = GEOMETRY_FACTORY.createLinearRing(holeCoords);
            }
        }

        return GEOMETRY_FACTORY.createPolygon(shell, holes);
    }

    public static MultiPolygon parseMultiPolygon(JsonNode coordinates) {
        if (coordinates.size() == 0) {
            throw new IllegalArgumentException("MultiPolygon coordinates cannot be empty");
        }

        Polygon[] polygons = new Polygon[coordinates.size()];
        for (int i = 0; i < coordinates.size(); i++) {
            polygons[i] = parsePolygon(coordinates.get(i));
        }

        return GEOMETRY_FACTORY.createMultiPolygon(polygons);
    }

    public static MultiPolygon toMultiPolygon(Geometry geometry) {
        if (geometry instanceof MultiPolygon multiPolygon) {
            return multiPolygon;
        } else if (geometry instanceof Polygon polygon) {
            MultiPolygon mp = GEOMETRY_FACTORY.createMultiPolygon(new Polygon[]{polygon});
            mp.setSRID(geometry.getSRID());
            return mp;
        } else {
            throw new IllegalArgumentException("Cannot convert geometry of type " + geometry.getGeometryType() + " to MultiPolygon");
        }
    }

    public static Polygon toPolygon(Geometry geometry) {
        if (geometry instanceof Polygon polygon) {
            return polygon;
        } else if (geometry instanceof MultiPolygon mp && mp.getNumGeometries() == 1) {
            Polygon p = (Polygon) mp.getGeometryN(0);
            p.setSRID(geometry.getSRID());
            return p;
        } else {
            throw new IllegalArgumentException("Cannot convert geometry of type " + geometry.getGeometryType() + " to Polygon");
        }
    }

    public static Geometry parseWkt(String wkt) throws ParseException {
        WKTReader reader = new WKTReader(GEOMETRY_FACTORY);
        Geometry geom = reader.read(wkt);
        geom.setSRID(DEFAULT_SRID);
        return geom;
    }

    private static Coordinate parseCoordinate(JsonNode node) {
        if (!node.isArray() || node.size() < 2) {
            throw new IllegalArgumentException("Coordinate must be an array with at least [lon, lat]");
        }
        double lon = node.get(0).asDouble();
        double lat = node.get(1).asDouble();
        if (node.size() >= 3) {
            double z = node.get(2).asDouble();
            return new Coordinate(lon, lat, z);
        }
        return new Coordinate(lon, lat);
    }

    private static Coordinate[] parseCoordinateArray(JsonNode ringNode) {
        if (!ringNode.isArray()) {
            throw new IllegalArgumentException("Ring must be an array of coordinates");
        }
        Coordinate[] coords = new Coordinate[ringNode.size()];
        for (int i = 0; i < ringNode.size(); i++) {
            coords[i] = parseCoordinate(ringNode.get(i));
        }
        return coords;
    }

    private static Coordinate[] ensureClosedRing(Coordinate[] coords) {
        if (coords.length == 0) {
            return coords;
        }
        if (!coords[0].equals2D(coords[coords.length - 1])) {
            Coordinate[] closed = new Coordinate[coords.length + 1];
            System.arraycopy(coords, 0, closed, 0, coords.length);
            closed[coords.length] = new Coordinate(coords[0]);
            return closed;
        }
        return coords;
    }

    private static Geometry parseLineString(JsonNode coordinates) {
        Coordinate[] coords = parseCoordinateArray(coordinates);
        return GEOMETRY_FACTORY.createLineString(coords);
    }

    private static Geometry parseMultiPoint(JsonNode coordinates) {
        Coordinate[] coords = parseCoordinateArray(coordinates);
        return GEOMETRY_FACTORY.createMultiPointFromCoords(coords);
    }

    private static Geometry parseMultiLineString(JsonNode coordinates) {
        org.locationtech.jts.geom.LineString[] lines = new org.locationtech.jts.geom.LineString[coordinates.size()];
        for (int i = 0; i < coordinates.size(); i++) {
            lines[i] = (org.locationtech.jts.geom.LineString) parseLineString(coordinates.get(i));
        }
        return GEOMETRY_FACTORY.createMultiLineString(lines);
    }
}
