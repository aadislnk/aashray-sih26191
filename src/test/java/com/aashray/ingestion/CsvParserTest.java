package com.aashray.ingestion;

import java.io.IOException;
import java.util.List;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.aashray.ingestion.parser.CsvParser;
import com.aashray.ingestion.parser.CsvParser.CsvParseResult;

import static org.assertj.core.api.Assertions.assertThat;

class CsvParserTest {

    @Test
    @DisplayName("Should parse standard CSV with headers and rows")
    void testStandardCsv() throws IOException {
        String csv = """
                name,lgd_code,population
                "Village East",1001,450
                "Village West",1002,320
                """;

        CsvParseResult result = CsvParser.parse(csv);

        assertThat(result.headers()).containsExactly("name", "lgd_code", "population");
        assertThat(result.rows()).hasSize(2);
        assertThat(result.rows().get(0).values().get("name")).isEqualTo("Village East");
        assertThat(result.rows().get(0).values().get("lgd_code")).isEqualTo("1001");
        assertThat(result.rows().get(0).values().get("population")).isEqualTo("450");
        assertThat(result.rows().get(1).values().get("name")).isEqualTo("Village West");
    }

    @Test
    @DisplayName("Should handle commas and quotes inside quoted fields")
    void testQuotedCommasAndEscapes() throws IOException {
        String csv = """
                name,notes
                "Village, North","Contains ""special"" area"
                """;

        CsvParseResult result = CsvParser.parse(csv);

        assertThat(result.rows()).hasSize(1);
        assertThat(result.rows().get(0).values().get("name")).isEqualTo("Village, North");
        assertThat(result.rows().get(0).values().get("notes")).isEqualTo("Contains \"special\" area");
    }

    @Test
    @DisplayName("Should handle empty and blank content gracefully")
    void testEmptyContent() throws IOException {
        CsvParseResult emptyResult = CsvParser.parse("");
        assertThat(emptyResult.rows()).isEmpty();
        assertThat(emptyResult.headers()).isEmpty();

        CsvParseResult nullResult = CsvParser.parse(null);
        assertThat(nullResult.rows()).isEmpty();
    }
}
