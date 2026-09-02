package com.aashray.repository;

import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

import com.aashray.entity.Scenario;

public interface ScenarioRepository extends JpaRepository<Scenario, UUID> {
}
