package com.aashray.ingestion.importer;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

import org.locationtech.jts.geom.Geometry;
import org.locationtech.jts.geom.MultiPolygon;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.Polygon;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import com.aashray.entity.AdminBoundary;
import com.aashray.entity.DataSource;
import com.aashray.entity.Habitation;
import com.aashray.entity.Infrastructure;
import com.aashray.entity.RelocationSite;
import com.aashray.ingestion.model.IngestionError;
import com.aashray.ingestion.model.IngestionFormat;
import com.aashray.ingestion.model.IngestionResult;
import com.aashray.ingestion.model.IngestionStatus;
import com.aashray.ingestion.model.IngestionTarget;
import com.aashray.ingestion.parser.GeoJsonGeometryParser;
import com.aashray.ingestion.validator.IngestionValidator;
import com.aashray.repository.AdminBoundaryRepository;
import com.aashray.repository.DataSourceRepository;
import com.aashray.repository.HabitationRepository;
import com.aashray.repository.InfrastructureRepository;
import com.aashray.repository.RelocationSiteRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@Component
public class GeoJsonDataImporter implements DataImporter {

    private final HabitationRepository habitationRepository;
    private final AdminBoundaryRepository adminBoundaryRepository;
    private final RelocationSiteRepository relocationSiteRepository;
    private final InfrastructureRepository infrastructureRepository;
    private final DataSourceRepository dataSourceRepository;
    private final IngestionValidator validator;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public GeoJsonDataImporter(HabitationRepository habitationRepository,
                               AdminBoundaryRepository adminBoundaryRepository,
                               RelocationSiteRepository relocationSiteRepository,
                               InfrastructureRepository infrastructureRepository,
                               DataSourceRepository dataSourceRepository,
                               IngestionValidator validator) {
        this.habitationRepository = habitationRepository;
        this.adminBoundaryRepository = adminBoundaryRepository;
        this.relocationSiteRepository = relocationSiteRepository;
        this.infrastructureRepository = infrastructureRepository;
        this.dataSourceRepository = dataSourceRepository;
        this.validator = validator;
    }

    @Override
    public boolean supports(IngestionFormat format, IngestionTarget target) {
        if (format != IngestionFormat.GEOJSON) {
            return false;
        }
        return target == null ||
                target == IngestionTarget.HABITATION ||
                target == IngestionTarget.ADMIN_BOUNDARY ||
                target == IngestionTarget.RELOCATION_SITE ||
                target == IngestionTarget.INFRASTRUCTURE;
    }

