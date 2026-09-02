package com.aashray.repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import com.aashray.entity.RelocationSite;

public interface RelocationSiteRepository extends JpaRepository<RelocationSite, UUID> {
    Optional<RelocationSite> findByName(String name);

    @Query(value = """
        select r.*
        from relocation_site r
        where r.geometry && ST_MakeEnvelope(:minLongitude, :minLatitude, :maxLongitude, :maxLatitude, 4326)
          and ST_Intersects(r.geometry, ST_MakeEnvelope(:minLongitude, :minLatitude, :maxLongitude, :maxLatitude, 4326))
        """, nativeQuery = true)
    List<RelocationSite> findAllWithinBoundingBox(double minLongitude, double minLatitude, double maxLongitude, double maxLatitude);

    @Query(value = """
        select r.*
        from relocation_site r
        where ST_DWithin(
            r.geometry::geography,
            ST_SetSRID(ST_Point(:longitude, :latitude), 4326)::geography,
            :distanceMeters
        )
        """, nativeQuery = true)
    List<RelocationSite> findAllWithinRadius(double longitude, double latitude, double distanceMeters);

    @Query(value = """
        select r.*
        from relocation_site r
        where ST_Intersects(r.geometry, ST_GeomFromText(:geometryWkt, 4326))
        """, nativeQuery = true)
    List<RelocationSite> findAllIntersectingGeometry(String geometryWkt);
}
