package com.aashray.entity;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.Map;

import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "recommendation")
public class Recommendation extends BaseUuidEntity {

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "habitation_id", nullable = false)
    private Habitation habitation;

    @Column(nullable = false)
    private String status;

    @Column(name = "suitability_score")
    private BigDecimal suitabilityScore;

    @Column(name = "allocated_population")
    private Integer allocatedPopulation;

    @Column(name = "split_required", nullable = false)
    private boolean splitRequired;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "reason_codes", columnDefinition = "jsonb")
    private Map<String, Object> reasonCodes;

    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

    public Habitation getHabitation() {
        return habitation;
    }

    public void setHabitation(Habitation habitation) {
        this.habitation = habitation;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public BigDecimal getSuitabilityScore() {
        return suitabilityScore;
    }

    public void setSuitabilityScore(BigDecimal suitabilityScore) {
        this.suitabilityScore = suitabilityScore;
    }

    public Integer getAllocatedPopulation() {
        return allocatedPopulation;
    }

    public void setAllocatedPopulation(Integer allocatedPopulation) {
        this.allocatedPopulation = allocatedPopulation;
    }

    public boolean isSplitRequired() {
        return splitRequired;
    }

    public void setSplitRequired(boolean splitRequired) {
        this.splitRequired = splitRequired;
    }

    public Map<String, Object> getReasonCodes() {
        return reasonCodes;
    }

    public void setReasonCodes(Map<String, Object> reasonCodes) {
        this.reasonCodes = reasonCodes;
    }

    public OffsetDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(OffsetDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
}
