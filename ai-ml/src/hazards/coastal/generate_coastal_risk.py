from pathlib import Path

import geopandas as gpd
import pandas as pd


# ============================================================
# AASHRAY - KENDRAPARA VILLAGE-LEVEL COASTAL HAZARD
# ============================================================

INPUT_SHORELINE = Path(
    "data/processed/features/"
    "kendrapara_shoreline_proximity_features.csv"
)

INPUT_EROSION = Path(
    "data/processed/features/"
    "kendrapara_coastal_erosion_features.csv"
)

INPUT_GEOMETRY = Path(
    "data/processed/administrative/"
    "kendrapara_coastal_villages.geojson"
)

OUTPUT_GEOJSON = Path(
    "data/processed/coastal/"
    "kendrapara_village_coastal_hazard.geojson"
)

OUTPUT_CSV = Path(
    "data/processed/coastal/"
    "kendrapara_village_coastal_hazard_summary.csv"
)


print("=" * 70)
print("AASHRAY KENDRAPARA VILLAGE-LEVEL COASTAL HAZARD")
print("=" * 70)


# ------------------------------------------------------------
# 1. LOAD SHORELINE PROXIMITY
# ------------------------------------------------------------

print("\nLoading shoreline proximity features...")

shoreline = pd.read_csv(INPUT_SHORELINE)

print(f"Rows: {len(shoreline)}")


# ------------------------------------------------------------
# 2. LOAD NCCR EROSION BASELINE
# ------------------------------------------------------------

print("\nLoading NCCR erosion baseline...")

erosion = pd.read_csv(INPUT_EROSION)

print(f"Rows: {len(erosion)}")


# ------------------------------------------------------------
# 3. LOAD VILLAGE GEOMETRIES
# ------------------------------------------------------------

print("\nLoading village geometries...")

gdf = gpd.read_file(INPUT_GEOMETRY)

print(f"Geometries: {len(gdf)}")


# ------------------------------------------------------------
# 4. CHECK REQUIRED COLUMNS
# ------------------------------------------------------------

shoreline_required = [
    "village",
    "vlcode",
    "block",
    "district",
    "coastal_exposure_score",
    "shoreline_distance_km",
    "shoreline_proximity_score",
]

erosion_required = [
    "village",
    "vlcode",
    "erosion_baseline_score",
    "coastal_hazard_baseline",
]

for column in shoreline_required:

    if column not in shoreline.columns:
        raise SystemExit(
            f"ERROR: Missing shoreline column: {column}"
        )

for column in erosion_required:

    if column not in erosion.columns:
        raise SystemExit(
            f"ERROR: Missing erosion column: {column}"
        )


# ------------------------------------------------------------
# 5. PREPARE JOIN KEYS
# ------------------------------------------------------------

shoreline["vlcode_join"] = (
    shoreline["vlcode"]
    .astype(str)
    .str.strip()
)

erosion["vlcode_join"] = (
    erosion["vlcode"]
    .astype(str)
    .str.strip()
)

gdf["vlcode_join"] = (
    gdf["vlcode"]
    .astype(str)
    .str.strip()
)


# ------------------------------------------------------------
# 6. MERGE NCCR BASELINE
# ------------------------------------------------------------

print("\nCombining NCCR baseline with shoreline features...")

features = shoreline.merge(
    erosion[
        [
            "vlcode_join",
            "erosion_baseline_score",
            "coastal_hazard_baseline",
        ]
    ],
    on="vlcode_join",
    how="left",
)


# ------------------------------------------------------------
# 7. CHECK MERGE
# ------------------------------------------------------------

missing_baseline = (
    features["erosion_baseline_score"]
    .isna()
    .sum()
)

if missing_baseline != 0:

    raise SystemExit(
        f"ERROR: {missing_baseline} villages "
        "have no NCCR baseline."
    )


# ------------------------------------------------------------
# 8. CREATE VILLAGE-LEVEL COASTAL HAZARD
# ------------------------------------------------------------
#
# Components:
#
#   40% NCCR erosion baseline
#   60% shoreline proximity
#
# Why?
#
# NCCR gives the regional erosion signal.
# Shoreline proximity gives spatial differentiation.
#
# IMPORTANT:
# This is a MODELLED HAZARD SCORE, not a measured
# village-specific erosion rate.
# ------------------------------------------------------------

features["coastal_hazard_score"] = (
    0.40 * features["erosion_baseline_score"]
    + 0.60 * features["shoreline_proximity_score"]
)


# ------------------------------------------------------------
# 9. CLASSIFY HAZARD
# ------------------------------------------------------------

