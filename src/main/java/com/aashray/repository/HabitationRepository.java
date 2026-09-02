package com.aashray.repository;

import java.util.Optional;
import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import com.aashray.entity.Habitation;

public interface HabitationRepository extends JpaRepository<Habitation, UUID> {
    Optional<Habitation> findByLgdCode(String lgdCode);
    Optional<Habitation> findByName(String name);
    boolean existsByLgdCode(String lgdCode);

    @Query(value = """
        select h.*
        from habitation h
        where h.geometry && ST_MakeEnvelope(:minLongitude, :minLatitude, :maxLongitude, :maxLatitude, 4326)
          and ST_Intersects(h.geometry, ST_MakeEnvelope(:minLongitude, :minLatitude, :maxLongitude, :maxLatitude, 4326))
        """, nativeQuery = true)
    List<Habitation> findAllWithinBoundingBox(double minLongitude, double minLatitude, double maxLongitude, double maxLatitude);

    @Query(value = """
        select h.*
        from habitation h
        where ST_DWithin(
            h.geometry::geography,
            ST_SetSRID(ST_Point(:longitude, :latitude), 4326)::geography,
            :distanceMeters
        )
        """, nativeQuery = true)
    List<Habitation> findAllWithinRadius(double longitude, double latitude, double distanceMeters);

    @Query(value = """
        select h.*
        from habitation h
        where ST_Intersects(h.geometry, ST_GeomFromText(:geometryWkt, 4326))
        """, nativeQuery = true)
    List<Habitation> findAllIntersectingGeometry(String geometryWkt);
}
