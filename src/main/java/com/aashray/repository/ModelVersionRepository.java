package com.aashray.repository;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

import com.aashray.entity.ModelVersion;

public interface ModelVersionRepository extends JpaRepository<ModelVersion, UUID> {
    Optional<ModelVersion> findByModelNameAndVersion(String modelName, String version);
}
