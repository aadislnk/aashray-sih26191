from pathlib import Path

import geopandas as gpd
import pandas as pd


# ============================================================
# AASHRAY - KENDRAPARA COASTAL EXPOSURE FEATURES
# ============================================================

INPUT_VILLAGES = Path(
    "data/processed/administrative/"
    "kendrapara_coastal_villages.geojson"
)

OUTPUT_GEOJSON = Path(
    "data/processed/coastal/"
    "kendrapara_coastal_exposure.geojson"
)

OUTPUT_CSV = Path(
    "data/processed/features/"
    "kendrapara_coastal_exposure_features.csv"
)


print("=" * 70)
print("AASHRAY KENDRAPARA COASTAL EXPOSURE")
print("=" * 70)


# ------------------------------------------------------------
# 1. LOAD VILLAGE BOUNDARIES
# ------------------------------------------------------------

print("\nLoading Kendrapara coastal villages...")

gdf = gpd.read_file(INPUT_VILLAGES)

print(f"Villages loaded: {len(gdf)}")

if len(gdf) == 0:
    raise SystemExit("ERROR: No village geometries found.")


# ------------------------------------------------------------
# 2. CHECK REQUIRED COLUMNS
# ------------------------------------------------------------

required_columns = [
    "village",
    "vlcode",
    "block",
    "district",
    "geometry",
]

missing = [
    column
    for column in required_columns
    if column not in gdf.columns
]

if missing:
    print("\nERROR: Missing columns:")
    print(missing)
    raise SystemExit(1)


# ------------------------------------------------------------
# 3. CALCULATE VILLAGE AREA
# ------------------------------------------------------------
#
# The source CRS is EPSG:7755.
# We calculate area directly in the projected CRS.
# This gives area in square metres.
# ------------------------------------------------------------

print("\nCalculating village areas...")

if not gdf.crs:
    raise SystemExit("ERROR: Village layer has no CRS.")

print(f"Source CRS: {gdf.crs}")

gdf["area_m2"] = gdf.geometry.area

gdf["area_km2"] = (
    gdf["area_m2"] / 1_000_000
)


# ------------------------------------------------------------
# 4. CALCULATE VILLAGE CENTROIDS
# ------------------------------------------------------------

print("\nCalculating village centroids...")

centroids = gdf.geometry.centroid

gdf["centroid_x"] = centroids.x
gdf["centroid_y"] = centroids.y


# ------------------------------------------------------------
# 5. NORMALIZE AREA
# ------------------------------------------------------------
#
# Larger villages generally contain more land that may be
# exposed to coastal hazards.
#
# This is an EXPOSURE PROXY, not a measured hazard.
# ------------------------------------------------------------

area_min = gdf["area_km2"].min()
area_max = gdf["area_km2"].max()

if area_max > area_min:

    gdf["area_exposure_score"] = (
        (gdf["area_km2"] - area_min)
        / (area_max - area_min)
    )

else:

    gdf["area_exposure_score"] = 0.0


# ------------------------------------------------------------
# 6. CREATE BASE EXPOSURE SCORE
# ------------------------------------------------------------
#
# At this stage we do NOT have village-level shoreline
# distance or measured erosion rate.
#
# Therefore we explicitly call this:
#
#   COASTAL_GEOMETRY_EXPOSURE
#
# It is a preliminary spatial exposure feature.
# ------------------------------------------------------------

gdf["coastal_exposure_score"] = (
    gdf["area_exposure_score"]
)


# ------------------------------------------------------------
# 7. EXPOSURE CATEGORY
# ------------------------------------------------------------

def classify_exposure(score):

    if score < 0.25:
        return "LOW"

    elif score < 0.50:
        return "MODERATE"

    elif score < 0.75:
        return "HIGH"

    else:
        return "VERY HIGH"


gdf["coastal_exposure_category"] = (
    gdf["coastal_exposure_score"]
    .apply(classify_exposure)
)


# ------------------------------------------------------------
# 8. DATA PROVENANCE
# ------------------------------------------------------------

gdf["exposure_method"] = (
    "Village geometry area normalized within "
    "Kendrapara coastal-belt villages"
)

gdf["exposure_data_quality"] = (
    "PRELIMINARY_SPATIAL_PROXY"
)

gdf["shoreline_distance_available"] = False

gdf["village_erosion_rate_available"] = False


# ------------------------------------------------------------
# 9. SAVE GEOJSON
# ------------------------------------------------------------

OUTPUT_GEOJSON.parent.mkdir(
    parents=True,
    exist_ok=True
)

gdf.to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON"
)


# ------------------------------------------------------------
# 10. CREATE CSV
# ------------------------------------------------------------

output_columns = [
    "village",
    "vlcode",
    "block",
    "district",
    "area_m2",
    "area_km2",
    "centroid_x",
    "centroid_y",
    "area_exposure_score",
    "coastal_exposure_score",
    "coastal_exposure_category",
    "exposure_method",
    "exposure_data_quality",
    "shoreline_distance_available",
    "village_erosion_rate_available",
]

features = gdf[output_columns].copy()

OUTPUT_CSV.parent.mkdir(
    parents=True,
    exist_ok=True
)

features.to_csv(
    OUTPUT_CSV,
    index=False
)


# ------------------------------------------------------------
# 11. PRINT STATISTICS
# ------------------------------------------------------------

print("\nExposure score statistics:")

print(
    f"  Minimum: "
    f"{gdf['coastal_exposure_score'].min():.4f}"
)

print(
    f"  Mean: "
    f"{gdf['coastal_exposure_score'].mean():.4f}"
)

print(
    f"  Maximum: "
    f"{gdf['coastal_exposure_score'].max():.4f}"
)


print("\nExposure category distribution:")

distribution = (
    gdf["coastal_exposure_category"]
    .value_counts()
    .sort_index()
)

for category, count in distribution.items():

    percentage = (
        count / len(gdf)
    ) * 100

    print(
        f"  {category}: "
        f"{count} villages "
        f"({percentage:.2f}%)"
    )


print("\nVillage area statistics:")

print(
    f"  Minimum area: "
    f"{gdf['area_km2'].min():.4f} km²"
)

print(
    f"  Mean area: "
    f"{gdf['area_km2'].mean():.4f} km²"
)

print(
    f"  Maximum area: "
    f"{gdf['area_km2'].max():.4f} km²"
)


# ------------------------------------------------------------
# 12. OUTPUT PATHS
# ------------------------------------------------------------

print("\nSaved spatial exposure layer:")
print(OUTPUT_GEOJSON.resolve())

print("\nSaved exposure features:")
print(OUTPUT_CSV.resolve())


print("\n" + "=" * 70)
print("✓ COASTAL EXPOSURE FEATURE GENERATION COMPLETE")
print("=" * 70)