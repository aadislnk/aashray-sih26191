package com.aashray.ingestion.importer;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

import org.locationtech.jts.geom.Geometry;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.Polygon;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import com.aashray.entity.AdminBoundary;
import com.aashray.entity.CarryingCapacity;
import com.aashray.entity.DataSource;
import com.aashray.entity.Habitation;
import com.aashray.entity.HazardAssessment;
import com.aashray.entity.Infrastructure;
import com.aashray.entity.ModelVersion;
import com.aashray.entity.Population;
import com.aashray.entity.RelocationSite;
import com.aashray.entity.RiskAssessment;
import com.aashray.entity.Vulnerability;
import com.aashray.ingestion.model.IngestionError;
import com.aashray.ingestion.model.IngestionFormat;
import com.aashray.ingestion.model.IngestionResult;
import com.aashray.ingestion.model.IngestionStatus;
import com.aashray.ingestion.model.IngestionTarget;
import com.aashray.ingestion.parser.GeoJsonGeometryParser;
import com.aashray.ingestion.validator.IngestionValidator;
import com.aashray.repository.AdminBoundaryRepository;
import com.aashray.repository.CarryingCapacityRepository;
import com.aashray.repository.DataSourceRepository;
import com.aashray.repository.HabitationRepository;
import com.aashray.repository.HazardAssessmentRepository;
import com.aashray.repository.InfrastructureRepository;
import com.aashray.repository.ModelVersionRepository;
import com.aashray.repository.PopulationRepository;
import com.aashray.repository.RelocationSiteRepository;
import com.aashray.repository.RiskAssessmentRepository;
import com.aashray.repository.VulnerabilityRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@Component
public class JsonDataImporter implements DataImporter {

    private final HabitationRepository habitationRepository;
    private final AdminBoundaryRepository adminBoundaryRepository;
    private final PopulationRepository populationRepository;
    private final InfrastructureRepository infrastructureRepository;
    private final RelocationSiteRepository relocationSiteRepository;
    private final CarryingCapacityRepository carryingCapacityRepository;
    private final VulnerabilityRepository vulnerabilityRepository;
    private final HazardAssessmentRepository hazardAssessmentRepository;
    private final RiskAssessmentRepository riskAssessmentRepository;
    private final ModelVersionRepository modelVersionRepository;
    private final DataSourceRepository dataSourceRepository;
    private final IngestionValidator validator;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public JsonDataImporter(HabitationRepository habitationRepository,
                            AdminBoundaryRepository adminBoundaryRepository,
                            PopulationRepository populationRepository,
                            InfrastructureRepository infrastructureRepository,
                            RelocationSiteRepository relocationSiteRepository,
                            CarryingCapacityRepository carryingCapacityRepository,
                            VulnerabilityRepository vulnerabilityRepository,
                            HazardAssessmentRepository hazardAssessmentRepository,
                            RiskAssessmentRepository riskAssessmentRepository,
                            ModelVersionRepository modelVersionRepository,
                            DataSourceRepository dataSourceRepository,
                            IngestionValidator validator) {
        this.habitationRepository = habitationRepository;
        this.adminBoundaryRepository = adminBoundaryRepository;
        this.populationRepository = populationRepository;
        this.infrastructureRepository = infrastructureRepository;
        this.relocationSiteRepository = relocationSiteRepository;
        this.carryingCapacityRepository = carryingCapacityRepository;
        this.vulnerabilityRepository = vulnerabilityRepository;
        this.hazardAssessmentRepository = hazardAssessmentRepository;
        this.riskAssessmentRepository = riskAssessmentRepository;
        this.modelVersionRepository = modelVersionRepository;
        this.dataSourceRepository = dataSourceRepository;
        this.validator = validator;
    }

    @Override
    public boolean supports(IngestionFormat format, IngestionTarget target) {
        return format == IngestionFormat.JSON && target != null;
    }

