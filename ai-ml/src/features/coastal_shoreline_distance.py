from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, MultiLineString


# ============================================================
# AASHRAY - KENDRAPARA SHORELINE PROXIMITY
# ============================================================

INPUT_VILLAGES = Path(
    "data/processed/administrative/"
    "kendrapara_coastal_villages.geojson"
)

INPUT_FEATURES = Path(
    "data/processed/features/"
    "kendrapara_coastal_exposure_features.csv"
)

OUTPUT_GEOJSON = Path(
    "data/processed/coastal/"
    "kendrapara_shoreline_proximity.geojson"
)

OUTPUT_CSV = Path(
    "data/processed/features/"
    "kendrapara_shoreline_proximity_features.csv"
)


print("=" * 70)
print("AASHRAY KENDRAPARA SHORELINE PROXIMITY")
print("=" * 70)


# ------------------------------------------------------------
# 1. LOAD VILLAGES
# ------------------------------------------------------------

print("\nLoading village boundaries...")

gdf = gpd.read_file(INPUT_VILLAGES)

print(f"Villages loaded: {len(gdf)}")

if len(gdf) == 0:
    raise SystemExit("ERROR: No village geometries found.")


# ------------------------------------------------------------
# 2. CHECK CRS
# ------------------------------------------------------------

if gdf.crs is None:
    raise SystemExit("ERROR: Village layer has no CRS.")

print(f"Source CRS: {gdf.crs}")


# ------------------------------------------------------------
# 3. LOAD EXISTING EXPOSURE FEATURES
# ------------------------------------------------------------

print("\nLoading existing exposure features...")

features = pd.read_csv(INPUT_FEATURES)

print(f"Exposure feature rows: {len(features)}")

required = [
    "village",
    "vlcode",
    "block",
    "district",
    "area_km2",
    "coastal_exposure_score",
]

missing = [
    col for col in required
    if col not in features.columns
]

if missing:
    print("\nERROR: Missing columns:")
    print(missing)
    raise SystemExit(1)


# ------------------------------------------------------------
# 4. CREATE A COASTAL REFERENCE LINE
# ------------------------------------------------------------
#
# We use the outer boundary of the complete coastal village
# belt as a spatial reference.
#
# This is a PROXY coastline, not an official shoreline.
# ------------------------------------------------------------

print("\nCreating coastal reference boundary...")

boundary = gdf.geometry.union_all().boundary

if isinstance(boundary, LineString):
    shoreline = boundary

elif isinstance(boundary, MultiLineString):
    shoreline = boundary

else:
    shoreline = boundary


# ------------------------------------------------------------
# 5. CREATE SHORELINE GEODATAFRAME
# ------------------------------------------------------------

shoreline_gdf = gpd.GeoDataFrame(
    {"reference": ["coastal_village_belt_boundary"]},
    geometry=[shoreline],
    crs=gdf.crs,
)


# ------------------------------------------------------------
# 6. CALCULATE VILLAGE DISTANCE
# ------------------------------------------------------------
#
# EPSG:7755 is projected, so distances are calculated in metres.
# ------------------------------------------------------------

print("\nCalculating distance to coastal reference...")

gdf["shoreline_distance_m"] = (
    gdf.geometry
    .centroid
    .distance(shoreline)
)

gdf["shoreline_distance_km"] = (
    gdf["shoreline_distance_m"] / 1000.0
)


# ------------------------------------------------------------
# 7. NORMALIZE DISTANCE
# ------------------------------------------------------------
#
# Villages closer to the coastal reference receive a higher
# proximity score.
#
# Closest village = 1
# Farthest village = 0
# ------------------------------------------------------------

distance_min = gdf["shoreline_distance_km"].min()
distance_max = gdf["shoreline_distance_km"].max()

if distance_max > distance_min:

    gdf["shoreline_proximity_score"] = (
        1.0
        - (
            (gdf["shoreline_distance_km"] - distance_min)
            / (distance_max - distance_min)
        )
    )

else:

    gdf["shoreline_proximity_score"] = 1.0


