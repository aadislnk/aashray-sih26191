from pathlib import Path
import pandas as pd


INPUT = Path(
    "data/processed/features/"
    "kendrapara_coastal_erosion_features.csv"
)


print("=" * 70)
print("AASHRAY COASTAL FEATURE VALIDATION")
print("=" * 70)


df = pd.read_csv(INPUT)


print(f"\nRows: {len(df)}")
print(f"Columns: {len(df.columns)}")


# ---------------------------------------------------------------
# Required columns
# ---------------------------------------------------------------

required_columns = [
    "village",
    "vlcode",
    "block",
    "district",
    "nccr_total_coast_km",
    "nccr_high_erosion_km",
    "nccr_moderate_erosion_km",
    "nccr_low_erosion_km",
    "nccr_stable_km",
    "nccr_low_accretion_km",
    "nccr_moderate_accretion_km",
    "nccr_high_accretion_km",
    "erosion_baseline_score",
    "coastal_hazard_baseline",
]


missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


print("\nRequired-column check:")

if missing_columns:
    print("  FAILED")
    print("  Missing:", missing_columns)
    raise SystemExit(1)

else:
    print("  PASSED")


# ---------------------------------------------------------------
# Village checks
# ---------------------------------------------------------------

print("\nVillage checks:")

missing_villages = df["village"].isna().sum()
missing_codes = df["vlcode"].isna().sum()
duplicate_codes = df["vlcode"].duplicated().sum()

print(f"  Missing village names: {missing_villages}")
print(f"  Missing village codes: {missing_codes}")
print(f"  Duplicate village codes: {duplicate_codes}")


# ---------------------------------------------------------------
# District check
# ---------------------------------------------------------------

districts = df["district"].dropna().unique()

print("\nDistricts:")
for district in districts:
    print(f"  {district}")


# ---------------------------------------------------------------
# Block distribution
# ---------------------------------------------------------------

print("\nCoastal villages by block:")

block_counts = (
    df["block"]
    .value_counts()
    .sort_index()
)

for block, count in block_counts.items():
    print(f"  {block}: {count}")


# ---------------------------------------------------------------
# Baseline checks
# ---------------------------------------------------------------

baseline_values = (
    df["erosion_baseline_score"]
    .dropna()
    .unique()
)

hazard_values = (
    df["coastal_hazard_baseline"]
    .dropna()
    .unique()
)

print("\nBaseline checks:")

print(
    f"  Unique erosion baseline values: "
    f"{len(baseline_values)}"
)

print(
    f"  Unique coastal hazard values: "
    f"{len(hazard_values)}"
)

if len(baseline_values) == 1:

    print(
        f"  Baseline score: "
        f"{baseline_values[0]:.4f}"
    )


# ---------------------------------------------------------------
# NCCR coastline consistency
# ---------------------------------------------------------------

total_coast = df["nccr_total_coast_km"].iloc[0]

erosion_total = (
    df["nccr_high_erosion_km"].iloc[0]
    + df["nccr_moderate_erosion_km"].iloc[0]
    + df["nccr_low_erosion_km"].iloc[0]
)

stable_total = df["nccr_stable_km"].iloc[0]

accretion_total = (
    df["nccr_low_accretion_km"].iloc[0]
    + df["nccr_moderate_accretion_km"].iloc[0]
    + df["nccr_high_accretion_km"].iloc[0]
)

combined_total = (
    erosion_total
    + stable_total
    + accretion_total
)

print("\nNCCR coastline consistency:")

print(f"  Total reported: {total_coast:.2f} km")
print(f"  Erosion: {erosion_total:.2f} km")
print(f"  Stable: {stable_total:.2f} km")
print(f"  Accretion: {accretion_total:.2f} km")
print(f"  Combined: {combined_total:.2f} km")


# ---------------------------------------------------------------
# Final validation
# ---------------------------------------------------------------

passed = True

if len(df) != 808:
    passed = False

if missing_villages != 0:
    passed = False

if missing_codes != 0:
    passed = False

if duplicate_codes != 0:
    passed = False

if abs(combined_total - total_coast) > 0.1:
    passed = False

if not passed:
    print("\n✗ COASTAL FEATURE VALIDATION FAILED")
    raise SystemExit(1)


print("\n" + "=" * 70)
print("✓ COASTAL FEATURE VALIDATION PASSED")
print("=" * 70)