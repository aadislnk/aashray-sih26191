package com.aashray.ingestion.importer;

import java.io.IOException;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.Geometry;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.MultiPolygon;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.Polygon;
import org.locationtech.jts.geom.PrecisionModel;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import com.aashray.entity.AdminBoundary;
import com.aashray.entity.DataSource;
import com.aashray.entity.Habitation;
import com.aashray.entity.Infrastructure;
import com.aashray.entity.Population;
import com.aashray.entity.RelocationSite;
import com.aashray.ingestion.model.IngestionError;
import com.aashray.ingestion.model.IngestionFormat;
import com.aashray.ingestion.model.IngestionResult;
import com.aashray.ingestion.model.IngestionStatus;
import com.aashray.ingestion.model.IngestionTarget;
import com.aashray.ingestion.parser.CsvParser;
import com.aashray.ingestion.parser.CsvParser.CsvParseResult;
import com.aashray.ingestion.parser.CsvParser.CsvRow;
import com.aashray.ingestion.parser.GeoJsonGeometryParser;
import com.aashray.ingestion.validator.IngestionValidator;
import com.aashray.repository.AdminBoundaryRepository;
import com.aashray.repository.DataSourceRepository;
import com.aashray.repository.HabitationRepository;
import com.aashray.repository.InfrastructureRepository;
import com.aashray.repository.PopulationRepository;
import com.aashray.repository.RelocationSiteRepository;

@Component
public class CsvDataImporter implements DataImporter {

    private static final GeometryFactory GEOMETRY_FACTORY = new GeometryFactory(new PrecisionModel(), 4326);

    private final HabitationRepository habitationRepository;
    private final AdminBoundaryRepository adminBoundaryRepository;
    private final PopulationRepository populationRepository;
    private final InfrastructureRepository infrastructureRepository;
    private final RelocationSiteRepository relocationSiteRepository;
    private final DataSourceRepository dataSourceRepository;
    private final IngestionValidator validator;

    public CsvDataImporter(HabitationRepository habitationRepository,
                           AdminBoundaryRepository adminBoundaryRepository,
                           PopulationRepository populationRepository,
                           InfrastructureRepository infrastructureRepository,
                           RelocationSiteRepository relocationSiteRepository,
                           DataSourceRepository dataSourceRepository,
                           IngestionValidator validator) {
        this.habitationRepository = habitationRepository;
        this.adminBoundaryRepository = adminBoundaryRepository;
        this.populationRepository = populationRepository;
        this.infrastructureRepository = infrastructureRepository;
        this.relocationSiteRepository = relocationSiteRepository;
        this.dataSourceRepository = dataSourceRepository;
        this.validator = validator;
    }

    @Override
    public boolean supports(IngestionFormat format, IngestionTarget target) {
        if (format != IngestionFormat.CSV) {
            return false;
        }
        return target == null ||
                target == IngestionTarget.HABITATION ||
                target == IngestionTarget.POPULATION ||
                target == IngestionTarget.INFRASTRUCTURE ||
                target == IngestionTarget.ADMIN_BOUNDARY ||
                target == IngestionTarget.RELOCATION_SITE ||
                target == IngestionTarget.DATA_SOURCE;
    }