# ------------------------------------------------------------
# 8. CLASSIFY PROXIMITY
# ------------------------------------------------------------

def classify_proximity(score):

    if score < 0.25:
        return "LOW"

    elif score < 0.50:
        return "MODERATE"

    elif score < 0.75:
        return "HIGH"

    else:
        return "VERY HIGH"


gdf["shoreline_proximity_category"] = (
    gdf["shoreline_proximity_score"]
    .apply(classify_proximity)
)


# ------------------------------------------------------------
# 9. ADD DATA QUALITY / PROVENANCE
# ------------------------------------------------------------

gdf["shoreline_method"] = (
    "Distance from village centroid to outer boundary "
    "of Kendrapara coastal-village belt"
)

gdf["shoreline_data_quality"] = (
    "PROXY_REFERENCE"
)

gdf["official_shoreline_used"] = False


# ------------------------------------------------------------
# 10. JOIN EXISTING FEATURES
# ------------------------------------------------------------

print("\nJoining existing exposure features...")

features["vlcode_join"] = (
    features["vlcode"]
    .astype(str)
    .str.strip()
)

gdf["vlcode_join"] = (
    gdf["vlcode"]
    .astype(str)
    .str.strip()
)

join_columns = [
    "vlcode_join",
    "area_km2",
    "coastal_exposure_score",
]

gdf = gdf.merge(
    features[join_columns],
    on="vlcode_join",
    how="left",
    suffixes=("", "_existing"),
)


# ------------------------------------------------------------
# 11. CHECK JOIN
# ------------------------------------------------------------

missing_exposure = (
    gdf["coastal_exposure_score"]
    .isna()
    .sum()
)

if missing_exposure != 0:
    print(
        f"\nERROR: {missing_exposure} villages "
        "lost their exposure score."
    )
    raise SystemExit(1)


# ------------------------------------------------------------
# 12. REMOVE TEMPORARY COLUMNS
# ------------------------------------------------------------

gdf = gdf.drop(
    columns=["vlcode_join"]
)


if "area_km2_existing" in gdf.columns:
    gdf = gdf.drop(
        columns=["area_km2_existing"]
    )


# ------------------------------------------------------------
# 13. SAVE GEOJSON
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
# 14. SAVE CSV
# ------------------------------------------------------------

output_columns = [
    "village",
    "vlcode",
    "block",
    "district",
    "area_km2",
    "coastal_exposure_score",
    "shoreline_distance_m",
    "shoreline_distance_km",
    "shoreline_proximity_score",
    "shoreline_proximity_category",
    "shoreline_method",
    "shoreline_data_quality",
    "official_shoreline_used",
]

result = gdf[output_columns].copy()

OUTPUT_CSV.parent.mkdir(
    parents=True,
    exist_ok=True
)

result.to_csv(
    OUTPUT_CSV,
    index=False
)


# ------------------------------------------------------------
# 15. PRINT STATISTICS
# ------------------------------------------------------------

print("\nShoreline distance statistics:")

print(
    f"  Minimum: "
    f"{gdf['shoreline_distance_km'].min():.4f} km"
)

print(
    f"  Mean: "
    f"{gdf['shoreline_distance_km'].mean():.4f} km"
)

print(
    f"  Maximum: "
    f"{gdf['shoreline_distance_km'].max():.4f} km"
)


print("\nShoreline proximity score statistics:")

print(
    f"  Minimum: "
    f"{gdf['shoreline_proximity_score'].min():.4f}"
)

print(
    f"  Mean: "
    f"{gdf['shoreline_proximity_score'].mean():.4f}"
)

print(
    f"  Maximum: "
    f"{gdf['shoreline_proximity_score'].max():.4f}"
)


print("\nProximity category distribution:")

distribution = (
    gdf["shoreline_proximity_category"]
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


print("\nSaved spatial layer:")
print(OUTPUT_GEOJSON.resolve())

print("\nSaved feature table:")
print(OUTPUT_CSV.resolve())


print("\n" + "=" * 70)
print("✓ SHORELINE PROXIMITY GENERATION COMPLETE")
print("=" * 70)