import os
import numpy as np
import pandas as pd
import geopandas as gpd


# ============================================================
# AASHRAY - KENDRAPARA MULTI-HAZARD VALIDATION
# ============================================================

GEOJSON_FILE = (
    r"data\processed\multi_hazard"
    r"\kendrapara_multi_hazard_risk.geojson"
)

CSV_FILE = (
    r"data\processed\multi_hazard"
    r"\kendrapara_multi_hazard_summary.csv"
)


print("=" * 70)
print("AASHRAY - KENDRAPARA MULTI-HAZARD VALIDATION")
print("=" * 70)
print()


# ============================================================
# LOAD FILES
# ============================================================

print("Loading GeoJSON...")

gdf = gpd.read_file(
    GEOJSON_FILE
)

print(
    f"GeoJSON villages: {len(gdf):,}"
)

print()

print("Loading CSV...")

df = pd.read_csv(
    CSV_FILE
)

print(
    f"CSV villages: {len(df):,}"
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "village",
    "vlcode",
    "coastal_score",
    "flood_score",
    "cyclone_score",
    "multi_hazard_score",
    "risk_category",
    "hazards_available"
]

missing_csv = [
    col
    for col in required_columns
    if col not in df.columns
]

missing_geojson = [
    col
    for col in required_columns
    if col not in gdf.columns
]

if missing_csv:
    raise ValueError(
        f"CSV missing columns: {missing_csv}"
    )

if missing_geojson:
    raise ValueError(
        f"GeoJSON missing columns: {missing_geojson}"
    )

print()
print("✓ Required columns present")


# ============================================================
# VILLAGE IDENTIFIERS
# ============================================================

missing_names = (
    df["village"]
    .isna()
    .sum()
)

missing_codes = (
    df["vlcode"]
    .isna()
    .sum()
)

duplicate_codes = (
    df["vlcode"]
    .duplicated()
    .sum()
)

print()
print(
    f"Missing village names: {missing_names}"
)

print(
    f"Missing village codes: {missing_codes}"
)

print(
    f"Duplicate village codes: {duplicate_codes}"
)

if (
    missing_names > 0
    or missing_codes > 0
    or duplicate_codes > 0
):
    raise ValueError(
        "Village identifier validation failed."
    )

print(
    "✓ Village identifiers valid"
)


# ============================================================
# DISTRICT
# ============================================================

if "district" in gdf.columns:

    districts = (
        gdf["district"]
        .dropna()
        .astype(str)
        .str.lower()
        .unique()
    )

    print()
    print(
        f"Districts found: {list(districts)}"
    )


# ============================================================
# SCORE VALIDATION
# ============================================================

score_columns = [
    "coastal_score",
    "flood_score",
    "cyclone_score",
    "multi_hazard_score"
]

print()
print("Checking score ranges...")

for column in score_columns:

    values = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    invalid = (
        values.isna().sum()
        +
        ((values < 0) | (values > 1)).sum()
    )

    print(
        f"{column}: "
        f"min={values.min():.4f}, "
        f"mean={values.mean():.4f}, "
        f"max={values.max():.4f}, "
        f"invalid={invalid}"
    )

    if invalid > 0:
        raise ValueError(
            f"Invalid values found in {column}"
        )

print()
print("✓ Score ranges valid")


# ============================================================
# VERIFY FUSION MATHEMATICALLY
# ============================================================

expected_score = (
    0.35 * df["coastal_score"]
    +
    0.30 * df["flood_score"]
    +
    0.35 * df["cyclone_score"]
)

difference = (
    df["multi_hazard_score"]
    - expected_score
).abs()

max_difference = difference.max()

print()
print(
    "Maximum fusion calculation difference: "
    f"{max_difference:.10f}"
)

if max_difference > 0.00001:

    raise ValueError(
        "Multi-hazard fusion calculation failed."
    )

print(
    "✓ Fusion mathematics validated"
)


# ============================================================
# VERIFY ALL THREE HAZARDS
# ============================================================

print()
print("Checking hazard availability...")

combination_counts = (
    df["hazards_available"]
    .value_counts()
)

print(
    combination_counts.to_string()
)

expected_combination = (
    "COASTAL + FLOOD + CYCLONE"
)

full_count = (
    df["hazards_available"]
    == expected_combination
).sum()

print()

print(
    f"Villages with all 3 hazards: "
    f"{full_count:,}/{len(df):,}"
)

if full_count != len(df):

    raise ValueError(
        "Not all villages have all three hazards."
    )

print(
    "✓ All three hazards available"
)


# ============================================================
# RISK CATEGORY VALIDATION
# ============================================================

valid_categories = [
    "LOW",
    "MODERATE",
    "HIGH",
    "VERY HIGH"
]

invalid_categories = (
    ~df["risk_category"]
    .isin(valid_categories)
).sum()

print()
print(
    f"Invalid risk categories: "
    f"{invalid_categories}"
)

if invalid_categories > 0:

    raise ValueError(
        "Invalid risk categories found."
    )

print(
    "✓ Risk categories valid"
)


# ============================================================
# GEOMETRY VALIDATION
# ============================================================

print()
print("Checking geometry...")

if gdf.crs is None:

    raise ValueError(
        "GeoJSON has no CRS."
    )

print(
    f"CRS: {gdf.crs}"
)

empty_geometries = (
    gdf.geometry.is_empty.sum()
)

invalid_geometries = (
    (~gdf.geometry.is_valid).sum()
)

print(
    f"Empty geometries: "
    f"{empty_geometries}"
)

print(
    f"Invalid geometries: "
    f"{invalid_geometries}"
)

if (
    empty_geometries > 0
    or invalid_geometries > 0
):

    raise ValueError(
        "Geometry validation failed."
    )

print(
    "✓ Geometry valid"
)


# ============================================================
# CHECK CSV / GEOJSON MATCH
# ============================================================

csv_codes = set(
    df["vlcode"].astype(str)
)

geojson_codes = set(
    gdf["vlcode"].astype(str)
)

missing_in_geojson = (
    csv_codes - geojson_codes
)

missing_in_csv = (
    geojson_codes - csv_codes
)

print()
print(
    f"CSV codes missing from GeoJSON: "
    f"{len(missing_in_geojson)}"
)

print(
    f"GeoJSON codes missing from CSV: "
    f"{len(missing_in_csv)}"
)

if (
    missing_in_geojson
    or missing_in_csv
):

    raise ValueError(
        "CSV and GeoJSON village sets do not match."
    )

print(
    "✓ CSV and GeoJSON match"
)


# ============================================================
# RISK DISTRIBUTION
# ============================================================

print()
print("Final risk distribution:")

distribution = (
    df["risk_category"]
    .value_counts()
    .reindex(
        valid_categories,
        fill_value=0
    )
)

print(
    distribution.to_string()
)


# ============================================================
# TOP VILLAGES
# ============================================================

print()
print("Top 10 multi-hazard villages:")

top10 = (
    df
    .sort_values(
        "multi_hazard_score",
        ascending=False
    )
    .head(10)
)

print(
    top10[
        [
            "village",
            "multi_hazard_score",
            "risk_category",
            "coastal_score",
            "flood_score",
            "cyclone_score"
        ]
    ].to_string(
        index=False
    )
)


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 70)
print("✓ KENDRAPARA MULTI-HAZARD VALIDATION PASSED")
print("=" * 70)