    @Override
    @Transactional
    public IngestionResult importData(String content, IngestionTarget target, Map<String, Object> options) {
        if (content == null || content.isBlank()) {
            return IngestionResult.failed(target, IngestionFormat.CSV,
                    "CSV content must not be empty", List.of(IngestionError.general("Empty CSV content")));
        }

        CsvParseResult parseResult;
        try {
            parseResult = CsvParser.parse(content);
        } catch (IOException e) {
            return IngestionResult.failed(target, IngestionFormat.CSV,
                    "Failed to parse CSV: " + e.getMessage(), List.of(IngestionError.general(e.getMessage())));
        }

        if (parseResult.rows().isEmpty()) {
            return IngestionResult.failed(target, IngestionFormat.CSV,
                    "CSV contains no data rows", List.of(IngestionError.general("No data rows")));
        }

        IngestionTarget resolvedTarget = target != null ? target : inferTarget(parseResult.headers());
        if (resolvedTarget == null) {
            resolvedTarget = IngestionTarget.HABITATION;
        }

        List<IngestionError> errors = new ArrayList<>();
        List<UUID> savedIds = new ArrayList<>();
        Set<String> seenLgdCodes = new HashSet<>();

        for (CsvRow row : parseResult.rows()) {
            int rowNum = row.rowNumber();
            Map<String, String> values = row.values();

            switch (resolvedTarget) {
                case HABITATION -> processHabitation(values, rowNum, seenLgdCodes, errors, savedIds);
                case POPULATION -> processPopulation(values, rowNum, errors, savedIds);
                case INFRASTRUCTURE -> processInfrastructure(values, rowNum, errors, savedIds);
                case ADMIN_BOUNDARY -> processAdminBoundary(values, rowNum, errors, savedIds);
                case RELOCATION_SITE -> processRelocationSite(values, rowNum, errors, savedIds, options);
                case DATA_SOURCE -> processDataSource(values, rowNum, errors, savedIds);
                default -> errors.add(IngestionError.row(rowNum, "target", "Unsupported CSV target: " + resolvedTarget, resolvedTarget));
            }
        }

        if (!errors.isEmpty()) {
            IngestionResult result = IngestionResult.failed(resolvedTarget, IngestionFormat.CSV,
                    "Validation errors occurred during CSV ingestion", errors);
            result.setImportedIds(savedIds);
            result.setTotalRecords(parseResult.rows().size());
            result.setImportedCount(savedIds.size());
            result.setFailedCount(errors.size());
            if (!savedIds.isEmpty()) {
                result.setStatus(IngestionStatus.PARTIAL_SUCCESS);
            }
            return result;
        }

        return IngestionResult.success(resolvedTarget, IngestionFormat.CSV, savedIds.size(), savedIds);
    }

    private IngestionTarget inferTarget(List<String> headers) {
        Set<String> lower = new HashSet<>();
        for (String h : headers) {
            lower.add(h.toLowerCase().trim());
        }
        if (lower.contains("population_count") || lower.contains("population") || lower.contains("year")) {
            return IngestionTarget.POPULATION;
        }
        if (lower.contains("infrastructure_type") || lower.contains("infra_type")) {
            return IngestionTarget.INFRASTRUCTURE;
        }
        if (lower.contains("boundary_type")) {
            return IngestionTarget.ADMIN_BOUNDARY;
        }
        if (lower.contains("suitability_score") && lower.contains("status")) {
            return IngestionTarget.RELOCATION_SITE;
        }
        if (lower.contains("provider") && lower.contains("dataset")) {
            return IngestionTarget.DATA_SOURCE;
        }
        return IngestionTarget.HABITATION;
    }

