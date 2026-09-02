package com.aashray.repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

import com.aashray.entity.Habitation;
import com.aashray.entity.Population;

public interface PopulationRepository extends JpaRepository<Population, UUID> {
    List<Population> findByHabitation(Habitation habitation);
    Optional<Population> findByHabitationAndYear(Habitation habitation, Integer year);
}
