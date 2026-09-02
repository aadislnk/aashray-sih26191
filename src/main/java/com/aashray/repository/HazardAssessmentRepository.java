package com.aashray.repository;

import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

import com.aashray.entity.HazardAssessment;

public interface HazardAssessmentRepository extends JpaRepository<HazardAssessment, UUID> {
}
