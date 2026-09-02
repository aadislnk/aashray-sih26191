package com.aashray.repository;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

import com.aashray.entity.DataSource;

public interface DataSourceRepository extends JpaRepository<DataSource, UUID> {
    Optional<DataSource> findByProviderAndDataset(String provider, String dataset);
}