    @Override
    @Transactional
    public IngestionResult importData(String content, IngestionTarget target, Map<String, Object> options) {
        if (content == null || content.isBlank()) {
            return IngestionResult.failed(target, IngestionFormat.JSON,
                    "JSON content must not be empty", List.of(IngestionError.general("Empty JSON content")));
        }

        try {
            JsonNode root = objectMapper.readTree(content);
            List<JsonNode> items = new ArrayList<>();
            if (root.isArray()) {
                root.forEach(items::add);
            } else {
                items.add(root);
            }

            if (items.isEmpty()) {
                return IngestionResult.failed(target, IngestionFormat.JSON,
                        "JSON array contains no items", List.of(IngestionError.general("Empty JSON array")));
            }

            List<IngestionError> errors = new ArrayList<>();
            List<UUID> savedIds = new ArrayList<>();
            Set<String> seenIdentifiers = new HashSet<>();

            for (int i = 0; i < items.size(); i++) {
                int rowNumber = i + 1;
                JsonNode node = items.get(i);

                switch (target) {
                    case HABITATION -> processHabitation(node, rowNumber, seenIdentifiers, errors, savedIds);
                    case POPULATION -> processPopulation(node, rowNumber, errors, savedIds);
                    case INFRASTRUCTURE -> processInfrastructure(node, rowNumber, errors, savedIds);
                    case RELOCATION_SITE -> processRelocationSite(node, rowNumber, errors, savedIds, options);
                    case CARRYING_CAPACITY -> processCarryingCapacity(node, rowNumber, errors, savedIds);
                    case VULNERABILITY -> processVulnerability(node, rowNumber, errors, savedIds);
                    case HAZARD_ASSESSMENT -> processHazardAssessment(node, rowNumber, errors, savedIds);
                    case RISK_ASSESSMENT -> processRiskAssessment(node, rowNumber, errors, savedIds);
                    case MODEL_VERSION -> processModelVersion(node, rowNumber, errors, savedIds);
                    default -> errors.add(IngestionError.row(rowNumber, "target", "Unsupported JSON target: " + target, target));
                }
            }

            if (!errors.isEmpty()) {
                IngestionResult result = IngestionResult.failed(target, IngestionFormat.JSON,
                        "Validation errors occurred during JSON ingestion", errors);
                result.setImportedIds(savedIds);
                result.setTotalRecords(items.size());
                result.setImportedCount(savedIds.size());
                result.setFailedCount(errors.size());
                if (!savedIds.isEmpty()) {
                    result.setStatus(IngestionStatus.PARTIAL_SUCCESS);
                }
                return result;
            }

            return IngestionResult.success(target, IngestionFormat.JSON, savedIds.size(), savedIds);

        } catch (Exception e) {
            return IngestionResult.failed(target, IngestionFormat.JSON,
                    "Failed to process JSON payload: " + e.getMessage(),
                    List.of(IngestionError.general(e.getMessage())));
        }
    }