def classify_hazard(score):

    if score < 0.3333:
        return "LOW"

    elif score < 0.6667:
        return "MODERATE"

    elif score < 0.8333:
        return "HIGH"

    else:
        return "VERY HIGH"


features["coastal_hazard_category"] = (
    features["coastal_hazard_score"]
    .apply(classify_hazard)
)


# ------------------------------------------------------------
# 10. ADD MODEL INFORMATION
# ------------------------------------------------------------

features["hazard_model"] = (
    "0.40*NCCR_erosion_baseline + "
    "0.60*shoreline_proximity"
)

features["hazard_data_quality"] = (
    "MODELLED_PROXY"
)

features["village_erosion_rate_available"] = False

features["official_shoreline_used"] = False


# ------------------------------------------------------------
# 11. JOIN WITH GEOMETRIES
# ------------------------------------------------------------

print("\nAttaching hazard scores to village geometries...")

join_columns = [
    "vlcode_join",
    "coastal_hazard_score",
    "coastal_hazard_category",
    "shoreline_distance_km",
    "shoreline_proximity_score",
    "erosion_baseline_score",
    "hazard_model",
    "hazard_data_quality",
]

hazard = gdf.merge(
    features[join_columns],
    on="vlcode_join",
    how="left",
)


# ------------------------------------------------------------
# 12. CHECK SPATIAL JOIN
# ------------------------------------------------------------

missing_hazard = (
    hazard["coastal_hazard_score"]
    .isna()
    .sum()
)

if missing_hazard != 0:

    raise SystemExit(
        f"ERROR: {missing_hazard} villages "
        "have no coastal hazard score."
    )


# ------------------------------------------------------------
# 13. REMOVE TEMPORARY COLUMN
# ------------------------------------------------------------

hazard = hazard.drop(
    columns=["vlcode_join"]
)


# ------------------------------------------------------------
# 14. SAVE GEOJSON
# ------------------------------------------------------------

OUTPUT_GEOJSON.parent.mkdir(
    parents=True,
    exist_ok=True
)

hazard.to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON"
)


# ------------------------------------------------------------
# 15. CREATE SUMMARY TABLE
# ------------------------------------------------------------

summary_columns = [
    "village",
    "vlcode",
    "block",
    "district",
    "shoreline_distance_km",
    "shoreline_proximity_score",
    "erosion_baseline_score",
    "coastal_hazard_score",
    "coastal_hazard_category",
    "hazard_model",
    "hazard_data_quality",
]

summary = hazard[summary_columns].copy()

summary = summary.sort_values(
    "coastal_hazard_score",
    ascending=False
)

summary.to_csv(
    OUTPUT_CSV,
    index=False
)


# ------------------------------------------------------------
# 16. PRINT SCORE STATISTICS
# ------------------------------------------------------------

print("\nCoastal hazard score statistics:")

print(
    f"  Minimum: "
    f"{hazard['coastal_hazard_score'].min():.4f}"
)

print(
    f"  Mean: "
    f"{hazard['coastal_hazard_score'].mean():.4f}"
)

print(
    f"  Maximum: "
    f"{hazard['coastal_hazard_score'].max():.4f}"
)


# ------------------------------------------------------------
# 17. CATEGORY DISTRIBUTION
# ------------------------------------------------------------

print("\nCoastal hazard category distribution:")

distribution = (
    hazard["coastal_hazard_category"]
    .value_counts()
    .sort_index()
)

for category, count in distribution.items():

    percentage = (
        count / len(hazard)
    ) * 100

    print(
        f"  {category}: "
        f"{count} villages "
        f"({percentage:.2f}%)"
    )


# ------------------------------------------------------------
# 18. TOP 10 HIGHEST-RISK VILLAGES
# ------------------------------------------------------------

print("\nTop 10 coastal hazard villages:")

top10 = (
    summary.head(10)
)

for _, row in top10.iterrows():

    print(
        f"  {row['village']} | "
        f"{row['block']} | "
        f"score={row['coastal_hazard_score']:.4f} | "
        f"{row['coastal_hazard_category']} | "
        f"distance={row['shoreline_distance_km']:.2f} km"
    )


# ------------------------------------------------------------
# 19. OUTPUT PATHS
# ------------------------------------------------------------

print("\nSaved coastal hazard layer:")
print(OUTPUT_GEOJSON.resolve())

print("\nSaved coastal hazard summary:")
print(OUTPUT_CSV.resolve())


print("\n" + "=" * 70)
print("✓ VILLAGE-LEVEL COASTAL HAZARD GENERATION COMPLETE")
print("=" * 70)
