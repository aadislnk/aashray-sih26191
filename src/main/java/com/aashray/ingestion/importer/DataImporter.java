package com.aashray.ingestion.importer;

import java.util.Map;

import com.aashray.ingestion.model.IngestionFormat;
import com.aashray.ingestion.model.IngestionResult;
import com.aashray.ingestion.model.IngestionTarget;

public interface DataImporter {

    boolean supports(IngestionFormat format, IngestionTarget target);

    IngestionResult importData(String content, IngestionTarget target, Map<String, Object> options);
}
