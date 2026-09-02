package com.aashray.repository;

import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

import com.aashray.entity.CarryingCapacity;

public interface CarryingCapacityRepository extends JpaRepository<CarryingCapacity, UUID> {
}
