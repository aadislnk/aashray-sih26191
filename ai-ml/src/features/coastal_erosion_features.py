from pathlib import Path
import geopandas as gpd
import pandas as pd


INPUT = Path(
    "data/processed/administrative/"
    "kendrapara_coastal_villages.geojson"
)

OUTPUT = Path(
    "data/processed/features/"
    "kendrapara_coastal_erosion_features.csv"
)


print("=" * 70)
print("AASHRAY KENDRAPARA COASTAL EROSION FEATURES")
print("=" * 70)


# ------------------------------------------------------------------
# 1. LOAD COASTAL VILLAGES
# ------------------------------------------------------------------

print("\nLoading coastal villages...")

gdf = gpd.read_file(INPUT)

print(f"Coastal villages: {len(gdf)}")


# ------------------------------------------------------------------
# 2. NCCR KENDRAPARA SHORELINE STATISTICS
# ------------------------------------------------------------------

nccr_stats = {
    "high_erosion_km": 31.02,
    "moderate_erosion_km": 8.72,
    "low_erosion_km": 9.22,
    "stable_km": 54.26,
    "low_accretion_km": 11.26,
    "moderate_accretion_km": 5.02,
    "high_accretion_km": 16.32,
}

total_coast_km = 135.82


# ------------------------------------------------------------------
# 3. CALCULATE NCCR PROPORTIONS
# ------------------------------------------------------------------

nccr_proportions = {
    "high_erosion": 31.02 / total_coast_km,
    "moderate_erosion": 8.72 / total_coast_km,
    "low_erosion": 9.22 / total_coast_km,
}


# ------------------------------------------------------------------
# 4. DISTRICT-LEVEL EROSION BASELINE
# ------------------------------------------------------------------

erosion_baseline = (
    nccr_proportions["high_erosion"] * 1.00
    + nccr_proportions["moderate_erosion"] * 0.67
    + nccr_proportions["low_erosion"] * 0.33
)


# ------------------------------------------------------------------
# 5. CREATE FEATURE TABLE
# ------------------------------------------------------------------

features = pd.DataFrame()

features["village"] = (
    gdf["village"]
    .astype(str)
    .str.strip()
)

features["vlcode"] = (
    gdf["vlcode"]
)

features["block"] = (
    gdf["block"]
    .astype(str)
    .str.strip()
)

features["district"] = (
    gdf["district"]
    .astype(str)
    .str.strip()
)


# ------------------------------------------------------------------
# 6. NCCR COASTLINE INFORMATION
# ------------------------------------------------------------------

features["nccr_total_coast_km"] = total_coast_km

features["nccr_high_erosion_km"] = (
    nccr_stats["high_erosion_km"]
)

features["nccr_moderate_erosion_km"] = (
    nccr_stats["moderate_erosion_km"]
)

features["nccr_low_erosion_km"] = (
    nccr_stats["low_erosion_km"]
)

features["nccr_stable_km"] = (
    nccr_stats["stable_km"]
)

features["nccr_low_accretion_km"] = (
    nccr_stats["low_accretion_km"]
)

features["nccr_moderate_accretion_km"] = (
    nccr_stats["moderate_accretion_km"]
)

features["nccr_high_accretion_km"] = (
    nccr_stats["high_accretion_km"]
)


# ------------------------------------------------------------------
# 7. HAZARD BASELINE
# ------------------------------------------------------------------

features["erosion_baseline_score"] = (
    erosion_baseline
)

features["coastal_hazard_baseline"] = (
    erosion_baseline
)


# ------------------------------------------------------------------
# 8. DATA PROVENANCE
# ------------------------------------------------------------------

features["erosion_data_source"] = (
    "NCCR National Assessment of Shoreline Changes 1990-2016"
)

features["erosion_resolution"] = (
    "District coastline baseline"
)

features["village_erosion_rate_available"] = False


# ------------------------------------------------------------------
# 9. SAVE
# ------------------------------------------------------------------

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

features.to_csv(
    OUTPUT,
    index=False
)


# ------------------------------------------------------------------
# 10. SUMMARY
# ------------------------------------------------------------------

print("\nNCCR Kendrapara coastline:")
print(f"  Total: {total_coast_km:.2f} km")
print(
    f"  High erosion: "
    f"{nccr_stats['high_erosion_km']:.2f} km"
)
print(
    f"  Moderate erosion: "
    f"{nccr_stats['moderate_erosion_km']:.2f} km"
)
print(
    f"  Low erosion: "
    f"{nccr_stats['low_erosion_km']:.2f} km"
)
print(
    f"  Stable: "
    f"{nccr_stats['stable_km']:.2f} km"
)

print(
    f"\nDistrict erosion baseline score: "
    f"{erosion_baseline:.4f}"
)

print(
    f"\nFeature rows: "
    f"{len(features)}"
)

print("\nSaved:")
print(OUTPUT.resolve())

print("\n" + "=" * 70)
print("COASTAL EROSION FEATURE EXTRACTION COMPLETE")
print("=" * 70)