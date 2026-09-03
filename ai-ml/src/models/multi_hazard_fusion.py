from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

COASTAL_FILE = (
    PROJECT_ROOT / "data" / "processed" / "coastal"
    / "kendrapara_village_coastal_hazard.geojson"
)

FLOOD_FILE = (
    PROJECT_ROOT / "data" / "processed" / "flood"
    / "kendrapara_flood_hazard.geojson"
)

CYCLONE_FILE = (
    PROJECT_ROOT / "data" / "processed" / "cyclone"
    / "kendrapara_cyclone_hazard.geojson"
)

RAINFALL_FILE = (
    PROJECT_ROOT / "data" / "processed" / "rainfall"
    / "kendrapara_rainfall_features.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT / "data" / "processed" / "multi_hazard"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_GEOJSON = (
    OUTPUT_DIR / "kendrapara_multi_hazard_risk.geojson"
)

OUTPUT_CSV = (
    OUTPUT_DIR / "kendrapara_multi_hazard_summary.csv"
)


print("=" * 70)
print("KENDRAPARA 4-HAZARD MULTI-HAZARD FUSION")
print("=" * 70)


# ============================================================
# LOAD
# ============================================================

print("\n[1] Loading hazard layers...")

coastal_gdf = gpd.read_file(COASTAL_FILE)
flood_gdf = gpd.read_file(FLOOD_FILE)
cyclone_gdf = gpd.read_file(CYCLONE_FILE)
rainfall_gdf = gpd.read_file(RAINFALL_FILE)

print(f"Coastal villages: {len(coastal_gdf)}")
print(f"Flood villages: {len(flood_gdf)}")
print(f"Cyclone villages: {len(cyclone_gdf)}")
print(f"Rainfall villages: {len(rainfall_gdf)}")


# ============================================================
# CREATE ATTRIBUTE TABLES
# ============================================================

coastal = coastal_gdf[
    ["village", "vlcode", "coastal_hazard_score"]
].copy()

flood = flood_gdf[
    ["village", "vlcode", "flood_hazard_score"]
].copy()

cyclone = cyclone_gdf[
    ["village", "vlcode", "cyclone_hazard_score"]
].copy()

rainfall = rainfall_gdf[
    ["village", "vlcode", "rainfall_hazard_score"]
].copy()


# ============================================================
# MERGE
# ============================================================

print("\n[2] Merging hazard layers...")

base = coastal.merge(
    flood,
    on=["village", "vlcode"],
    how="left"
)

base = base.merge(
    cyclone,
    on=["village", "vlcode"],
    how="left"
)

base = base.merge(
    rainfall,
    on=["village", "vlcode"],
    how="left"
)

print(f"Merged villages: {len(base)}")


# ============================================================
# HAZARD WEIGHTS
# ============================================================

WEIGHTS = {
    "coastal_hazard_score": 0.30,
    "flood_hazard_score": 0.25,
    "cyclone_hazard_score": 0.25,
    "rainfall_hazard_score": 0.20,
}


# ============================================================
# AVAILABILITY-AWARE FUSION
# ============================================================

print("\n[3] Calculating availability-aware multi-hazard risk...")

scores = []
contributions = []
hazards_available = []

for _, row in base.iterrows():

    weighted_sum = 0.0
    weight_sum = 0.0
    available = []

    for hazard, weight in WEIGHTS.items():

        value = row[hazard]

        if pd.notna(value):

            value = float(
                np.clip(float(value), 0.0, 1.0)
            )

            weighted_sum += value * weight
            weight_sum += weight

            available.append(
                hazard.replace(
                    "_hazard_score",
                    ""
                ).upper()
            )

    if weight_sum > 0:
        final_score = weighted_sum / weight_sum
    else:
        final_score = np.nan

    scores.append(final_score)

    contributions.append(
        " + ".join(available)
        if available
        else "NO_DATA"
    )

    hazards_available.append(
        len(available)
    )


base["multi_hazard_score"] = scores

base["hazards_available"] = hazards_available

base["hazard_contribution"] = contributions


# ============================================================
# CLASSIFICATION
# ============================================================

def classify(score):

    if pd.isna(score):
        return "NO_DATA"

    if score < 0.25:
        return "LOW"

    if score < 0.50:
        return "MODERATE"

    if score < 0.75:
        return "HIGH"

    return "VERY HIGH"


base["multi_hazard_category"] = (
    base["multi_hazard_score"]
    .apply(classify)
)


# ============================================================
# ATTACH ORIGINAL GEOMETRY
# ============================================================

print("\n[4] Attaching village geometry...")

geometry = coastal_gdf[
    ["village", "vlcode", "geometry"]
].copy()

result = geometry.merge(
    base,
    on=["village", "vlcode"],
    how="left"
)

result = gpd.GeoDataFrame(
    result,
    geometry="geometry",
    crs=coastal_gdf.crs
)


# ============================================================
# SAVE GEOJSON
# ============================================================

print("\n[5] Saving multi-hazard layer...")

result.to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON"
)

print(
    f"GeoJSON saved: {OUTPUT_GEOJSON}"
)


# ============================================================
# SAVE CSV
# ============================================================

summary_columns = [
    "village",
    "vlcode",
    "coastal_hazard_score",
    "flood_hazard_score",
    "cyclone_hazard_score",
    "rainfall_hazard_score",
    "multi_hazard_score",
    "multi_hazard_category",
    "hazards_available",
    "hazard_contribution",
]

summary = base[summary_columns].copy()

summary.to_csv(
    OUTPUT_CSV,
    index=False
)

print(
    f"CSV saved: {OUTPUT_CSV}"
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("4-HAZARD FUSION SUMMARY")
print("=" * 70)

print(
    f"Total villages: {len(result)}"
)

print("\nHazard availability:")

print(
    result["hazards_available"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nHazard combinations:")

print(
    result["hazard_contribution"]
    .value_counts()
    .to_string()
)

print("\nMulti-hazard risk distribution:")

print(
    result["multi_hazard_category"]
    .value_counts()
    .to_string()
)

valid_scores = result[
    result["multi_hazard_score"].notna()
]["multi_hazard_score"]

if len(valid_scores) > 0:

    print("\nMulti-hazard score statistics:")

    print(
        valid_scores
        .describe()
        .round(4)
    )


# ============================================================
# TOP 10
# ============================================================

print("\nTop 10 highest-risk villages:")

top10 = (
    result[
        [
            "village",
            "multi_hazard_score",
            "multi_hazard_category",
            "coastal_hazard_score",
            "flood_hazard_score",
            "cyclone_hazard_score",
            "rainfall_hazard_score",
        ]
    ]
    .sort_values(
        "multi_hazard_score",
        ascending=False
    )
    .head(10)
)

print(
    top10.to_string(index=False)
)


print("\n" + "=" * 70)
print("✓ KENDRAPARA 4-HAZARD FUSION COMPLETE")
print("=" * 70)