package com.aashray.repository;

import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

import com.aashray.entity.RecommendationSite;

public interface RecommendationSiteRepository extends JpaRepository<RecommendationSite, UUID> {
}
