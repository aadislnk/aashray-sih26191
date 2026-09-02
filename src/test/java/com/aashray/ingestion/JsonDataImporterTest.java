package com.aashray.ingestion;

import java.util.Collections;
import java.util.Optional;
import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.aashray.entity.Habitation;
import com.aashray.entity.RiskAssessment;
import com.aashray.entity.Vulnerability;
import com.aashray.ingestion.importer.JsonDataImporter;
import com.aashray.ingestion.model.IngestionResult;
import com.aashray.ingestion.model.IngestionStatus;
import com.aashray.ingestion.model.IngestionTarget;
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

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class JsonDataImporterTest {

    @Mock
    private HabitationRepository habitationRepository;
    @Mock
    private AdminBoundaryRepository adminBoundaryRepository;
    @Mock
    private PopulationRepository populationRepository;
    @Mock
    private InfrastructureRepository infrastructureRepository;
    @Mock
    private RelocationSiteRepository relocationSiteRepository;
    @Mock
    private CarryingCapacityRepository carryingCapacityRepository;
    @Mock
    private VulnerabilityRepository vulnerabilityRepository;
    @Mock
    private HazardAssessmentRepository hazardAssessmentRepository;
    @Mock
    private RiskAssessmentRepository riskAssessmentRepository;
    @Mock
    private ModelVersionRepository modelVersionRepository;
    @Mock
    private DataSourceRepository dataSourceRepository;

    private IngestionValidator validator;
    private JsonDataImporter jsonDataImporter;

    @BeforeEach
    void setUp() {
        validator = new IngestionValidator();
        jsonDataImporter = new JsonDataImporter(
                habitationRepository,
                adminBoundaryRepository,
                populationRepository,
                infrastructureRepository,
                relocationSiteRepository,
                carryingCapacityRepository,
                vulnerabilityRepository,
                hazardAssessmentRepository,
                riskAssessmentRepository,
                modelVersionRepository,
                dataSourceRepository,
                validator
        );
    }

    @Test
    @DisplayName("Should import valid Vulnerability JSON array")
    void testValidVulnerabilityJson() {
        String json = """
                [
                  {
                    "habitationName": "North Village",
                    "hviScore": 0.72,
                    "exposureScore": 0.85,
                    "copingCapacity": 0.40,
                    "assessmentYear": 2026,
                    "componentData": { "floodDepth": 1.2, "roadAccess": false }
                  }
                ]
                """;

        Habitation hab = new Habitation();
        hab.setName("North Village");
        hab.setId(UUID.randomUUID());
        when(habitationRepository.findByName("North Village")).thenReturn(Optional.of(hab));
        when(vulnerabilityRepository.save(any(Vulnerability.class))).thenAnswer(inv -> {
            Vulnerability v = inv.getArgument(0);
            v.setId(UUID.randomUUID());
            return v;
        });

        IngestionResult result = jsonDataImporter.importData(json, IngestionTarget.VULNERABILITY, Collections.emptyMap());

        assertThat(result.getStatus()).isEqualTo(IngestionStatus.SUCCESS);
        assertThat(result.getImportedCount()).isEqualTo(1);
    }

    @Test
    @DisplayName("Should import valid RiskAssessment JSON array")
    void testValidRiskAssessmentJson() {
        String json = """
                [
                  {
                    "habitationName": "North Village",
                    "riskScore": 0.81,
                    "riskBand": "HIGH",
                    "priority": "URGENT",
                    "confidence": 0.92
                  }
                ]
                """;

        Habitation hab = new Habitation();
        hab.setName("North Village");
        hab.setId(UUID.randomUUID());
        when(habitationRepository.findByName("North Village")).thenReturn(Optional.of(hab));
        when(riskAssessmentRepository.save(any(RiskAssessment.class))).thenAnswer(inv -> {
            RiskAssessment ra = inv.getArgument(0);
            ra.setId(UUID.randomUUID());
            return ra;
        });

        IngestionResult result = jsonDataImporter.importData(json, IngestionTarget.RISK_ASSESSMENT, Collections.emptyMap());

        assertThat(result.getStatus()).isEqualTo(IngestionStatus.SUCCESS);
        assertThat(result.getImportedCount()).isEqualTo(1);
    }

    @Test
    @DisplayName("Should reject malformed JSON payload")
    void testMalformedJson() {
        String badJson = "{ invalid json structure ...";

        IngestionResult result = jsonDataImporter.importData(badJson, IngestionTarget.VULNERABILITY, Collections.emptyMap());

        assertThat(result.getStatus()).isEqualTo(IngestionStatus.FAILED);
        assertThat(result.getMessage()).contains("Failed to process JSON payload");
    }

    @Test
    @DisplayName("Should reject out-of-range risk score")
    void testInvalidScoreRange() {
        String json = """
                [
                  {
                    "habitationName": "North Village",
                    "riskScore": 250.0,
                    "riskBand": "HIGH",
                    "priority": "URGENT"
                  }
                ]
                """;

        Habitation hab = new Habitation();
        hab.setName("North Village");
        hab.setId(UUID.randomUUID());
        when(habitationRepository.findByName("North Village")).thenReturn(Optional.of(hab));

        IngestionResult result = jsonDataImporter.importData(json, IngestionTarget.RISK_ASSESSMENT, Collections.emptyMap());

        assertThat(result.getStatus()).isEqualTo(IngestionStatus.FAILED);
        assertThat(result.getErrors()).anyMatch(e -> "riskScore".equals(e.field()));
    }
}
