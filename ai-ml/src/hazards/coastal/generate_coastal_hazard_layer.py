from pathlib import Path
import geopandas as gpd
import pandas as pd


INPUT_GEOJSON = Path(
    "data/processed/administrative/"
    "kendrapara_coastal_villages.geojson"
)

INPUT_FEATURES = Path(
    "data/processed/features/"
    "kendrapara_coastal_erosion_features.csv"
)

OUTPUT_GEOJSON = Path(
    "data/processed/coastal/"
    "kendrapara_coastal_hazard.geojson"
)

OUTPUT_SUMMARY = Path(
    "data/processed/coastal/"
    "kendrapara_coastal_hazard_summary.csv"
)


print("=" * 70)
print("AASHRAY KENDRAPARA COASTAL HAZARD LAYER")
print("=" * 70)


# ---------------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------------

print("\nLoading village boundaries...")

gdf = gpd.read_file(INPUT_GEOJSON)

print(f"Village geometries: {len(gdf)}")

print("\nLoading coastal features...")

features = pd.read_csv(INPUT_FEATURES)

print(f"Feature rows: {len(features)}")


# ---------------------------------------------------------------
# 2. KEEP ONLY REQUIRED FEATURE COLUMNS
# ---------------------------------------------------------------

required = [
    "village",
    "vlcode",
    "block",
    "district",
    "erosion_baseline_score",
    "coastal_hazard_baseline",
]

missing = [
    column
    for column in required
    if column not in features.columns
]

if missing:
    print("\nERROR: Missing columns:")
    print(missing)
    raise SystemExit(1)


features = features[required].copy()


# ---------------------------------------------------------------
# 3. PREPARE JOIN KEYS
# ---------------------------------------------------------------

gdf["vlcode_join"] = (
    gdf["vlcode"]
    .astype(str)
    .str.strip()
)

features["vlcode_join"] = (
    features["vlcode"]
    .astype(str)
    .str.strip()
)


# ---------------------------------------------------------------
# 4. JOIN FEATURES TO VILLAGE GEOMETRIES
# ---------------------------------------------------------------

print("\nJoining hazard features to village geometries...")

hazard = gdf.merge(
    features.drop(
        columns=["village", "block", "district"]
    ),
    on="vlcode_join",
    how="left",
    suffixes=("", "_feature"),
)


# ---------------------------------------------------------------
# 5. CHECK JOIN
# ---------------------------------------------------------------

missing_scores = (
    hazard["coastal_hazard_baseline"]
    .isna()
    .sum()
)

print(
    f"Villages without hazard score: "
    f"{missing_scores}"
)

if missing_scores != 0:
    print("\nERROR: Some villages were not matched.")
    raise SystemExit(1)


# ---------------------------------------------------------------
# 6. CREATE HAZARD CATEGORY
# ---------------------------------------------------------------
#
# Baseline score is 0.2938.
#
# Because this is a district-level baseline rather than a
# village-specific measured erosion rate, we label the result
# explicitly as BASELINE.
#
# Categories follow the AASHRAY 4-level convention:
#
# LOW       < 0.3333
# MODERATE  0.3333 - <0.6667
# HIGH      0.6667 - <0.8333
# VERY HIGH >=0.8333
# ---------------------------------------------------------------

def classify_hazard(score):

    if score < 0.3333:
        return "LOW"

    elif score < 0.6667:
        return "MODERATE"

    elif score < 0.8333:
        return "HIGH"

    else:
        return "VERY HIGH"


hazard["coastal_hazard_category"] = (
    hazard["coastal_hazard_baseline"]
    .apply(classify_hazard)
)


# ---------------------------------------------------------------
# 7. ADD DATA QUALITY FLAG
# ---------------------------------------------------------------

hazard["hazard_data_quality"] = (
    "DISTRICT_BASELINE"
)

hazard["village_erosion_rate_available"] = False

hazard["hazard_source"] = (
    "NCCR National Assessment of Shoreline Changes 1990-2016"
)


# ---------------------------------------------------------------
# 8. REMOVE TEMPORARY JOIN COLUMN
# ---------------------------------------------------------------

hazard = hazard.drop(
    columns=["vlcode_join"]
)


# ---------------------------------------------------------------
# 9. SAVE GEOJSON
# ---------------------------------------------------------------

OUTPUT_GEOJSON.parent.mkdir(
    parents=True,
    exist_ok=True
)

hazard.to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON"
)


# ---------------------------------------------------------------
# 10. CREATE SUMMARY
# ---------------------------------------------------------------

summary = (
    hazard
    .groupby(
        ["block", "coastal_hazard_category"],
        dropna=False
    )
    .size()
    .reset_index(name="village_count")
)

OUTPUT_SUMMARY.parent.mkdir(
    parents=True,
    exist_ok=True
)

summary.to_csv(
    OUTPUT_SUMMARY,
    index=False
)


# ---------------------------------------------------------------
# 11. PRINT RESULTS
# ---------------------------------------------------------------

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


print("\nBlock distribution:")

block_counts = (
    hazard["block"]
    .value_counts()
    .sort_index()
)

for block, count in block_counts.items():

    print(
        f"  {block}: {count} villages"
    )


print("\nSaved spatial layer:")
print(OUTPUT_GEOJSON.resolve())

print("\nSaved summary:")
print(OUTPUT_SUMMARY.resolve())


print("\n" + "=" * 70)
print("✓ COASTAL HAZARD LAYER GENERATION COMPLETE")
print("=" * 70)