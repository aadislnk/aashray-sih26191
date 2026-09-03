from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

GEOJSON_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "multi_hazard"
    / "kendrapara_multi_hazard_risk.geojson"
)

CSV_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "multi_hazard"
    / "kendrapara_multi_hazard_summary.csv"
)


# ============================================================
# LOAD
# ============================================================

print("=" * 70)
print("KENDRAPARA 4-HAZARD VALIDATION")
print("=" * 70)

print("\n[1] Loading outputs...")

gdf = gpd.read_file(GEOJSON_FILE)
df = pd.read_csv(CSV_FILE)

print(f"GeoJSON rows: {len(gdf)}")
print(f"CSV rows: {len(df)}")


# ============================================================
# BASIC ROW VALIDATION
# ============================================================

print("\n[2] Checking village records...")

assert len(gdf) == 808, (
    f"Expected 808 GeoJSON rows, got {len(gdf)}"
)

assert len(df) == 808, (
    f"Expected 808 CSV rows, got {len(df)}"
)

assert gdf["village"].notna().all()
assert gdf["vlcode"].notna().all()

assert df["village"].notna().all()
assert df["vlcode"].notna().all()

print("✓ 808 villages present")
print("✓ No missing village names")
print("✓ No missing village codes")


# ============================================================
# DUPLICATE VALIDATION
# ============================================================

print("\n[3] Checking duplicate village codes...")

geo_duplicates = gdf["vlcode"].duplicated().sum()
csv_duplicates = df["vlcode"].duplicated().sum()

print(f"GeoJSON duplicates: {geo_duplicates}")
print(f"CSV duplicates: {csv_duplicates}")

assert geo_duplicates == 0
assert csv_duplicates == 0

print("✓ No duplicate village codes")


# ============================================================
# REQUIRED COLUMNS
# ============================================================

print("\n[4] Checking required hazard columns...")

required_columns = [
    "coastal_hazard_score",
    "flood_hazard_score",
    "cyclone_hazard_score",
    "rainfall_hazard_score",
    "multi_hazard_score",
    "multi_hazard_category",
    "hazards_available",
    "hazard_contribution",
]

for column in required_columns:

    assert column in gdf.columns, (
        f"Missing column: {column}"
    )

print("✓ All required columns present")


# ============================================================
# SCORE RANGE VALIDATION
# ============================================================

print("\n[5] Checking hazard score ranges...")

hazard_columns = [
    "coastal_hazard_score",
    "flood_hazard_score",
    "cyclone_hazard_score",
    "rainfall_hazard_score",
    "multi_hazard_score",
]

for column in hazard_columns:

    values = gdf[column].dropna()

    assert (values >= 0).all(), (
        f"{column} contains values below 0"
    )

    assert (values <= 1).all(), (
        f"{column} contains values above 1"
    )

    print(
        f"{column}: "
        f"min={values.min():.4f}, "
        f"max={values.max():.4f}, "
        f"mean={values.mean():.4f}"
    )

print("✓ All scores are within 0–1")


# ============================================================
# RAINFALL NO-DATA VALIDATION
# ============================================================

print("\n[6] Checking rainfall NO_DATA handling...")

rainfall_missing = (
    gdf["rainfall_hazard_score"].isna()
)

print(
    f"Rainfall NO_DATA villages: "
    f"{rainfall_missing.sum()}"
)

assert rainfall_missing.sum() == 23

print("✓ Exactly 23 rainfall NO_DATA villages")


# ============================================================
# HAZARD AVAILABILITY
# ============================================================

print("\n[7] Checking hazard availability...")

availability = (
    gdf["hazards_available"]
    .value_counts()
    .sort_index()
)

print(availability.to_string())

assert availability.get(4, 0) == 785
assert availability.get(3, 0) == 23

print("✓ 785 villages have all 4 hazards")
print("✓ 23 villages have 3 hazards")


# ============================================================
# FUSION MATHEMATICS
# ============================================================

print("\n[8] Validating fusion calculation...")

weights = {
    "coastal_hazard_score": 0.30,
    "flood_hazard_score": 0.25,
    "cyclone_hazard_score": 0.25,
    "rainfall_hazard_score": 0.20,
}

calculated_scores = []

for _, row in gdf.iterrows():

    weighted_sum = 0.0
    weight_sum = 0.0

    for hazard, weight in weights.items():

        value = row[hazard]

        if pd.notna(value):

            weighted_sum += float(value) * weight
            weight_sum += weight

    if weight_sum > 0:

        expected = weighted_sum / weight_sum

    else:

        expected = np.nan

    calculated_scores.append(expected)


calculated_scores = np.array(
    calculated_scores,
    dtype=float
)

actual_scores = gdf[
    "multi_hazard_score"
].to_numpy(dtype=float)

differences = np.abs(
    calculated_scores - actual_scores
)

max_difference = np.nanmax(differences)

print(
    f"Maximum fusion difference: "
    f"{max_difference:.12f}"
)

assert max_difference < 1e-9

print("✓ Fusion mathematics is correct")


# ============================================================
# CATEGORY VALIDATION
# ============================================================

print("\n[9] Checking risk categories...")

def expected_category(score):

    if pd.isna(score):
        return "NO_DATA"

    if score < 0.25:
        return "LOW"

    if score < 0.50:
        return "MODERATE"

    if score < 0.75:
        return "HIGH"

    return "VERY HIGH"


expected_categories = (
    gdf["multi_hazard_score"]
    .apply(expected_category)
)

category_matches = (
    expected_categories
    == gdf["multi_hazard_category"]
)

assert category_matches.all()

print("✓ All risk categories match scores")


# ============================================================
# GEOMETRY VALIDATION
# ============================================================

print("\n[10] Checking spatial geometry...")

print(f"CRS: {gdf.crs}")

assert gdf.crs is not None
assert gdf.crs.to_epsg() == 7755

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

assert empty_geometries == 0
assert invalid_geometries == 0

print("✓ CRS is EPSG:7755")
print("✓ No empty geometries")
print("✓ No invalid geometries")


# ============================================================
# CSV ↔ GEOJSON CONSISTENCY
# ============================================================

print("\n[11] Checking CSV and GeoJSON consistency...")

geo_codes = set(
    gdf["vlcode"].astype(str)
)

csv_codes = set(
    df["vlcode"].astype(str)
)

assert geo_codes == csv_codes

print("✓ CSV and GeoJSON village codes match")


# ============================================================
# RISK DISTRIBUTION
# ============================================================

print("\n[12] Final risk distribution...")

distribution = (
    gdf["multi_hazard_category"]
    .value_counts()
)

print(
    distribution.to_string()
)


# ============================================================
# FINAL STATISTICS
# ============================================================

print("\nFinal multi-hazard statistics:")

print(
    gdf["multi_hazard_score"]
    .describe()
    .round(4)
)


# ============================================================
# FINAL RESULT
# ============================================================

print("\n" + "=" * 70)
print("✓ KENDRAPARA 4-HAZARD VALIDATION PASSED")
print("=" * 70)