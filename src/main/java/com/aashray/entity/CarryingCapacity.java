package com.aashray.entity;

import java.time.OffsetDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "carrying_capacity")
public class CarryingCapacity extends BaseUuidEntity {

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "relocation_site_id", nullable = false)
    private RelocationSite relocationSite;

    @Column(name = "total_capacity", nullable = false)
    private Integer totalCapacity;

    @Column(name = "estimated_capacity")
    private Integer estimatedCapacity;

    @Column(name = "binding_sector")
    private String bindingSector;

    @Column(name = "calculated_at", nullable = false)
    private OffsetDateTime calculatedAt;

    public RelocationSite getRelocationSite() {
        return relocationSite;
    }

    public void setRelocationSite(RelocationSite relocationSite) {
        this.relocationSite = relocationSite;
    }

    public Integer getTotalCapacity() {
        return totalCapacity;
    }

    public void setTotalCapacity(Integer totalCapacity) {
        this.totalCapacity = totalCapacity;
    }

    public Integer getEstimatedCapacity() {
        return estimatedCapacity;
    }

    public void setEstimatedCapacity(Integer estimatedCapacity) {
        this.estimatedCapacity = estimatedCapacity;
    }

    public String getBindingSector() {
        return bindingSector;
    }

    public void setBindingSector(String bindingSector) {
        this.bindingSector = bindingSector;
    }

    public OffsetDateTime getCalculatedAt() {
        return calculatedAt;
    }

    public void setCalculatedAt(OffsetDateTime calculatedAt) {
        this.calculatedAt = calculatedAt;
    }
}
