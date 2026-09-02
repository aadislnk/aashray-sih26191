# AASHRAY Data Ingestion Pipeline

This document describes the data ingestion layer implemented under **BE-011** for the AASHRAY backend.

---

## 1. Overview

The AASHRAY Data Ingestion Pipeline provides a clean, repeatable, and validated mechanism to ingest pilot spatial and tabular data into PostgreSQL/PostGIS. It supports:

1. **CSV**: Tabular pilot datasets (Habitations, Population census, Infrastructure, Relocation Sites, Data Sources).
2. **GeoJSON**: Geospatial vector data (FeatureCollection / Feature with Polygon, MultiPolygon, Point geometries).
3. **Structured JSON**: Domain model records (Vulnerabilities, Hazard Assessments, Risk Assessments, Carrying Capacity).
4. **GeoTIFF / Raster Metadata**: Metadata registration for raster layers (e.g. flood depth, elevation, slope) into `DataSource` without storing multi-megabyte binary blobs in relational tables.

---

## 2. Ingestion Architecture

```
                               ┌─────────────────────────────┐
                               │  REST API & File Upload     │
                               │  (/api/v1/ingestion/*)      │
                               └──────────────┬──────────────┘
                                              │
                               ┌──────────────▼──────────────┐
                               │      IngestionService       │
                               └──────────────┬──────────────┘
                                              │
            ┌───────────────────┬─────────────┴───────┬───────────────────┐
            │                   │                     │                   │
   ┌────────▼────────┐ ┌────────▼────────┐   ┌────────▼────────┐ ┌────────▼────────┐
   │ CsvDataImporter │ │GeoJsonImporter  │   │ JsonDataImporter│ │RasterMetadata   │
   └────────┬────────┘ └────────┬────────┘   └────────┬────────┘ └────────┬────────┘
            │                   │                     │                   │
            └───────────────────┴─────────────┬───────┴───────────────────┘
                                              │
                               ┌──────────────▼──────────────┐
                               │     IngestionValidator      │
                               │  - Coordinates [-180, 180]  │
                               │  - SRID 4326 / EPSG:4326    │
                               │  - JTS Geometry.isValid()   │
                               │  - Non-negative constraints │
                               │  - Duplicate deduplication  │
                               └──────────────┬──────────────┘
                                              │
                               ┌──────────────▼──────────────┐
                               │      JPA Repositories       │
                               │  (Transactional Persist)    │
                               └─────────────────────────────┘
```

---

## 3. Validation Rules

The ingestion engine never blindly imports raw files. Every record undergoes strict validation:

| Validation Category | Rules & Constraints |
| :--- | :--- |
| **Coordinates** | Longitude must be \([-180.0, 180.0]\), Latitude must be \([-90.0, 90.0]\). Non-finite (NaN) coordinates are rejected. |
| **SRID / CRS** | Standard project SRID is **4326** (`EPSG:4326` / WGS 84 / `CRS84`). Unsupported CRS headers are rejected. |
| **Geometry Validity** | Evaluated with JTS `IsValidOp`. Detects and rejects self-intersecting polygons (bowties), unclosed rings, or degenerate geometries. |
| **Geometry Compatibility** | `Habitation` and `RelocationSite` require `Polygon` or `MultiPolygon`; `AdminBoundary` requires `MultiPolygon`; `Infrastructure` requires `Point`. |
| **Numeric Value Ranges** | `population_count >= 0`, `capacity >= 0`, `total_capacity >= 0`, `estimated_capacity >= 0`. Assessment scores/probabilities must be within \([0.0, 1.0]\) or \([0, 100]\). Years must be between 1900 and 2100. |
| **Duplicates & Uniqueness**| Batch deduplication prevents repeated identifiers (`lgd_code`, `name`, `email`) in a single payload, and checks existing database unique keys. |
| **Mandatory Fields** | Required fields (`name`, `geometry`, `population_count`, `year`, `infrastructure_type`, `provider`, `dataset`) cannot be null or empty. |

---

## 4. Supported Formats & Expected Schemas

### A. CSV Ingestion

#### 1. Habitation (`target=HABITATION`)
- **Columns**:
  - `name` *(required)*: Village or habitation name
  - `lgd_code` *(optional)*: Unique Local Government Directory code
  - `admin_boundary_name` *(optional)*: Associated district or taluk name
  - `min_lon`, `min_lat`, `max_lon`, `max_lat` OR `wkt_geometry` OR `longitude`, `latitude`
- **Example**:
  ```csv
  name,lgd_code,min_lon,min_lat,max_lon,max_lat
  "East Village","LGD001",77.50,12.90,77.55,12.95
  "West Village","LGD002",77.60,12.90,77.65,12.95
  ```

#### 2. Population (`target=POPULATION`)
- **Columns**:
  - `habitation_name` or `lgd_code` *(required)*: Target habitation identifier
  - `population_count` *(required, integer >= 0)*: Total population
  - `year` *(required, 1900-2100)*: Census or estimate year
  - `source` *(optional)*: Data source description
- **Example**:
  ```csv
  habitation_name,population_count,year,source
  "East Village",1240,2026,"Census 2026"
  ```

#### 3. Infrastructure (`target=INFRASTRUCTURE`)
- **Columns**:
  - `habitation_name` or `lgd_code` *(required)*: Target habitation
  - `infrastructure_type` *(required)*: e.g. `HEALTH_CENTER`, `SCHOOL`, `SHELTER`, `ROAD`
  - `status` *(optional)*: `OPERATIONAL`, `DAMAGED`, etc.
  - `capacity` *(optional, integer >= 0)*
  - `longitude`, `latitude` *(required)* OR `wkt_geometry`
