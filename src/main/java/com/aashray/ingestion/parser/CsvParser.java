package com.aashray.ingestion.parser;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class CsvParser {

    public record CsvRow(int rowNumber, Map<String, String> values, List<String> rawColumns) {}

    public record CsvParseResult(List<String> headers, List<CsvRow> rows) {}

    public static CsvParseResult parse(String csvContent) throws IOException {
        if (csvContent == null || csvContent.isBlank()) {
            return new CsvParseResult(Collections.emptyList(), Collections.emptyList());
        }

        List<List<String>> allRows = parseCsvTokens(csvContent);
        if (allRows.isEmpty()) {
            return new CsvParseResult(Collections.emptyList(), Collections.emptyList());
        }

        List<String> rawHeaders = allRows.getFirst();
        List<String> headers = new ArrayList<>();
        for (String h : rawHeaders) {
            headers.add(h != null ? h.trim() : "");
        }

        List<CsvRow> rows = new ArrayList<>();
        for (int i = 1; i < allRows.size(); i++) {
            List<String> rawRow = allRows.get(i);
            // Skip empty trailing rows
            if (rawRow.isEmpty() || (rawRow.size() == 1 && rawRow.getFirst().isBlank())) {
                continue;
            }

            Map<String, String> rowMap = new HashMap<>();
            for (int col = 0; col < headers.size(); col++) {
                String header = headers.get(col);
                String value = col < rawRow.size() ? rawRow.get(col) : "";
                rowMap.put(header, value != null ? value.trim() : "");
                // Also put lowercase key for case-insensitive lookup
                rowMap.put(header.toLowerCase(), value != null ? value.trim() : "");
            }
            rows.add(new CsvRow(i + 1, rowMap, rawRow));
        }

        return new CsvParseResult(headers, rows);
    }

    private static List<List<String>> parseCsvTokens(String csvContent) throws IOException {
        List<List<String>> rows = new ArrayList<>();
        BufferedReader reader = new BufferedReader(new StringReader(csvContent));
        String line;
        List<String> currentRow = new ArrayList<>();
        StringBuilder currentField = new StringBuilder();
        boolean inQuotes = false;

        while ((line = reader.readLine()) != null) {
            char[] chars = line.toCharArray();
            for (int i = 0; i < chars.length; i++) {
                char c = chars[i];
                if (c == '"') {
                    if (inQuotes && i + 1 < chars.length && chars[i + 1] == '"') {
                        currentField.append('"');
                        i++; // Skip escaped quote
                    } else {
                        inQuotes = !inQuotes;
                    }
                } else if (c == ',' && !inQuotes) {
                    currentRow.add(currentField.toString());
                    currentField.setLength(0);
                } else {
                    currentField.append(c);
                }
            }

            if (!inQuotes) {
                currentRow.add(currentField.toString());
                currentField.setLength(0);
                rows.add(currentRow);
                currentRow = new ArrayList<>();
            } else {
                currentField.append("\n"); // Retain newline inside quoted field
            }
        }

        if (inQuotes || !currentRow.isEmpty() || currentField.length() > 0) {
            currentRow.add(currentField.toString());
            rows.add(currentRow);
        }

        return rows;
    }
}
