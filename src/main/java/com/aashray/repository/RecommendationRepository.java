package com.aashray.repository;

import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

import com.aashray.entity.Recommendation;

public interface RecommendationRepository extends JpaRepository<Recommendation, UUID> {
}