    private void processHabitation(Map<String, String> values, int rowNumber, Set<String> seenLgdCodes,
                                   List<IngestionError> errors, List<UUID> savedIds) {
        String name = getField(values, "name", "habitation_name", "village_name");
        if (name == null || name.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "name", "name is required for HABITATION", null));
            return;
        }

        String lgdCode = getField(values, "lgd_code", "lgdcode", "code");
        if (lgdCode != null && !lgdCode.isBlank()) {
            if (seenLgdCodes.contains(lgdCode)) {
                errors.add(IngestionError.row(rowNumber, "lgd_code", "Duplicate lgd_code in CSV payload: " + lgdCode, lgdCode));
                return;
            }
            seenLgdCodes.add(lgdCode);
        }

        AdminBoundary adminBoundary = null;
        String boundaryName = getField(values, "admin_boundary_name", "admin_boundary", "district", "taluk", "block");
        if (boundaryName != null && !boundaryName.isBlank()) {
            adminBoundary = adminBoundaryRepository.findByName(boundaryName).orElse(null);
        }

        Polygon polygon = parsePolygonFromValues(values, rowNumber, errors);
        if (polygon == null) {
            return;
        }

        List<IngestionError> geomErrors = validator.validateGeometry(polygon, IngestionTarget.HABITATION, rowNumber);
        if (!geomErrors.isEmpty()) {
            errors.addAll(geomErrors);
            return;
        }

        if (adminBoundary == null) {
            adminBoundary = adminBoundaryRepository.findByName("Default Admin Boundary")
                    .orElseGet(() -> {
                        AdminBoundary defaultBoundary = new AdminBoundary();
                        defaultBoundary.setName("Default Admin Boundary");
                        defaultBoundary.setBoundaryType("DISTRICT");
                        MultiPolygon mp = GeoJsonGeometryParser.toMultiPolygon(polygon);
                        defaultBoundary.setGeometry(mp);
                        defaultBoundary.setCreatedAt(OffsetDateTime.now());
                        defaultBoundary.setUpdatedAt(OffsetDateTime.now());
                        return adminBoundaryRepository.save(defaultBoundary);
                    });
        }

        Habitation habitation = null;
        if (lgdCode != null && !lgdCode.isBlank()) {
            habitation = habitationRepository.findByLgdCode(lgdCode).orElse(null);
        }
        if (habitation == null) {
            habitation = habitationRepository.findByName(name).orElseGet(Habitation::new);
        }

        habitation.setName(name);
        habitation.setLgdCode(lgdCode);
        habitation.setAdminBoundary(adminBoundary);
        habitation.setGeometry(polygon);

        OffsetDateTime now = OffsetDateTime.now();
        if (habitation.getCreatedAt() == null) {
            habitation.setCreatedAt(now);
        }
        habitation.setUpdatedAt(now);

        habitation = habitationRepository.save(habitation);
        savedIds.add(habitation.getId());
    }

    private void processPopulation(Map<String, String> values, int rowNumber,
                                   List<IngestionError> errors, List<UUID> savedIds) {
        String habName = getField(values, "habitation_name", "habitation", "village_name", "name");
        String lgdCode = getField(values, "lgd_code", "lgdcode");

        Habitation habitation = null;
        if (lgdCode != null && !lgdCode.isBlank()) {
            habitation = habitationRepository.findByLgdCode(lgdCode).orElse(null);
        }
        if (habitation == null && habName != null && !habName.isBlank()) {
            habitation = habitationRepository.findByName(habName).orElse(null);
        }
        if (habitation == null) {
            // Pick first habitation if available, else error
            List<Habitation> all = habitationRepository.findAll();
            if (!all.isEmpty()) {
                habitation = all.getFirst();
            } else {
                errors.add(IngestionError.row(rowNumber, "habitation", "Associated habitation not found", habName));
                return;
            }
        }

        String countStr = getField(values, "population_count", "population", "count");
        if (countStr == null || countStr.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "populationCount", "population_count is required", null));
            return;
        }

        Integer populationCount;
        try {
            populationCount = Integer.parseInt(countStr);
        } catch (NumberFormatException e) {
            errors.add(IngestionError.row(rowNumber, "populationCount", "population_count must be an integer: " + countStr, countStr));
            return;
        }

        errors.addAll(validator.validateNonNegativeInteger(populationCount, "populationCount", rowNumber));
        if (!errors.isEmpty()) {
            return;
        }

        String yearStr = getField(values, "year", "census_year");
        int year = 2026;
        if (yearStr != null && !yearStr.isBlank()) {
            try {
                year = Integer.parseInt(yearStr);
                errors.addAll(validator.validateYear(year, rowNumber));
                if (!errors.isEmpty()) {
                    return;
                }
            } catch (NumberFormatException e) {
                errors.add(IngestionError.row(rowNumber, "year", "year must be a valid 4-digit year: " + yearStr, yearStr));
                return;
            }
        }

        String source = getField(values, "source", "data_source", "source_name");

        Optional<Population> existing = populationRepository.findByHabitationAndYear(habitation, year);
        Population pop = existing.orElseGet(Population::new);
        pop.setHabitation(habitation);
        pop.setPopulationCount(populationCount);
        pop.setYear(year);
        pop.setSource(source);
        if (pop.getCreatedAt() == null) {
            pop.setCreatedAt(OffsetDateTime.now());
        }

        pop = populationRepository.save(pop);
        savedIds.add(pop.getId());
    }

    private void processInfrastructure(Map<String, String> values, int rowNumber,
                                       List<IngestionError> errors, List<UUID> savedIds) {
        String infraType = getField(values, "infrastructure_type", "type", "category");
        if (infraType == null || infraType.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "infrastructureType", "infrastructure_type is required", null));
            return;
        }

        String habName = getField(values, "habitation_name", "habitation", "village_name");
        String lgdCode = getField(values, "lgd_code", "lgdcode");

        Habitation habitation = null;
        if (lgdCode != null && !lgdCode.isBlank()) {
            habitation = habitationRepository.findByLgdCode(lgdCode).orElse(null);
        }
        if (habitation == null && habName != null && !habName.isBlank()) {
            habitation = habitationRepository.findByName(habName).orElse(null);
        }
        if (habitation == null) {
            List<Habitation> all = habitationRepository.findAll();
            if (!all.isEmpty()) {
                habitation = all.getFirst();
            } else {
                errors.add(IngestionError.row(rowNumber, "habitation", "Associated habitation not found", habName));
                return;
            }
        }

        Point point = parsePointFromValues(values, rowNumber, errors);
        if (point == null) {
            return;
        }

        List<IngestionError> geomErrors = validator.validateGeometry(point, IngestionTarget.INFRASTRUCTURE, rowNumber);
        if (!geomErrors.isEmpty()) {
            errors.addAll(geomErrors);
            return;
        }

        String status = getField(values, "status", "condition");
        String capStr = getField(values, "capacity");
        Integer capacity = null;
        if (capStr != null && !capStr.isBlank()) {
            try {
                capacity = Integer.parseInt(capStr);
                errors.addAll(validator.validateNonNegativeInteger(capacity, "capacity", rowNumber));
                if (!errors.isEmpty()) {
                    return;
                }
            } catch (NumberFormatException e) {
                errors.add(IngestionError.row(rowNumber, "capacity", "Invalid capacity integer: " + capStr, capStr));
                return;
            }
        }

        Infrastructure infra = new Infrastructure();
        infra.setHabitation(habitation);
        infra.setInfrastructureType(infraType);
        infra.setStatus(status);
        infra.setCapacity(capacity);
        infra.setGeometry(point);
        infra.setUpdatedAt(OffsetDateTime.now());

        infra = infrastructureRepository.save(infra);
        savedIds.add(infra.getId());
    }

    private void processAdminBoundary(Map<String, String> values, int rowNumber,
                                      List<IngestionError> errors, List<UUID> savedIds) {
        String name = getField(values, "name", "boundary_name");
        if (name == null || name.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "name", "name is required for ADMIN_BOUNDARY", null));
            return;
        }

        String boundaryType = getField(values, "boundary_type", "type");
        if (boundaryType == null || boundaryType.isBlank()) {
            boundaryType = "DISTRICT";
        }

        Polygon polygon = parsePolygonFromValues(values, rowNumber, errors);
        if (polygon == null) {
            return;
        }

        MultiPolygon multiPolygon = GeoJsonGeometryParser.toMultiPolygon(polygon);
        List<IngestionError> geomErrors = validator.validateGeometry(multiPolygon, IngestionTarget.ADMIN_BOUNDARY, rowNumber);
        if (!geomErrors.isEmpty()) {
            errors.addAll(geomErrors);
            return;
        }

        AdminBoundary boundary = adminBoundaryRepository.findByName(name).orElseGet(AdminBoundary::new);
        boundary.setName(name);
        boundary.setBoundaryType(boundaryType);
        boundary.setGeometry(multiPolygon);

        OffsetDateTime now = OffsetDateTime.now();
        if (boundary.getCreatedAt() == null) {
            boundary.setCreatedAt(now);
        }
        boundary.setUpdatedAt(now);

        String parentName = getField(values, "parent_boundary_name", "parent_name");
        if (parentName != null && !parentName.isBlank()) {
            adminBoundaryRepository.findByName(parentName).ifPresent(boundary::setParentBoundary);
        }

        boundary = adminBoundaryRepository.save(boundary);
        savedIds.add(boundary.getId());
    }

    private void processRelocationSite(Map<String, String> values, int rowNumber,
                                       List<IngestionError> errors, List<UUID> savedIds, Map<String, Object> options) {
        String name = getField(values, "name", "site_name");
        if (name == null || name.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "name", "name is required for RELOCATION_SITE", null));
            return;
        }

        String status = getField(values, "status");
        if (status == null || status.isBlank()) {
            status = "PROPOSED";
        }

        BigDecimal suitabilityScore = null;
        String scoreStr = getField(values, "suitability_score", "score");
        if (scoreStr != null && !scoreStr.isBlank()) {
            try {
                suitabilityScore = new BigDecimal(scoreStr);
                errors.addAll(validator.validateScore(suitabilityScore, "suitabilityScore", rowNumber));
                if (!errors.isEmpty()) {
                    return;
                }
            } catch (NumberFormatException e) {
                errors.add(IngestionError.row(rowNumber, "suitabilityScore", "Invalid numeric suitability score: " + scoreStr, scoreStr));
                return;
            }
        }

        Polygon polygon = parsePolygonFromValues(values, rowNumber, errors);
        if (polygon == null) {
            return;
        }

        List<IngestionError> geomErrors = validator.validateGeometry(polygon, IngestionTarget.RELOCATION_SITE, rowNumber);
        if (!geomErrors.isEmpty()) {
            errors.addAll(geomErrors);
            return;
        }

        RelocationSite site = relocationSiteRepository.findByName(name).orElseGet(RelocationSite::new);
        site.setName(name);
        site.setStatus(status);
        site.setSuitabilityScore(suitabilityScore);
        site.setGeometry(polygon);
        site.setUpdatedAt(OffsetDateTime.now());

        if (options != null && options.containsKey("dataSourceId")) {
            UUID dsId = (UUID) options.get("dataSourceId");
            dataSourceRepository.findById(dsId).ifPresent(site::setDataSource);
        }

        site = relocationSiteRepository.save(site);
        savedIds.add(site.getId());
    }

    private void processDataSource(Map<String, String> values, int rowNumber,
                                  List<IngestionError> errors, List<UUID> savedIds) {
        String provider = getField(values, "provider", "source_provider");
        String dataset = getField(values, "dataset", "dataset_name");

        if (provider == null || provider.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "provider", "provider is required for DATA_SOURCE", null));
            return;
        }
        if (dataset == null || dataset.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "dataset", "dataset is required for DATA_SOURCE", null));
            return;
        }

        String crs = getField(values, "crs");
        if (crs == null || crs.isBlank()) {
            crs = "EPSG:4326";
        }
        errors.addAll(validator.validateCrs(crs, rowNumber));
        if (!errors.isEmpty()) {
            return;
        }

        DataSource ds = dataSourceRepository.findByProviderAndDataset(provider, dataset).orElseGet(DataSource::new);
        ds.setProvider(provider);
        ds.setDataset(dataset);
        ds.setSourceType(getField(values, "source_type", "sourcetype"));
        ds.setCoverage(getField(values, "coverage"));
        ds.setResolution(getField(values, "resolution"));
        ds.setUrl(getField(values, "url", "file_path", "uri"));
        ds.setCrs(crs);
        ds.setLicense(getField(values, "license"));
        ds.setFreshnessClass(getField(values, "freshness_class", "freshnessclass"));
        ds.setNotes(getField(values, "notes", "description"));
        if (ds.getFetchTime() == null) {
            ds.setFetchTime(OffsetDateTime.now());
        }

        ds = dataSourceRepository.save(ds);
        savedIds.add(ds.getId());
    }

    private Polygon parsePolygonFromValues(Map<String, String> values, int rowNumber, List<IngestionError> errors) {
        String wkt = getField(values, "wkt_geometry", "wkt", "geometry", "geom");
        if (wkt != null && !wkt.isBlank()) {
            try {
                Geometry geom = GeoJsonGeometryParser.parseWkt(wkt);
                return GeoJsonGeometryParser.toPolygon(geom);
            } catch (Exception e) {
                errors.add(IngestionError.row(rowNumber, "wkt_geometry", "Invalid WKT polygon: " + e.getMessage(), wkt));
                return null;
            }
        }

        // Check for bounding box coordinates
        String minLonStr = getField(values, "min_lon", "min_longitude", "minlon", "west");
        String minLatStr = getField(values, "min_lat", "min_latitude", "minlat", "south");
        String maxLonStr = getField(values, "max_lon", "max_longitude", "maxlon", "east");
        String maxLatStr = getField(values, "max_lat", "max_latitude", "maxlat", "north");

        if (minLonStr != null && minLatStr != null && maxLonStr != null && maxLatStr != null) {
            try {
                double minLon = Double.parseDouble(minLonStr);
                double minLat = Double.parseDouble(minLatStr);
                double maxLon = Double.parseDouble(maxLonStr);
                double maxLat = Double.parseDouble(maxLatStr);

                Coordinate[] coords = new Coordinate[]{
                        new Coordinate(minLon, minLat),
                        new Coordinate(maxLon, minLat),
                        new Coordinate(maxLon, maxLat),
                        new Coordinate(minLon, maxLat),
                        new Coordinate(minLon, minLat)
                };
                Polygon poly = GEOMETRY_FACTORY.createPolygon(coords);
                poly.setSRID(4326);
                return poly;
            } catch (NumberFormatException e) {
                errors.add(IngestionError.row(rowNumber, "bbox", "Invalid numeric bounding box coordinates", minLonStr + "," + minLatStr));
                return null;
            }
        }

        // Check for center point and create a small default polygon buffer around it
        String lonStr = getField(values, "longitude", "lon", "lng", "x");
        String latStr = getField(values, "latitude", "lat", "y");
        if (lonStr != null && latStr != null) {
            try {
                double lon = Double.parseDouble(lonStr);
                double lat = Double.parseDouble(latStr);
                double delta = 0.005; // approx 500m box
                Coordinate[] coords = new Coordinate[]{
                        new Coordinate(lon - delta, lat - delta),
                        new Coordinate(lon + delta, lat - delta),
                        new Coordinate(lon + delta, lat + delta),
                        new Coordinate(lon - delta, lat + delta),
                        new Coordinate(lon - delta, lat - delta)
                };
                Polygon poly = GEOMETRY_FACTORY.createPolygon(coords);
                poly.setSRID(4326);
                return poly;
            } catch (NumberFormatException e) {
                errors.add(IngestionError.row(rowNumber, "coordinates", "Invalid numeric coordinates: " + lonStr + ", " + latStr, lonStr));
                return null;
            }
        }

        errors.add(IngestionError.row(rowNumber, "geometry", "Missing geometry (provide wkt_geometry, bbox, or lon/lat)", null));
        return null;
    }

    private Point parsePointFromValues(Map<String, String> values, int rowNumber, List<IngestionError> errors) {
        String wkt = getField(values, "wkt_geometry", "wkt", "geometry", "geom");
        if (wkt != null && !wkt.isBlank()) {
            try {
                Geometry geom = GeoJsonGeometryParser.parseWkt(wkt);
                if (geom instanceof Point pt) {
                    return pt;
                }
                errors.add(IngestionError.row(rowNumber, "wkt_geometry", "WKT geometry is not a Point: " + geom.getGeometryType(), wkt));
                return null;
            } catch (Exception e) {
                errors.add(IngestionError.row(rowNumber, "wkt_geometry", "Invalid WKT point: " + e.getMessage(), wkt));
                return null;
            }
        }

        String lonStr = getField(values, "longitude", "lon", "lng", "x");
        String latStr = getField(values, "latitude", "lat", "y");
        if (lonStr != null && latStr != null) {
            try {
                double lon = Double.parseDouble(lonStr);
                double lat = Double.parseDouble(latStr);
                Point point = GeoJsonGeometryParser.createPoint(lon, lat);
                return point;
            } catch (NumberFormatException e) {
                errors.add(IngestionError.row(rowNumber, "coordinates", "Invalid numeric coordinates: " + lonStr + ", " + latStr, lonStr));
                return null;
            }
        }

        errors.add(IngestionError.row(rowNumber, "geometry", "Point coordinates missing (provide longitude and latitude)", null));
        return null;
    }

    private String getField(Map<String, String> values, String... keys) {
        for (String k : keys) {
            if (values.containsKey(k) && !values.get(k).isBlank()) {
                return values.get(k);
            }
            if (values.containsKey(k.toLowerCase()) && !values.get(k.toLowerCase()).isBlank()) {
                return values.get(k.toLowerCase());
            }
        }
        return null;
    }
}
