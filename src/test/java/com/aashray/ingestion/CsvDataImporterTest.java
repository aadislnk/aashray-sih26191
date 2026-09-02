package com.aashray.ingestion;

import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.aashray.entity.AdminBoundary;
import com.aashray.entity.Habitation;
import com.aashray.entity.Infrastructure;
import com.aashray.entity.Population;
import com.aashray.ingestion.importer.CsvDataImporter;
import com.aashray.ingestion.model.IngestionResult;
import com.aashray.ingestion.model.IngestionStatus;
import com.aashray.ingestion.model.IngestionTarget;
import com.aashray.ingestion.validator.IngestionValidator;
import com.aashray.repository.AdminBoundaryRepository;
import com.aashray.repository.DataSourceRepository;
import com.aashray.repository.HabitationRepository;
import com.aashray.repository.InfrastructureRepository;
import com.aashray.repository.PopulationRepository;
import com.aashray.repository.RelocationSiteRepository;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class CsvDataImporterTest {

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
    private DataSourceRepository dataSourceRepository;

    private IngestionValidator validator;
    private CsvDataImporter csvDataImporter;

    @BeforeEach
    void setUp() {
        validator = new IngestionValidator();
        csvDataImporter = new CsvDataImporter(
                habitationRepository,
                adminBoundaryRepository,
                populationRepository,
                infrastructureRepository,
                relocationSiteRepository,
                dataSourceRepository,
                validator
        );
    }

    @Test
    @DisplayName("Should successfully import valid Habitation CSV with bounding box coordinates")
    void testValidHabitationCsvImport() {
        String csv = """
                name,lgd_code,min_lon,min_lat,max_lon,max_lat
                "East Village","LGD001",77.50,12.90,77.55,12.95
                "West Village","LGD002",77.60,12.90,77.65,12.95
                """;

        when(habitationRepository.findByLgdCode(any())).thenReturn(Optional.empty());
        when(habitationRepository.findByName(any())).thenReturn(Optional.empty());
        when(adminBoundaryRepository.findByName(any())).thenReturn(Optional.of(new AdminBoundary()));
        when(habitationRepository.save(any(Habitation.class))).thenAnswer(invocation -> {
            Habitation h = invocation.getArgument(0);
            h.setId(UUID.randomUUID());
            return h;
        });

        IngestionResult result = csvDataImporter.importData(csv, IngestionTarget.HABITATION, Collections.emptyMap());

        assertThat(result.getStatus()).isEqualTo(IngestionStatus.SUCCESS);
        assertThat(result.getImportedCount()).isEqualTo(2);
        assertThat(result.getErrors()).isEmpty();
        assertThat(result.getImportedIds()).hasSize(2);
    }

    @Test
    @DisplayName("Should detect duplicate LGD code within same CSV payload")
    void testDuplicateLgdCodeInCsv() {
        String csv = """
                name,lgd_code,min_lon,min_lat,max_lon,max_lat
                "Village 1","DUP001",77.50,12.90,77.55,12.95
                "Village 2","DUP001",77.60,12.90,77.65,12.95
                """;

        when(habitationRepository.findByLgdCode(any())).thenReturn(Optional.empty());
        when(habitationRepository.findByName(any())).thenReturn(Optional.empty());
        when(adminBoundaryRepository.findByName(any())).thenReturn(Optional.of(new AdminBoundary()));
        when(habitationRepository.save(any(Habitation.class))).thenAnswer(inv -> {
            Habitation h = inv.getArgument(0);
            h.setId(UUID.randomUUID());
            return h;
        });

        IngestionResult result = csvDataImporter.importData(csv, IngestionTarget.HABITATION, Collections.emptyMap());

        assertThat(result.getStatus()).isEqualTo(IngestionStatus.PARTIAL_SUCCESS);
        assertThat(result.getErrors()).hasSize(1);
        assertThat(result.getErrors().get(0).field()).isEqualTo("lgd_code");
        assertThat(result.getErrors().get(0).message()).contains("Duplicate lgd_code");
    }

    @Test
    @DisplayName("Should reject invalid negative population count in CSV")
    void testNegativePopulationCsv() {
        String csv = """
                habitation_name,population_count,year
                "East Village",-500,2026
                """;

        Habitation mockHab = new Habitation();
        mockHab.setName("East Village");
        mockHab.setId(UUID.randomUUID());
        when(habitationRepository.findByName("East Village")).thenReturn(Optional.of(mockHab));

        IngestionResult result = csvDataImporter.importData(csv, IngestionTarget.POPULATION, Collections.emptyMap());

        assertThat(result.getStatus()).isEqualTo(IngestionStatus.FAILED);
        assertThat(result.getErrors()).hasSize(1);
        assertThat(result.getErrors().get(0).field()).isEqualTo("populationCount");
        assertThat(result.getErrors().get(0).message()).contains("non-negative");
    }

    @Test
    @DisplayName("Should reject missing required field 'name' in Habitation CSV")
    void testMissingNameInHabitationCsv() {
        String csv = """
                name,lgd_code,min_lon,min_lat,max_lon,max_lat
                ,"LGD001",77.50,12.90,77.55,12.95
                """;

        IngestionResult result = csvDataImporter.importData(csv, IngestionTarget.HABITATION, Collections.emptyMap());

        assertThat(result.getStatus()).isEqualTo(IngestionStatus.FAILED);
        assertThat(result.getErrors()).hasSize(1);
        assertThat(result.getErrors().get(0).field()).isEqualTo("name");
    }
}