    private void processHabitation(JsonNode node, int rowNumber, Set<String> seenIdentifiers,
                                   List<IngestionError> errors, List<UUID> savedIds) {
        String name = getText(node, "name");
        if (name == null || name.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "name", "name is required for HABITATION", null));
            return;
        }

        String lgdCode = getText(node, "lgdCode", "lgd_code");
        if (lgdCode != null && !lgdCode.isBlank()) {
            if (seenIdentifiers.contains(lgdCode)) {
                errors.add(IngestionError.row(rowNumber, "lgdCode", "Duplicate lgdCode in JSON payload: " + lgdCode, lgdCode));
                return;
            }
            seenIdentifiers.add(lgdCode);
        }

        Geometry geom = parseGeometry(node, rowNumber, errors);
        if (geom == null) {
            return;
        }

        Polygon polygon;
        try {
            polygon = GeoJsonGeometryParser.toPolygon(geom);
        } catch (Exception e) {
            errors.add(IngestionError.row(rowNumber, "geometry", "Habitation requires a Polygon: " + e.getMessage(), geom.getGeometryType()));
            return;
        }

        List<IngestionError> geomErrors = validator.validateGeometry(polygon, IngestionTarget.HABITATION, rowNumber);
        if (!geomErrors.isEmpty()) {
            errors.addAll(geomErrors);
            return;
        }

        AdminBoundary adminBoundary = null;
        String boundaryName = getText(node, "adminBoundaryName", "admin_boundary_name", "district");
        if (boundaryName != null && !boundaryName.isBlank()) {
            adminBoundary = adminBoundaryRepository.findByName(boundaryName).orElse(null);
        }
        if (adminBoundary == null) {
            adminBoundary = adminBoundaryRepository.findByName("Default Admin Boundary")
                    .orElseGet(() -> {
                        AdminBoundary defaultBoundary = new AdminBoundary();
                        defaultBoundary.setName("Default Admin Boundary");
                        defaultBoundary.setBoundaryType("DISTRICT");
                        defaultBoundary.setGeometry(GeoJsonGeometryParser.toMultiPolygon(polygon));
                        defaultBoundary.setCreatedAt(OffsetDateTime.now());
                        defaultBoundary.setUpdatedAt(OffsetDateTime.now());
                        return adminBoundaryRepository.save(defaultBoundary);
                    });
        }

        Habitation hab = null;
        if (lgdCode != null && !lgdCode.isBlank()) {
            hab = habitationRepository.findByLgdCode(lgdCode).orElse(null);
        }
        if (hab == null) {
            hab = habitationRepository.findByName(name).orElseGet(Habitation::new);
        }

        hab.setName(name);
        hab.setLgdCode(lgdCode);
        hab.setAdminBoundary(adminBoundary);
        hab.setGeometry(polygon);

        OffsetDateTime now = OffsetDateTime.now();
        if (hab.getCreatedAt() == null) {
            hab.setCreatedAt(now);
        }
        hab.setUpdatedAt(now);

        hab = habitationRepository.save(hab);
        savedIds.add(hab.getId());
    }

    private void processPopulation(JsonNode node, int rowNumber,
                                   List<IngestionError> errors, List<UUID> savedIds) {
        Habitation habitation = resolveHabitation(node, rowNumber, errors);
        if (habitation == null) {
            return;
        }

        if (!node.hasNonNull("populationCount") && !node.hasNonNull("population_count")) {
            errors.add(IngestionError.row(rowNumber, "populationCount", "populationCount is required", null));
            return;
        }

        int popCount = node.hasNonNull("populationCount") ? node.get("populationCount").asInt() : node.get("population_count").asInt();
        errors.addAll(validator.validateNonNegativeInteger(popCount, "populationCount", rowNumber));
        if (!errors.isEmpty()) {
            return;
        }

        int year = 2026;
        if (node.hasNonNull("year")) {
            year = node.get("year").asInt();
            errors.addAll(validator.validateYear(year, rowNumber));
            if (!errors.isEmpty()) {
                return;
            }
        }

        String source = getText(node, "source");

        Optional<Population> existing = populationRepository.findByHabitationAndYear(habitation, year);
        Population pop = existing.orElseGet(Population::new);
        pop.setHabitation(habitation);
        pop.setPopulationCount(popCount);
        pop.setYear(year);
        pop.setSource(source);
        if (pop.getCreatedAt() == null) {
            pop.setCreatedAt(OffsetDateTime.now());
        }

        pop = populationRepository.save(pop);
        savedIds.add(pop.getId());
    }

    private void processInfrastructure(JsonNode node, int rowNumber,
                                       List<IngestionError> errors, List<UUID> savedIds) {
        Habitation habitation = resolveHabitation(node, rowNumber, errors);
        if (habitation == null) {
            return;
        }

        String infraType = getText(node, "infrastructureType", "infrastructure_type", "type");
        if (infraType == null || infraType.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "infrastructureType", "infrastructureType is required", null));
            return;
        }

        Geometry geom = parseGeometry(node, rowNumber, errors);
        if (geom == null) {
            return;
        }
        if (!(geom instanceof Point point)) {
            errors.add(IngestionError.row(rowNumber, "geometry", "Infrastructure requires a Point geometry", geom.getGeometryType()));
            return;
        }

        errors.addAll(validator.validateGeometry(point, IngestionTarget.INFRASTRUCTURE, rowNumber));
        if (!errors.isEmpty()) {
            return;
        }

        Integer capacity = null;
        if (node.hasNonNull("capacity")) {
            capacity = node.get("capacity").asInt();
            errors.addAll(validator.validateNonNegativeInteger(capacity, "capacity", rowNumber));
            if (!errors.isEmpty()) {
                return;
            }
        }

        Infrastructure infra = new Infrastructure();
        infra.setHabitation(habitation);
        infra.setInfrastructureType(infraType);
        infra.setStatus(getText(node, "status"));
        infra.setCapacity(capacity);
        infra.setGeometry(point);
        infra.setUpdatedAt(OffsetDateTime.now());

        infra = infrastructureRepository.save(infra);
        savedIds.add(infra.getId());
    }

    private void processRelocationSite(JsonNode node, int rowNumber,
                                       List<IngestionError> errors, List<UUID> savedIds, Map<String, Object> options) {
        String name = getText(node, "name");
        if (name == null || name.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "name", "name is required for RELOCATION_SITE", null));
            return;
        }

        String status = getText(node, "status");
        if (status == null || status.isBlank()) {
            status = "PROPOSED";
        }

        BigDecimal suitabilityScore = null;
        if (node.hasNonNull("suitabilityScore") || node.hasNonNull("suitability_score")) {
            double score = node.hasNonNull("suitabilityScore") ? node.get("suitabilityScore").asDouble() : node.get("suitability_score").asDouble();
            suitabilityScore = BigDecimal.valueOf(score);
            errors.addAll(validator.validateScore(suitabilityScore, "suitabilityScore", rowNumber));
            if (!errors.isEmpty()) {
                return;
            }
        }

        Geometry geom = parseGeometry(node, rowNumber, errors);
        if (geom == null) {
            return;
        }

        Polygon polygon;
        try {
            polygon = GeoJsonGeometryParser.toPolygon(geom);
        } catch (Exception e) {
            errors.add(IngestionError.row(rowNumber, "geometry", "RelocationSite requires a Polygon: " + e.getMessage(), geom.getGeometryType()));
            return;
        }

        errors.addAll(validator.validateGeometry(polygon, IngestionTarget.RELOCATION_SITE, rowNumber));
        if (!errors.isEmpty()) {
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

    private void processCarryingCapacity(JsonNode node, int rowNumber,
                                         List<IngestionError> errors, List<UUID> savedIds) {
        String siteName = getText(node, "relocationSiteName", "relocation_site_name", "siteName");
        RelocationSite site = null;
        if (siteName != null && !siteName.isBlank()) {
            site = relocationSiteRepository.findByName(siteName).orElse(null);
        }
        if (site == null) {
            List<RelocationSite> sites = relocationSiteRepository.findAll();
            if (!sites.isEmpty()) {
                site = sites.getFirst();
            } else {
                errors.add(IngestionError.row(rowNumber, "relocationSite", "Relocation site not found: " + siteName, siteName));
                return;
            }
        }

        if (!node.hasNonNull("totalCapacity") && !node.hasNonNull("total_capacity")) {
            errors.add(IngestionError.row(rowNumber, "totalCapacity", "totalCapacity is required", null));
            return;
        }

        int totalCap = node.hasNonNull("totalCapacity") ? node.get("totalCapacity").asInt() : node.get("total_capacity").asInt();
        errors.addAll(validator.validateNonNegativeInteger(totalCap, "totalCapacity", rowNumber));

        Integer estimatedCap = null;
        if (node.hasNonNull("estimatedCapacity") || node.hasNonNull("estimated_capacity")) {
            estimatedCap = node.hasNonNull("estimatedCapacity") ? node.get("estimatedCapacity").asInt() : node.get("estimated_capacity").asInt();
            errors.addAll(validator.validateNonNegativeInteger(estimatedCap, "estimatedCapacity", rowNumber));
        }

        if (!errors.isEmpty()) {
            return;
        }

        CarryingCapacity cc = new CarryingCapacity();
        cc.setRelocationSite(site);
        cc.setTotalCapacity(totalCap);
        cc.setEstimatedCapacity(estimatedCap);
        cc.setBindingSector(getText(node, "bindingSector", "binding_sector"));
        cc.setCalculatedAt(OffsetDateTime.now());

        cc = carryingCapacityRepository.save(cc);
        savedIds.add(cc.getId());
    }

    private void processVulnerability(JsonNode node, int rowNumber,
                                      List<IngestionError> errors, List<UUID> savedIds) {
        Habitation habitation = resolveHabitation(node, rowNumber, errors);
        if (habitation == null) {
            return;
        }

        BigDecimal hviScore = getDecimal(node, "hviScore", "hvi_score");
        BigDecimal expScore = getDecimal(node, "exposureScore", "exposure_score");
        BigDecimal copingCap = getDecimal(node, "copingCapacity", "coping_capacity");

        errors.addAll(validator.validateScore(hviScore, "hviScore", rowNumber));
        errors.addAll(validator.validateScore(expScore, "exposureScore", rowNumber));
        errors.addAll(validator.validateScore(copingCap, "copingCapacity", rowNumber));
        if (!errors.isEmpty()) {
            return;
        }

        Integer assessmentYear = null;
        if (node.hasNonNull("assessmentYear") || node.hasNonNull("assessment_year")) {
            assessmentYear = node.hasNonNull("assessmentYear") ? node.get("assessmentYear").asInt() : node.get("assessment_year").asInt();
            errors.addAll(validator.validateYear(assessmentYear, rowNumber));
            if (!errors.isEmpty()) {
                return;
            }
        }

        Map<String, Object> componentData = null;
        if (node.hasNonNull("componentData") || node.hasNonNull("component_data")) {
            JsonNode compNode = node.hasNonNull("componentData") ? node.get("componentData") : node.get("component_data");
            componentData = objectMapper.convertValue(compNode, new TypeReference<Map<String, Object>>() {});
        }

        Vulnerability vuln = new Vulnerability();
        vuln.setHabitation(habitation);
        vuln.setHviScore(hviScore);
        vuln.setExposureScore(expScore);
        vuln.setCopingCapacity(copingCap);
        vuln.setComponentData(componentData);
        vuln.setAssessmentYear(assessmentYear != null ? assessmentYear : 2026);

        vuln = vulnerabilityRepository.save(vuln);
        savedIds.add(vuln.getId());
    }

    private void processHazardAssessment(JsonNode node, int rowNumber,
                                         List<IngestionError> errors, List<UUID> savedIds) {
        Habitation habitation = resolveHabitation(node, rowNumber, errors);
        if (habitation == null) {
            return;
        }

        String hazardType = getText(node, "hazardType", "hazard_type");
        if (hazardType == null || hazardType.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "hazardType", "hazardType is required", null));
            return;
        }

        BigDecimal susceptibility = getDecimal(node, "susceptibility");
        BigDecimal exposure = getDecimal(node, "exposure");
        BigDecimal confidence = getDecimal(node, "confidence");

        errors.addAll(validator.validateScore(susceptibility, "susceptibility", rowNumber));
        errors.addAll(validator.validateScore(exposure, "exposure", rowNumber));
        errors.addAll(validator.validateScore(confidence, "confidence", rowNumber));
        if (!errors.isEmpty()) {
            return;
        }

        boolean applicable = node.has("applicable") ? node.get("applicable").asBoolean(true) : true;

        HazardAssessment ha = new HazardAssessment();
        ha.setHabitation(habitation);
        ha.setHazardType(hazardType);
        ha.setSusceptibility(susceptibility);
        ha.setExposure(exposure);
        ha.setConfidence(confidence);
        ha.setApplicable(applicable);
        ha.setAssessmentTime(OffsetDateTime.now());

        ha = hazardAssessmentRepository.save(ha);
        savedIds.add(ha.getId());
    }

    private void processRiskAssessment(JsonNode node, int rowNumber,
                                       List<IngestionError> errors, List<UUID> savedIds) {
        Habitation habitation = resolveHabitation(node, rowNumber, errors);
        if (habitation == null) {
            return;
        }

        BigDecimal riskScore = getDecimal(node, "riskScore", "risk_score");
        if (riskScore == null) {
            errors.add(IngestionError.row(rowNumber, "riskScore", "riskScore is required", null));
            return;
        }
        errors.addAll(validator.validateScore(riskScore, "riskScore", rowNumber));

        String riskBand = getText(node, "riskBand", "risk_band");
        if (riskBand == null || riskBand.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "riskBand", "riskBand is required", null));
            return;
        }

        String priority = getText(node, "priority");
        if (priority == null || priority.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "priority", "priority is required", null));
            return;
        }

        BigDecimal confidence = getDecimal(node, "confidence");
        errors.addAll(validator.validateScore(confidence, "confidence", rowNumber));

        if (!errors.isEmpty()) {
            return;
        }

        RiskAssessment ra = new RiskAssessment();
        ra.setHabitation(habitation);
        ra.setRiskScore(riskScore);
        ra.setRiskBand(riskBand);
        ra.setPriority(priority);
        ra.setConfidence(confidence);
        ra.setAssessmentTime(OffsetDateTime.now());

        ra = riskAssessmentRepository.save(ra);
        savedIds.add(ra.getId());
    }

    private void processModelVersion(JsonNode node, int rowNumber,
                                     List<IngestionError> errors, List<UUID> savedIds) {
        String modelName = getText(node, "modelName", "model_name");
        if (modelName == null || modelName.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "modelName", "modelName is required", null));
            return;
        }

        String version = getText(node, "version");
        if (version == null || version.isBlank()) {
            errors.add(IngestionError.row(rowNumber, "version", "version is required", null));
            return;
        }

        Map<String, Object> params = null;
        if (node.hasNonNull("parameters")) {
            params = objectMapper.convertValue(node.get("parameters"), new TypeReference<Map<String, Object>>() {});
        }

        Map<String, Object> metrics = null;
        if (node.hasNonNull("validationMetrics") || node.hasNonNull("validation_metrics")) {
            JsonNode mNode = node.hasNonNull("validationMetrics") ? node.get("validationMetrics") : node.get("validation_metrics");
            metrics = objectMapper.convertValue(mNode, new TypeReference<Map<String, Object>>() {});
        }

        ModelVersion mv = modelVersionRepository.findByModelNameAndVersion(modelName, version)
                .orElseGet(ModelVersion::new);
        mv.setModelName(modelName);
        mv.setVersion(version);
        mv.setParameters(params);
        mv.setValidationMetrics(metrics);
        if (mv.getCreatedAt() == null) {
            mv.setCreatedAt(OffsetDateTime.now());
        }

        mv = modelVersionRepository.save(mv);
        savedIds.add(mv.getId());
    }

    private Habitation resolveHabitation(JsonNode node, int rowNumber, List<IngestionError> errors) {
        String habName = getText(node, "habitationName", "habitation_name", "habitation");
        String lgdCode = getText(node, "lgdCode", "lgd_code");

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
                return null;
            }
        }
        return habitation;
    }

    private Geometry parseGeometry(JsonNode node, int rowNumber, List<IngestionError> errors) {
        if (node.has("geometry")) {
            try {
                return GeoJsonGeometryParser.parseGeometryNode(node.get("geometry"));
            } catch (Exception e) {
                errors.add(IngestionError.row(rowNumber, "geometry", "Invalid geometry: " + e.getMessage(), node.get("geometry").toString()));
                return null;
            }
        }

        if (node.hasNonNull("wkt") || node.hasNonNull("wkt_geometry")) {
            String wkt = node.hasNonNull("wkt") ? node.get("wkt").asText() : node.get("wkt_geometry").asText();
            try {
                return GeoJsonGeometryParser.parseWkt(wkt);
            } catch (Exception e) {
                errors.add(IngestionError.row(rowNumber, "wkt", "Invalid WKT: " + e.getMessage(), wkt));
                return null;
            }
        }

        if (node.hasNonNull("longitude") && node.hasNonNull("latitude")) {
            double lon = node.get("longitude").asDouble();
            double lat = node.get("latitude").asDouble();
            return GeoJsonGeometryParser.createPoint(lon, lat);
        }

        errors.add(IngestionError.row(rowNumber, "geometry", "Missing geometry or coordinates", null));
        return null;
    }

    private String getText(JsonNode node, String... keys) {
        for (String key : keys) {
            if (node.hasNonNull(key)) {
                return node.get(key).asText().trim();
            }
        }
        return null;
    }

    private BigDecimal getDecimal(JsonNode node, String... keys) {
        for (String key : keys) {
            if (node.hasNonNull(key)) {
                return BigDecimal.valueOf(node.get(key).asDouble());
            }
        }
        return null;
    }
}