- **Example**:
  ```csv
  habitation_name,infrastructure_type,status,capacity,longitude,latitude
  "East Village","PRIMARY_HEALTH_CENTER","OPERATIONAL",50,77.52,12.92
  ```

---

### B. GeoJSON Ingestion (`target=HABITATION` / `ADMIN_BOUNDARY` / `RELOCATION_SITE` / `INFRASTRUCTURE`)

Supports GeoJSON `FeatureCollection` or `Feature`.

- **Habitations FeatureCollection Example**:
  ```json
  {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Polygon",
          "coordinates": [
            [[77.5, 12.9], [77.6, 12.9], [77.6, 13.0], [77.5, 13.0], [77.5, 12.9]]
          ]
        },
        "properties": {
          "name": "East Habitation",
          "lgd_code": "LGD101",
          "admin_boundary_name": "Bangalore Urban"
        }
      }
    ]
  }
  ```

- **Relocation Site FeatureCollection Example**:
  ```json
  {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Polygon",
          "coordinates": [
            [[77.7, 13.1], [77.8, 13.1], [77.8, 13.2], [77.7, 13.2], [77.7, 13.1]]
          ]
        },
        "properties": {
          "name": "Highland Safe Zone",
          "status": "APPROVED",
          "suitability_score": 0.88
        }
      }
    ]
  }
  ```

---

### C. Structured JSON Ingestion

#### Vulnerability Assessment (`target=VULNERABILITY`)
```json
[
  {
    "habitationName": "East Habitation",
    "hviScore": 0.65,
    "exposureScore": 0.80,
    "copingCapacity": 0.45,
    "assessmentYear": 2026,
    "componentData": {
      "floodSusceptibility": 0.8,
      "distanceToShelterKm": 4.5
    }
  }
]
```

#### Risk Assessment (`target=RISK_ASSESSMENT`)
```json
[
  {
    "habitationName": "East Habitation",
    "riskScore": 0.78,
    "riskBand": "HIGH",
    "priority": "URGENT",
    "confidence": 0.90
  }
]
```

---

### D. GeoTIFF / Raster Metadata Registration

GeoTIFF files are tracked via metadata in `data_source` without storing large binary raster pixels inside PostgreSQL.

- **Endpoint**: `POST /api/v1/ingestion/raster-metadata`
- **Payload**:
  ```json
  {
    "provider": "ISRO_Bhuvan",
    "dataset": "Flood_Depth_Grid_2026",
    "sourceType": "RASTER_GEOTIFF",
    "coverage": "BBOX(77.0, 12.0, 78.0, 13.0)",
    "resolution": "10m",
    "url": "s3://aashray-spatial-rasters/flood_depth_2026.tif",
    "crs": "EPSG:4326",
    "license": "Open Government Data (OGD)",
    "freshnessClass": "DAILY",
    "notes": "Derived flood depth raster output from hydraulic modeling"
  }
  ```

---

## 5. API Usage & Local Execution

### 1. Ingest CSV via REST
```bash
curl -X POST "http://localhost:8080/api/v1/ingestion/csv?target=HABITATION" \
  -H "Content-Type: text/plain" \
  -d "name,lgd_code,min_lon,min_lat,max_lon,max_lat
\"Village A\",\"LGD01\",77.50,12.90,77.55,12.95"
```

### 2. Ingest GeoJSON via REST
```bash
curl -X POST "http://localhost:8080/api/v1/ingestion/geojson?target=HABITATION" \
  -H "Content-Type: application/json" \
  -d @habitations.geojson
```

### 3. Register Raster Metadata
```bash
curl -X POST "http://localhost:8080/api/v1/ingestion/raster-metadata" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "Sentinel-2",
    "dataset": "Inundation_Map_2026",
    "crs": "EPSG:4326",
    "resolution": "10m",
    "url": "file:///data/rasters/inundation_2026.tif"
  }'
```

### 4. Upload File (CSV or GeoJSON)
```bash
curl -X POST "http://localhost:8080/api/v1/ingestion/upload" \
  -F "file=@habitations.csv" \
  -F "target=HABITATION"
```

---

## 6. Response Format

### Success Response (`200 OK`)
```json
{
  "status": "SUCCESS",
  "target": "HABITATION",
  "format": "CSV",
  "totalRecords": 2,
  "importedCount": 2,
  "failedCount": 0,
  "message": "Successfully imported 2 HABITATION records.",
  "errors": [],
  "importedIds": [
    "c8a7167a-d021-4ba2-8d9e-0123456789ab",
    "e9b8278b-e132-5cb3-9eaf-123456789abc"
  ]
}
```

### Validation Failure Response (`400 Bad Request`)
```json
{
  "status": "FAILED",
  "target": "HABITATION",
  "format": "GEOJSON",
  "totalRecords": 1,
  "importedCount": 0,
  "failedCount": 1,
  "message": "Validation errors occurred during GeoJSON ingestion",
  "errors": [
    {
      "rowIndex": 1,
      "identifier": null,
      "field": "geometry",
      "message": "Geometry is invalid: Self-intersection at coordinate (77.1, 12.1)",
      "rejectedValue": "POLYGON ((...))"
    }
  ],
  "importedIds": []
}
```