    @Override
    @Transactional
    public IngestionResult importData(String content, IngestionTarget target, Map<String, Object> options) {
        if (content == null || content.isBlank()) {
            return IngestionResult.failed(target, IngestionFormat.GEOJSON,
                    "Payload must not be empty", List.of(IngestionError.general("Empty GeoJSON content")));
        }

        try {
            JsonNode root = objectMapper.readTree(content);

            // CRS check
            if (root.has("crs")) {
                JsonNode crsProps = root.get("crs").get("properties");
                if (crsProps != null && crsProps.has("name")) {
                    String crsName = crsProps.get("name").asText();
                    List<IngestionError> crsErrors = validator.validateCrs(crsName, 0);
                    if (!crsErrors.isEmpty()) {
                        return IngestionResult.failed(target, IngestionFormat.GEOJSON,
                                "Unsupported CRS in GeoJSON: " + crsName, crsErrors);
                    }
                }
            }

            List<JsonNode> featureNodes = new ArrayList<>();
            String rootType = root.has("type") ? root.get("type").asText() : "";
            if ("FeatureCollection".equalsIgnoreCase(rootType)) {
                JsonNode features = root.get("features");
                if (features != null && features.isArray()) {
                    features.forEach(featureNodes::add);
                }
            } else if ("Feature".equalsIgnoreCase(rootType)) {
                featureNodes.add(root);
            } else {
                // Raw Geometry
                featureNodes.add(root);
            }

            if (featureNodes.isEmpty()) {
                return IngestionResult.failed(target, IngestionFormat.GEOJSON,
                        "No features found in GeoJSON payload", List.of(IngestionError.general("Feature collection is empty")));
            }

            // Determine target if not explicitly passed
            IngestionTarget resolvedTarget = target != null ? target : inferTarget(featureNodes.getFirst());
            if (resolvedTarget == null) {
                resolvedTarget = IngestionTarget.HABITATION;
            }

            List<IngestionError> errors = new ArrayList<>();
            List<UUID> savedIds = new ArrayList<>();
            Set<String> seenLgdCodes = new HashSet<>();

            for (int i = 0; i < featureNodes.size(); i++) {
                int rowNumber = i + 1;
                JsonNode feat = featureNodes.get(i);

                JsonNode geomNode = feat.has("geometry") ? feat.get("geometry") : feat;
                JsonNode propsNode = feat.has("properties") ? feat.get("properties") : objectMapper.createObjectNode();

                if (geomNode == null || geomNode.isNull()) {
                    errors.add(IngestionError.row(rowNumber, "geometry", "Feature missing geometry", null));
                    continue;
                }

                Geometry geometry;
                try {
                    geometry = GeoJsonGeometryParser.parseGeometryNode(geomNode);
                } catch (Exception e) {
                    errors.add(IngestionError.row(rowNumber, "geometry", "Failed to parse geometry: " + e.getMessage(), geomNode.toString()));
                    continue;
                }

                List<IngestionError> geomErrors = validator.validateGeometry(geometry, resolvedTarget, rowNumber);
                if (!geomErrors.isEmpty()) {
                    errors.addAll(geomErrors);
                    continue;
                }

                switch (resolvedTarget) {
                    case ADMIN_BOUNDARY -> processAdminBoundary(geometry, propsNode, rowNumber, errors, savedIds);
                    case HABITATION -> processHabitation(geometry, propsNode, rowNumber, seenLgdCodes, errors, savedIds);
                    case RELOCATION_SITE -> processRelocationSite(geometry, propsNode, rowNumber, errors, savedIds, options);
                    case INFRASTRUCTURE -> processInfrastructure(geometry, propsNode, rowNumber, errors, savedIds);
                    default -> errors.add(IngestionError.row(rowNumber, "target", "Unsupported GeoJSON target: " + resolvedTarget, resolvedTarget));
                }
            }

            if (!errors.isEmpty()) {
                IngestionResult result = IngestionResult.failed(resolvedTarget, IngestionFormat.GEOJSON,
                        "Validation errors occurred during GeoJSON ingestion", errors);
                result.setImportedIds(savedIds);
                result.setTotalRecords(featureNodes.size());
                result.setImportedCount(savedIds.size());
                result.setFailedCount(errors.size());
                if (!savedIds.isEmpty()) {
                    result.setStatus(IngestionStatus.PARTIAL_SUCCESS);
                }
                return result;
            }

            return IngestionResult.success(resolvedTarget, IngestionFormat.GEOJSON, savedIds.size(), savedIds);

        } catch (Exception e) {
            return IngestionResult.failed(target, IngestionFormat.GEOJSON,
                    "Failed to process GeoJSON: " + e.getMessage(),
                    List.of(IngestionError.general(e.getMessage())));
        }
    }

    private IngestionTarget inferTarget(JsonNode feature) {
        JsonNode props = feature.has("properties") ? feature.get("properties") : null;
        if (props != null) {
            if (props.has("boundaryType") || props.has("boundary_type")) {
                return IngestionTarget.ADMIN_BOUNDARY;
            }
            if (props.has("infrastructureType") || props.has("infrastructure_type")) {
                return IngestionTarget.INFRASTRUCTURE;
            }
            if (props.has("suitabilityScore") || props.has("suitability_score")) {
                return IngestionTarget.RELOCATION_SITE;
            }
        }
        return IngestionTarget.HABITATION;
    }

