AASHRAY API Standards (MVP)

This document defines minimal, practical conventions for all AASHRAY REST APIs.

Decisions not explicitly specified in the plan
- Successful responses are returned directly (no envelope/wrapper) for single-resource and list endpoints; list endpoints include a small pagination metadata object when paginated.
- Pagination defaults: page=0, size=20, max size=100. Use zero-based pages.
- Sorting: use a single query parameter `sort` with format `field,(asc|desc)`. Multiple sorts allowed by repeating `sort` or comma-separating pairs.
- Filtering: simple query parameters (equality and range). Use `minX` / `maxX` for numeric ranges and comma-separated lists for multiple values.
- Date/time: ISO-8601 timestamps with offset (UTC preferred, e.g. 2026-08-30T15:30:00Z).
- Geometry: use GeoJSON for geometries (GeoJSON Geometry or Feature objects) and separate `latitude`/`longitude` only when a single point is required.
- Error codes: uppercase, underscore-separated strings (e.g., RESOURCE_NOT_FOUND, VALIDATION_ERROR).

1. Base API URL and versioning
- Base path: /api/v1
- Versioning strategy: URI versioning. New major incompatible changes -> /api/v2.

2. URL / resource naming
- Use plural nouns for resources: /habitations, /relocation-sites, /users, /map/features
- Use kebab-case or camelCase? Use kebab-case in URLs (recommended for readability): /relocation-sites
- Path parameter convention: use `{id}` for primary identifiers and descriptive names when needed: /habitations/{habitationId}
- Examples:
  - /api/v1/habitations
  - /api/v1/habitations/{habitationId}
  - /api/v1/map/features
  - /api/v1/dashboard/summary
  - /api/v1/relocation-sites

3. HTTP methods
- GET: retrieve a resource or collection (safe, idempotent)
- POST: create a new resource (server assigns id). Returns 201 Created with Location header.
- PUT/PATCH: update existing resource. PUT for full replace, PATCH for partial update. Both idempotent in semantics.
- DELETE: remove a resource. Return 204 No Content on success.

4. HTTP status codes
- Successful responses
  - 200 OK — successful GET, successful non-creation operations returning a body.
  - 201 Created — successful POST creating a resource; include `Location` header set to the new resource URL and return representation.
  - 204 No Content — successful DELETE or update when no body is returned.
- Validation errors
  - 400 Bad Request — request validation failed. Use code VALIDATION_ERROR and details field contains field errors.
- Unauthorized / Forbidden
  - 401 Unauthorized — authentication required or failed.
  - 403 Forbidden — authenticated but not allowed to perform action.
- Not found
  - 404 Not Found — resource does not exist. Use code RESOURCE_NOT_FOUND.
- Conflict
  - 409 Conflict — resource conflict (e.g., unique constraint). Use code CONFLICT.
- Server / external-service errors
  - 502/503/504 as appropriate for upstream failures; 500 Internal Server Error for unexpected server errors. Use code INTERNAL_ERROR.

5. JSON response conventions
- Field naming: camelCase for JSON property names (e.g., createdAt, hazardLevel).
- Successful resource responses: return resource JSON directly (not wrapped). List endpoints return an object with `items` and paging metadata when paginated.
- Example single resource response (200):
  {
    "id": "123",
    "name": "East Habitation",
    "region": "north"
  }
- Example paginated list response (200):
  {
    "items": [ { ... }, { ... } ],
    "page": 0,
    "size": 20,
    "totalElements": 123,
    "totalPages": 7
  }

6. Error response
- Use the AASHRAY structure for all error responses:
  {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Habitation not found",
    "details": {}
  }
- Field meanings:
  - code: machine-readable error code (UPPER_SNAKE_CASE)
  - message: human-readable short message
  - details: free-form object for field errors or vendor details
- Validation example:
  {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": { "name": "must not be empty", "region": "invalid value" }
  }

7. Pagination
- Request parameters:
  - page (integer, zero-based, default 0)
  - size (integer, default 20, max 100)
  - sort (string, e.g. sort=name,asc). Can repeat or provide multiple comma-separated values.
- Response structure when paginated: the list response MUST include the `items` array and metadata: page, size, totalElements, totalPages.

8. Filtering
- Use query parameters for filtering. Prefer explicit parameter names rather than complex filter syntax.
- Equality: ?region=north&priority=high
- Multiple values: comma-separated or repeated param: ?region=north,south or ?region=north&region=south
- Ranges: use min/max prefixes: ?minRisk=0.2&maxRisk=0.8 or ?startDate=2026-01-01&endDate=2026-02-01
- Examples:
  - ?priority=high
  - ?hazard=flood
  - ?region=north
  - ?minRisk=0.1&maxRisk=0.5

9. Sorting
- Single query parameter `sort=field,asc|desc`. Example: ?sort=hazardLevel,desc
- Multiple sorts: repeat `sort` or supply `sort=field1,asc&sort=field2,desc`.

10. Date / time
- Use ISO-8601 timestamps with timezone offset. Prefer UTC (Z): 2026-08-30T15:30:00Z
- Use full date-time for timestamps (createdAt, updatedAt). For date-only fields use YYYY-MM-DD.

11. Geometry
- Represent spatial data using GeoJSON where appropriate.
- For location collections: return GeoJSON FeatureCollection or an array of GeoJSON Features:
  {
    "type": "FeatureCollection",
    "features": [ { "type": "Feature", "geometry": {"type":"Point","coordinates":[lon,lat]}, "properties": { ... } } ]
  }
- For single-location fields on a resource, include either:
  - a `geometry` GeoJSON object (preferred), or
  - separate `latitude` and `longitude` numeric fields when a simple point is sufficient.
- Do not mix geometry encodings; make field names explicit (geometry vs latitude/longitude).

12. Empty results
- Return 200 OK with an empty `items` array and pagination metadata when list endpoint returns no records:
  {
    "items": [],
    "page": 0,
    "size": 20,
    "totalElements": 0,
    "totalPages": 0
  }

13. API examples
- GET /api/v1/habitations
  Request: GET /api/v1/habitations?page=0&size=20&sort=name,asc&region=north
  Response 200:
  {
    "items": [
      { "id": "h1", "name": "East Habitation", "region": "north" }
    ],
    "page": 0,
    "size": 20,
    "totalElements": 1,
    "totalPages": 1
  }

- GET /api/v1/habitations/{id}
  Request: GET /api/v1/habitations/h1
  Response 200:
  {
    "id": "h1",
    "name": "East Habitation",
    "region": "north",
    "geometry": { "type": "Point", "coordinates": [77.6, 12.9] }
  }

  If not found: 404
  {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Habitation not found",
    "details": {}
  }

- GET /api/v1/map/features
  Request: GET /api/v1/map/features?bbox=77.0,12.5,78.0,13.5&hazard=flood
  Response 200 (GeoJSON FeatureCollection):
  {
    "type": "FeatureCollection",
    "features": [
      { "type": "Feature", "geometry": { "type": "Point", "coordinates": [77.6, 12.9] }, "properties": { "id": "h1", "hazard": "flood" } }
    ]
  }

- GET /api/v1/dashboard/summary
  Request: GET /api/v1/dashboard/summary?region=north
  Response 200:
  {
    "totalHabitations": 123,
    "atRisk": 12,
    "lastUpdated": "2026-08-30T15:30:00Z"
  }

Notes and guidance
- Keep endpoints simple and predictable. Prefer explicit query parameters over complex filter grammar.
- Document each endpoint with examples and required/optional query parameters in service-level API docs.
- These conventions are intentionally minimal to support rapid development while ensuring consistent client behavior.
