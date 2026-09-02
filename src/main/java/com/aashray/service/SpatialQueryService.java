package com.aashray.service;

import java.util.List;

import org.locationtech.jts.geom.Geometry;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.aashray.entity.AdminBoundary;
import com.aashray.entity.Habitation;
import com.aashray.entity.Infrastructure;
import com.aashray.entity.RelocationSite;
import com.aashray.exception.ApiException;
import com.aashray.repository.AdminBoundaryRepository;
import com.aashray.repository.HabitationRepository;
import com.aashray.repository.InfrastructureRepository;
import com.aashray.repository.RelocationSiteRepository;

@Service
@Transactional(readOnly = true)
public class SpatialQueryService {

    private static final double MIN_LONGITUDE = -180.0;
    private static final double MAX_LONGITUDE = 180.0;
    private static final double MIN_LATITUDE = -90.0;
    private static final double MAX_LATITUDE = 90.0;
    private static final int EXPECTED_SRID = 4326;

    private final HabitationRepository habitationRepository;
    private final InfrastructureRepository infrastructureRepository;
    private final RelocationSiteRepository relocationSiteRepository;
    private final AdminBoundaryRepository adminBoundaryRepository;

    public SpatialQueryService(HabitationRepository habitationRepository,
                               InfrastructureRepository infrastructureRepository,
                               RelocationSiteRepository relocationSiteRepository,
                               AdminBoundaryRepository adminBoundaryRepository) {
        this.habitationRepository = habitationRepository;
        this.infrastructureRepository = infrastructureRepository;
        this.relocationSiteRepository = relocationSiteRepository;
        this.adminBoundaryRepository = adminBoundaryRepository;
    }

    public List<Habitation> findHabitationsWithinBoundingBox(double minLongitude, double minLatitude,
                                                             double maxLongitude, double maxLatitude) {
        validateBoundingBox(minLongitude, minLatitude, maxLongitude, maxLatitude);
        return habitationRepository.findAllWithinBoundingBox(minLongitude, minLatitude, maxLongitude, maxLatitude);
    }

    public List<Habitation> findHabitationsWithinRadius(double longitude, double latitude, double distanceMeters) {
        validatePoint(longitude, latitude);
        validateDistance(distanceMeters);
        return habitationRepository.findAllWithinRadius(longitude, latitude, distanceMeters);
    }

    public List<Habitation> findHabitationsIntersectingGeometry(Geometry geometry) {
        validateGeometry(geometry);
        return habitationRepository.findAllIntersectingGeometry(geometry.toText());
    }

    public List<Infrastructure> findInfrastructureWithinBoundingBox(double minLongitude, double minLatitude,
                                                                     double maxLongitude, double maxLatitude) {
        validateBoundingBox(minLongitude, minLatitude, maxLongitude, maxLatitude);
        return infrastructureRepository.findAllWithinBoundingBox(minLongitude, minLatitude, maxLongitude, maxLatitude);
    }

    public List<Infrastructure> findInfrastructureWithinRadius(double longitude, double latitude, double distanceMeters) {
        validatePoint(longitude, latitude);
        validateDistance(distanceMeters);
        return infrastructureRepository.findAllWithinRadius(longitude, latitude, distanceMeters);
    }

    public List<Infrastructure> findInfrastructureIntersectingGeometry(Geometry geometry) {
        validateGeometry(geometry);
        return infrastructureRepository.findAllIntersectingGeometry(geometry.toText());
    }

    public List<RelocationSite> findRelocationSitesWithinBoundingBox(double minLongitude, double minLatitude,
                                                                     double maxLongitude, double maxLatitude) {
        validateBoundingBox(minLongitude, minLatitude, maxLongitude, maxLatitude);
        return relocationSiteRepository.findAllWithinBoundingBox(minLongitude, minLatitude, maxLongitude, maxLatitude);
    }

    public List<RelocationSite> findRelocationSitesWithinRadius(double longitude, double latitude, double distanceMeters) {
        validatePoint(longitude, latitude);
        validateDistance(distanceMeters);
        return relocationSiteRepository.findAllWithinRadius(longitude, latitude, distanceMeters);
    }

    public List<RelocationSite> findRelocationSitesIntersectingGeometry(Geometry geometry) {
        validateGeometry(geometry);
        return relocationSiteRepository.findAllIntersectingGeometry(geometry.toText());
    }

    public List<AdminBoundary> findAdminBoundariesWithinBoundingBox(double minLongitude, double minLatitude,
                                                                    double maxLongitude, double maxLatitude) {
        validateBoundingBox(minLongitude, minLatitude, maxLongitude, maxLatitude);
        return adminBoundaryRepository.findAllWithinBoundingBox(minLongitude, minLatitude, maxLongitude, maxLatitude);
    }

    public List<AdminBoundary> findAdminBoundariesWithinRadius(double longitude, double latitude, double distanceMeters) {
        validatePoint(longitude, latitude);
        validateDistance(distanceMeters);
        return adminBoundaryRepository.findAllWithinRadius(longitude, latitude, distanceMeters);
    }

    public List<AdminBoundary> findAdminBoundariesIntersectingGeometry(Geometry geometry) {
        validateGeometry(geometry);
        return adminBoundaryRepository.findAllIntersectingGeometry(geometry.toText());
    }

    private void validateBoundingBox(double minLongitude, double minLatitude,
                                     double maxLongitude, double maxLatitude) {
        validatePoint(minLongitude, minLatitude);
        validatePoint(maxLongitude, maxLatitude);
        if (minLongitude > maxLongitude) {
            throw ApiException.validation("minLongitude must be less than or equal to maxLongitude");
        }
        if (minLatitude > maxLatitude) {
            throw ApiException.validation("minLatitude must be less than or equal to maxLatitude");
        }
    }

    private void validatePoint(double longitude, double latitude) {
        if (longitude < MIN_LONGITUDE || longitude > MAX_LONGITUDE) {
            throw ApiException.validation("Longitude must be within [-180, 180]");
        }
        if (latitude < MIN_LATITUDE || latitude > MAX_LATITUDE) {
            throw ApiException.validation("Latitude must be within [-90, 90]");
        }
    }

    private void validateDistance(double distanceMeters) {
        if (distanceMeters <= 0.0d) {
            throw ApiException.validation("distanceMeters must be greater than 0");
        }
    }

    private void validateGeometry(Geometry geometry) {
        if (geometry == null || geometry.isEmpty()) {
            throw ApiException.validation("geometry must not be null or empty");
        }
        if (geometry.getSRID() != EXPECTED_SRID) {
            throw ApiException.validation("geometry must use SRID 4326");
        }
    }
}