    private void processAdminBoundary(Geometry geometry, JsonNode props, int rowNumber,
                                      List<IngestionError> errors, List<UUID> savedIds) {
        String name = getProperty(props, "name");
        if (name == null || name.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "name", "name is required for ADMIN_BOUNDARY", null));
            return;
        }

        String boundaryType = getProperty(props, "boundary_type", "boundaryType");
        if (boundaryType == null || boundaryType.isBlank()) {
            boundaryType = "VILLAGE";
        }

        MultiPolygon multiPolygon = GeoJsonGeometryParser.toMultiPolygon(geometry);

        AdminBoundary boundary = adminBoundaryRepository.findByName(name).orElseGet(AdminBoundary::new);
        boundary.setName(name);
        boundary.setBoundaryType(boundaryType);
        boundary.setGeometry(multiPolygon);

        OffsetDateTime now = OffsetDateTime.now();
        if (boundary.getCreatedAt() == null) {
            boundary.setCreatedAt(now);
        }
        boundary.setUpdatedAt(now);

        String parentName = getProperty(props, "parent_boundary_name", "parentBoundaryName");
        if (parentName != null && !parentName.isBlank()) {
            adminBoundaryRepository.findByName(parentName).ifPresent(boundary::setParentBoundary);
        }

        boundary = adminBoundaryRepository.save(boundary);
        savedIds.add(boundary.getId());
    }

    private void processHabitation(Geometry geometry, JsonNode props, int rowNumber, Set<String> seenLgdCodes,
                                   List<IngestionError> errors, List<UUID> savedIds) {
        String name = getProperty(props, "name");
        if (name == null || name.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "name", "name is required for HABITATION", null));
            return;
        }

        String lgdCode = getProperty(props, "lgd_code", "lgdCode");
        if (lgdCode != null && !lgdCode.isBlank()) {
            if (seenLgdCodes.contains(lgdCode)) {
                errors.add(IngestionError.row(rowNumber, "lgd_code", "Duplicate lgd_code in payload: " + lgdCode, lgdCode));
                return;
            }
            seenLgdCodes.add(lgdCode);
        }

        AdminBoundary adminBoundary = null;
        String boundaryName = getProperty(props, "admin_boundary_name", "adminBoundaryName", "district", "taluk", "block");
        if (boundaryName != null && !boundaryName.isBlank()) {
            adminBoundary = adminBoundaryRepository.findByName(boundaryName).orElse(null);
        }

        if (adminBoundary == null) {
            // Find or create default admin boundary for development seeding
            adminBoundary = adminBoundaryRepository.findByName("Default Admin Boundary")
                    .orElseGet(() -> {
                        AdminBoundary defaultBoundary = new AdminBoundary();
                        defaultBoundary.setName("Default Admin Boundary");
                        defaultBoundary.setBoundaryType("DISTRICT");
                        MultiPolygon mp = GeoJsonGeometryParser.toMultiPolygon(geometry);
                        defaultBoundary.setGeometry(mp);
                        defaultBoundary.setCreatedAt(OffsetDateTime.now());
                        defaultBoundary.setUpdatedAt(OffsetDateTime.now());
                        return adminBoundaryRepository.save(defaultBoundary);
                    });
        }

        Polygon polygon;
        try {
            polygon = GeoJsonGeometryParser.toPolygon(geometry);
        } catch (Exception e) {
            errors.add(IngestionError.row(rowNumber, "geometry", "Habitation requires a Polygon: " + e.getMessage(), geometry.getGeometryType()));
            return;
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

    private void processRelocationSite(Geometry geometry, JsonNode props, int rowNumber,
                                       List<IngestionError> errors, List<UUID> savedIds, Map<String, Object> options) {
        String name = getProperty(props, "name");
        if (name == null || name.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "name", "name is required for RELOCATION_SITE", null));
            return;
        }

        String status = getProperty(props, "status");
        if (status == null || status.isBlank()) {
            status = "PROPOSED";
        }

        BigDecimal suitabilityScore = null;
        String scoreStr = getProperty(props, "suitability_score", "suitabilityScore", "score");
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

        Polygon polygon;
        try {
            polygon = GeoJsonGeometryParser.toPolygon(geometry);
        } catch (Exception e) {
            errors.add(IngestionError.row(rowNumber, "geometry", "RelocationSite requires a Polygon: " + e.getMessage(), geometry.getGeometryType()));
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

    private void processInfrastructure(Geometry geometry, JsonNode props, int rowNumber,
                                       List<IngestionError> errors, List<UUID> savedIds) {
        if (!(geometry instanceof Point point)) {
            errors.add(IngestionError.row(rowNumber, "geometry", "Infrastructure requires a Point geometry", geometry.getGeometryType()));
            return;
        }

        String infraType = getProperty(props, "infrastructure_type", "infrastructureType", "type");
        if (infraType == null || infraType.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "infrastructureType", "infrastructure_type is required", null));
            return;
        }

        String habitationName = getProperty(props, "habitation_name", "habitationName", "habitation");
        String lgdCode = getProperty(props, "lgd_code", "lgdCode");

        Habitation habitation = null;
        if (lgdCode != null && !lgdCode.isBlank()) {
            habitation = habitationRepository.findByLgdCode(lgdCode).orElse(null);
        }
        if (habitation == null && habitationName != null && !habitationName.isBlank()) {
            habitation = habitationRepository.findByName(habitationName).orElse(null);
        }
        if (habitation == null) {
            // Pick first habitation if exists, or fail
            List<Habitation> all = habitationRepository.findAll();
            if (!all.isEmpty()) {
                habitation = all.getFirst();
            } else {
                errors.add(IngestionError.row(rowNumber, "habitation", "Associated habitation not found", habitationName));
                return;
            }
        }

        String status = getProperty(props, "status");
        Integer capacity = null;
        String capStr = getProperty(props, "capacity");
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

    private String getProperty(JsonNode props, String... keys) {
        if (props == null || props.isNull()) {
            return null;
        }
        for (String key : keys) {
            if (props.hasNonNull(key)) {
                return props.get(key).asText().trim();
            }
            if (props.hasNonNull(key.toLowerCase())) {
                return props.get(key.toLowerCase()).asText().trim();
            }
        }
        return null;
    }
}
