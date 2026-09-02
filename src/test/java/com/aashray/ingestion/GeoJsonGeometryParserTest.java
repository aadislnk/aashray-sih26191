package com.aashray.ingestion;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.locationtech.jts.geom.Geometry;
import org.locationtech.jts.geom.MultiPolygon;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.Polygon;

import com.aashray.ingestion.parser.GeoJsonGeometryParser;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class GeoJsonGeometryParserTest {

    @Test
    @DisplayName("Should parse GeoJSON Point with SRID 4326")
    void testParsePoint() throws Exception {
        String json = "{\"type\": \"Point\", \"coordinates\": [77.5946, 12.9716]}";
        Geometry geom = GeoJsonGeometryParser.parseGeometry(json);

        assertThat(geom).isInstanceOf(Point.class);
        assertThat(geom.getSRID()).isEqualTo(4326);
        Point pt = (Point) geom;
        assertThat(pt.getX()).isEqualTo(77.5946);
        assertThat(pt.getY()).isEqualTo(12.9716);
    }

    @Test
    @DisplayName("Should parse GeoJSON Polygon with SRID 4326")
    void testParsePolygon() throws Exception {
        String json = """
                {
                    "type": "Polygon",
                    "coordinates": [
                        [[77.0, 12.0], [77.1, 12.0], [77.1, 12.1], [77.0, 12.1], [77.0, 12.0]]
                    ]
                }
                """;
        Geometry geom = GeoJsonGeometryParser.parseGeometry(json);

        assertThat(geom).isInstanceOf(Polygon.class);
        assertThat(geom.getSRID()).isEqualTo(4326);
        assertThat(geom.isValid()).isTrue();
    }

    @Test
    @DisplayName("Should parse GeoJSON MultiPolygon with SRID 4326")
    void testParseMultiPolygon() throws Exception {
        String json = """
                {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [[[77.0, 12.0], [77.1, 12.0], [77.1, 12.1], [77.0, 12.1], [77.0, 12.0]]],
                        [[[77.2, 12.2], [77.3, 12.2], [77.3, 12.3], [77.2, 12.3], [77.2, 12.2]]]
                    ]
                }
                """;
        Geometry geom = GeoJsonGeometryParser.parseGeometry(json);

        assertThat(geom).isInstanceOf(MultiPolygon.class);
        assertThat(geom.getSRID()).isEqualTo(4326);
        MultiPolygon mp = (MultiPolygon) geom;
        assertThat(mp.getNumGeometries()).isEqualTo(2);
    }

    @Test
    @DisplayName("Should convert single Polygon to MultiPolygon")
    void testToMultiPolygon() throws Exception {
        String json = """
                {
                    "type": "Polygon",
                    "coordinates": [
                        [[77.0, 12.0], [77.1, 12.0], [77.1, 12.1], [77.0, 12.1], [77.0, 12.0]]
                    ]
                }
                """;
        Geometry geom = GeoJsonGeometryParser.parseGeometry(json);
        MultiPolygon mp = GeoJsonGeometryParser.toMultiPolygon(geom);

        assertThat(mp).isNotNull();
        assertThat(mp.getNumGeometries()).isEqualTo(1);
    }

    @Test
    @DisplayName("Should fail when parsing unsupported or invalid GeoJSON geometry")
    void testInvalidGeometryType() {
        String json = "{\"type\": \"UnknownType\", \"coordinates\": [1, 2]}";
        assertThatThrownBy(() -> GeoJsonGeometryParser.parseGeometry(json))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Unsupported GeoJSON geometry type");
    }
}
