package com.aashray.dto.dashboard;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

public record DashboardHotspotDto(
    UUID habitationId,
    String habitationName,
    String priority,
    BigDecimal riskScore,
    Map<String, Object> geometry,
    OffsetDateTime assessmentTime
) {
}
