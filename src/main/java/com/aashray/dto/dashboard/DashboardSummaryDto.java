package com.aashray.dto.dashboard;

import java.time.OffsetDateTime;

public record DashboardSummaryDto(
    long p1Count,
    long p2Count,
    long p3Count,
    long p4Count,
    long totalHabitations,
    OffsetDateTime lastUpdated
) {
}
