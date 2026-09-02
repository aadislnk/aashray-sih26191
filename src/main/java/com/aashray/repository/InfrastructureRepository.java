package com.aashray.repository;

import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import com.aashray.entity.Habitation;
import com.aashray.entity.Infrastructure;

public interface InfrastructureRepository extends JpaRepository<Infrastructure, UUID> {
    List<Infrastructure> findByHabitation(Habitation habitation);

    @Query(value = """
        select i.*
        from infrastructure i
        where i.geometry && ST_MakeEnvelope(:minLongitude, :minLatitude, :maxLongitude, :maxLatitude, 4326)
          and ST_Intersects(i.geometry, ST_MakeEnvelope(:minLongitude, :minLatitude, :maxLongitude, :maxLatitude, 4326))
        """, nativeQuery = true)
    List<Infrastructure> findAllWithinBoundingBox(double minLongitude, double minLatitude, double maxLongitude, double maxLatitude);

    @Query(value = """
        select i.*
        from infrastructure i
        where ST_DWithin(
            i.geometry::geography,
            ST_SetSRID(ST_Point(:longitude, :latitude), 4326)::geography,
            :distanceMeters
        )
        """, nativeQuery = true)
    List<Infrastructure> findAllWithinRadius(double longitude, double latitude, double distanceMeters);

    @Query(value = """
        select i.*
        from infrastructure i
        where ST_Intersects(i.geometry, ST_GeomFromText(:geometryWkt, 4326))
        """, nativeQuery = true)
    List<Infrastructure> findAllIntersectingGeometry(String geometryWkt);
}
