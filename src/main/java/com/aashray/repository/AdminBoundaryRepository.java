package com.aashray.repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import com.aashray.entity.AdminBoundary;

public interface AdminBoundaryRepository extends JpaRepository<AdminBoundary, UUID> {
    Optional<AdminBoundary> findByName(String name);
    Optional<AdminBoundary> findByNameAndBoundaryType(String name, String boundaryType);

    @Query(value = """
        select a.*
        from admin_boundary a
        where a.geometry && ST_MakeEnvelope(:minLongitude, :minLatitude, :maxLongitude, :maxLatitude, 4326)
          and ST_Intersects(a.geometry, ST_MakeEnvelope(:minLongitude, :minLatitude, :maxLongitude, :maxLatitude, 4326))
        """, nativeQuery = true)
    List<AdminBoundary> findAllWithinBoundingBox(double minLongitude, double minLatitude, double maxLongitude, double maxLatitude);

    @Query(value = """
        select a.*
        from admin_boundary a
        where ST_DWithin(
            a.geometry::geography,
            ST_SetSRID(ST_Point(:longitude, :latitude), 4326)::geography,
            :distanceMeters
        )
        """, nativeQuery = true)
    List<AdminBoundary> findAllWithinRadius(double longitude, double latitude, double distanceMeters);

    @Query(value = """
        select a.*
        from admin_boundary a
        where ST_Intersects(a.geometry, ST_GeomFromText(:geometryWkt, 4326))
        """, nativeQuery = true)
    List<AdminBoundary> findAllIntersectingGeometry(String geometryWkt);
}
