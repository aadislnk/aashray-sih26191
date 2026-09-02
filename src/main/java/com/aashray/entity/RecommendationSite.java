package com.aashray.entity;

import java.math.BigDecimal;
import java.time.OffsetDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "recommendation_site")
public class RecommendationSite extends BaseUuidEntity {

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "recommendation_id", nullable = false)
    private Recommendation recommendation;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "relocation_site_id", nullable = false)
    private RelocationSite relocationSite;

    @Column(name = "allocation_population", nullable = false)
    private Integer allocationPopulation;

    @Column(name = "allocation_percentage")
    private BigDecimal allocationPercentage;

    @Column(name = "rank")
    private Integer rank;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;

    public Recommendation getRecommendation() {
        return recommendation;
    }

    public void setRecommendation(Recommendation recommendation) {
        this.recommendation = recommendation;
    }

    public RelocationSite getRelocationSite() {
        return relocationSite;
    }

    public void setRelocationSite(RelocationSite relocationSite) {
        this.relocationSite = relocationSite;
    }

    public Integer getAllocationPopulation() {
        return allocationPopulation;
    }

    public void setAllocationPopulation(Integer allocationPopulation) {
        this.allocationPopulation = allocationPopulation;
    }

    public BigDecimal getAllocationPercentage() {
        return allocationPercentage;
    }

    public void setAllocationPercentage(BigDecimal allocationPercentage) {
        this.allocationPercentage = allocationPercentage;
    }

    public Integer getRank() {
        return rank;
    }

    public void setRank(Integer rank) {
        this.rank = rank;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
