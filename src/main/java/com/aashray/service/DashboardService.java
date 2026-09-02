package com.aashray.service;

import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.aashray.dto.dashboard.DashboardHotspotDto;
import com.aashray.dto.dashboard.DashboardSummaryDto;
import com.aashray.exception.ApiException;
import com.aashray.repository.RiskAssessmentRepository;
import com.aashray.repository.RiskAssessmentRepository.DashboardHotspotProjection;
import com.aashray.repository.RiskAssessmentRepository.DashboardSummaryProjection;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
@Transactional(readOnly = true)
public class DashboardService {

    private static final int MAX_HOTSPOTS_LIMIT = 100;

    private final RiskAssessmentRepository riskAssessmentRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public DashboardService(RiskAssessmentRepository riskAssessmentRepository) {
        this.riskAssessmentRepository = riskAssessmentRepository;
    }

    public DashboardSummaryDto getSummary(String region) {
        DashboardSummaryProjection summary = hasText(region)
            ? riskAssessmentRepository.summarizeLatestRiskByRegion(region.trim())
            : riskAssessmentRepository.summarizeLatestRisk();

        return new DashboardSummaryDto(
            valueOrZero(summary.getP1Count()),
            valueOrZero(summary.getP2Count()),
            valueOrZero(summary.getP3Count()),
            valueOrZero(summary.getP4Count()),
            valueOrZero(summary.getTotalHabitations()),
            summary.getLastUpdated()
        );
    }

    public List<DashboardHotspotDto> getHotspots(String region, int limit) {
        validateLimit(limit);
        List<DashboardHotspotProjection> hotspots = hasText(region)
            ? riskAssessmentRepository.findTopHotspotsByRegion(region.trim(), limit)
            : riskAssessmentRepository.findTopHotspots(limit);

        return hotspots.stream()
            .map(this::toHotspotDto)
            .toList();
    }

    private DashboardHotspotDto toHotspotDto(DashboardHotspotProjection hotspot) {
        return new DashboardHotspotDto(
            UUID.fromString(hotspot.getHabitationId()),
            hotspot.getHabitationName(),
            hotspot.getPriority(),
            hotspot.getRiskScore(),
            parseGeometry(hotspot.getGeometry()),
            hotspot.getAssessmentTime()
        );
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> parseGeometry(String geometry) {
        try {
            return objectMapper.readValue(geometry, Map.class);
        } catch (JsonProcessingException exception) {
            throw ApiException.internal("Unable to serialize dashboard geometry");
        }
    }

    private void validateLimit(int limit) {
        if (limit <= 0) {
            throw ApiException.validation("limit must be greater than 0");
        }
        if (limit > MAX_HOTSPOTS_LIMIT) {
            throw ApiException.validation("limit must be less than or equal to 100");
        }
    }

    private long valueOrZero(Long value) {
        return value == null ? 0L : value;
    }

    private boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }
}
