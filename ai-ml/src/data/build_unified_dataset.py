from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# AASHRAY UNIFIED 1508-VILLAGE DATASET BUILDER
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "processed"

KERALA_FILE = DATA_DIR / "risk" / "kerala_700_priority_dataset.csv"

KEND_MULTI_FILE = (
    DATA_DIR / "multi_hazard" / "kendrapara_multi_hazard_summary.csv"
)

KEND_RAIN_FILE = (
    DATA_DIR / "rainfall" / "kendrapara_rainfall_features.csv"
)

KEND_COASTAL_FILE = (
    DATA_DIR / "coastal"
    / "kendrapara_village_coastal_hazard_summary.csv"
)

KEND_FLOOD_FILE = (
    DATA_DIR / "features" / "kendrapara_flood_hazard_features.csv"
)

KEND_CYCLONE_FILE = (
    DATA_DIR / "cyclone" / "kendrapara_cyclone_hazard_summary.csv"
)

KEND_EXPOSURE_FILE = (
    DATA_DIR / "features" / "kendrapara_coastal_exposure_features.csv"
)

OUTPUT_DIR = DATA_DIR / "combined"

OUTPUT_FILE = (
    OUTPUT_DIR / "aashray_1508_villages.csv"
)


# ============================================================
# HELPERS
# ============================================================

def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    df = pd.read_csv(path)

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    return df


def num(series):
    return pd.to_numeric(
        series,
        errors="coerce"
    )


def txt(series):
    return (
        series
        .fillna("")
        .astype(str)
        .str.strip()
    )


def empty_series(index):
    return pd.Series(
        np.nan,
        index=index
    )


# ============================================================
# LOAD KERALA
# ============================================================

print()
print("=" * 60)
print("AASHRAY UNIFIED DATASET BUILDER")
print("=" * 60)

print()
print("Loading Kerala dataset...")

kerala = read_csv(
    KERALA_FILE
)

print(
    f"Kerala villages: {len(kerala)}"
)


# ============================================================
# KERALA NORMALIZATION
# ============================================================

kerala_out = pd.DataFrame(
    index=kerala.index
)

kerala_out["id"] = txt(
    kerala["vlcode"]
)

kerala_out["village"] = txt(
    kerala["village"]
)

kerala_out["vlcode"] = txt(
    kerala["vlcode"]
)

kerala_out["state"] = "Kerala"

kerala_out["district"] = txt(
    kerala["district"]
)

kerala_out["block"] = txt(
    kerala["block"]
)

kerala_out["latitude"] = num(
    kerala["latitude"]
)

kerala_out["longitude"] = num(
    kerala["longitude"]
)

kerala_out["population"] = num(
    kerala["total_population_village"]
)

kerala_out["total_population_village"] = num(
    kerala["total_population_village"]
)

kerala_out["total_households"] = num(
    kerala["total_households"]
)

kerala_out["total_geographical_area"] = num(
    kerala["total_geographical_area"]
)

kerala_out["forest_area"] = num(
    kerala["forest_area"]
)

kerala_out["net_area_sown"] = num(
    kerala["net_area_sown"]
)

kerala_out["total_unirrigated_land"] = num(
    kerala["total_unirrigated_land"]
)

kerala_out["area_irrigated_by_source"] = num(
    kerala["area_irrigated_by_source"]
)

kerala_out["nearest_town_distance_from_village"] = num(
    kerala["nearest_town_distance_from_village"]
)


# Kerala AASHRAY score

kerala_out["aashray_risk_score"] = num(
    kerala["aashray_risk_score"]
)

kerala_out["priority"] = txt(
    kerala["priority"]
)

kerala_out["risk_model"] = txt(
    kerala["risk_model"]
)

kerala_out["risk_model_note"] = txt(
    kerala["risk_model_note"]
)


# Kerala does not have the Kendrapara-specific
# coastal/cyclone hazard layers.

kerala_out["coastal_hazard_score"] = np.nan
kerala_out["flood_hazard_score"] = np.nan
kerala_out["cyclone_hazard_score"] = np.nan

# Kerala rainfall hazard is not being inserted
# from the current Wayanad pilot into this common
# dataset because the 700-village engine currently
# uses exposure/infrastructure features.

kerala_out["rainfall_hazard_score"] = np.nan

kerala_out["multi_hazard_score"] = np.nan

kerala_out["multi_hazard_category"] = ""

kerala_out["hazards_available"] = (
    "vulnerability,exposure"
)

kerala_out["hazard_contribution"] = (
    "AASHRAY vulnerability and exposure model"
)


# ============================================================
# LOAD KENDRAPARA
# ============================================================

print()
print("Loading Kendrapara datasets...")

kend_multi = read_csv(
    KEND_MULTI_FILE
)

kend_rain = read_csv(
    KEND_RAIN_FILE
)

kend_coastal = read_csv(
    KEND_COASTAL_FILE
)

kend_flood = read_csv(
    KEND_FLOOD_FILE
)

kend_cyclone = read_csv(
    KEND_CYCLONE_FILE
)

kend_exposure = read_csv(
    KEND_EXPOSURE_FILE
)

print(
    f"Kendrapara villages: {len(kend_multi)}"
)


# ============================================================
# START WITH MULTI-HAZARD DATA
# ============================================================

kend = kend_multi.copy()

kend["vlcode"] = txt(
    kend["vlcode"]
)


# ============================================================
# RAINFALL MERGE
# ============================================================

rain = kend_rain[
    [
        "vlcode",
        "latitude",
        "longitude",
        "rainfall_hazard_score",
        "rainfall_hazard_category"
    ]
].copy()

rain["vlcode"] = txt(
    rain["vlcode"]
)

rain = rain.drop_duplicates(
    subset=["vlcode"]
)

kend = kend.merge(
    rain,
    on="vlcode",
    how="left",
    suffixes=("", "_rain")
)


# ============================================================
# COASTAL MERGE
# ============================================================

coastal = kend_coastal[
    [
        "vlcode",
        "block",
        "district",
        "shoreline_distance_km",
        "erosion_baseline_score",
        "coastal_hazard_score",
        "coastal_hazard_category"
    ]
].copy()

coastal["vlcode"] = txt(
    coastal["vlcode"]
)

coastal = coastal.drop_duplicates(
    subset=["vlcode"]
)

kend = kend.merge(
    coastal,
    on="vlcode",
    how="left",
    suffixes=("", "_coastal")
)


# ============================================================
# FLOOD MERGE
# ============================================================

flood = kend_flood[
    [
        "vlcode",
        "flood_hazard_score",
        "flood_hazard_category"
    ]
].copy()

flood["vlcode"] = txt(
    flood["vlcode"]
)

flood = flood.drop_duplicates(
    subset=["vlcode"]
)

kend = kend.merge(
    flood,
    on="vlcode",
    how="left",
    suffixes=("", "_flood")
)


# ============================================================
# CYCLONE MERGE
# ============================================================

cyclone = kend_cyclone[
    [
        "vlcode",
        "cyclone_hazard_score",
        "cyclone_hazard_category"
    ]
].copy()

cyclone["vlcode"] = txt(
    cyclone["vlcode"]
)

cyclone = cyclone.drop_duplicates(
    subset=["vlcode"]
)

kend = kend.merge(
    cyclone,
    on="vlcode",
    how="left",
    suffixes=("", "_cyclone")
)


# ============================================================
# EXPOSURE MERGE
# ============================================================

exposure = kend_exposure[
    [
        "vlcode",
        "area_km2",
        "centroid_x",
        "centroid_y",
        "coastal_exposure_score"
    ]
].copy()

exposure["vlcode"] = txt(
    exposure["vlcode"]
)

exposure = exposure.drop_duplicates(
    subset=["vlcode"]
)

kend = kend.merge(
    exposure,
    on="vlcode",
    how="left"
)


# ============================================================
# KENDRAPARA NORMALIZATION
# ============================================================

kend_out = pd.DataFrame(
    index=kend.index
)

kend_out["id"] = txt(
    kend["vlcode"]
)

kend_out["village"] = txt(
    kend["village"]
)

kend_out["vlcode"] = txt(
    kend["vlcode"]
)

kend_out["state"] = "Odisha"

kend_out["district"] = txt(
    kend["district"]
)

kend_out["block"] = txt(
    kend["block"]
)


# ============================================================
# COORDINATES
# ============================================================

kend_out["latitude"] = num(
    kend["latitude"]
)

kend_out["longitude"] = num(
    kend["longitude"]
)


# ============================================================
# FALLBACK TO EXPOSURE CENTROID
# ============================================================

kend_out.loc[
    kend_out["latitude"].isna(),
    "latitude"
] = num(
    kend["centroid_y"]
)

kend_out.loc[
    kend_out["longitude"].isna(),
    "longitude"
] = num(
    kend["centroid_x"]
)


# ============================================================
# COMMON EXPOSURE FIELDS
# ============================================================

kend_out["population"] = np.nan

kend_out["total_population_village"] = np.nan

kend_out["total_households"] = np.nan

kend_out["total_geographical_area"] = num(
    kend["area_km2"]
)

kend_out["forest_area"] = np.nan

kend_out["net_area_sown"] = np.nan

kend_out["total_unirrigated_land"] = np.nan

kend_out["area_irrigated_by_source"] = np.nan

kend_out["nearest_town_distance_from_village"] = np.nan


# ============================================================
# HAZARD SCORES
# ============================================================

kend_out["coastal_hazard_score"] = num(
    kend["coastal_hazard_score"]
)

kend_out["flood_hazard_score"] = num(
    kend["flood_hazard_score"]
)

kend_out["cyclone_hazard_score"] = num(
    kend["cyclone_hazard_score"]
)

# IMPORTANT:
# Explicitly use the rainfall file's score.

kend_out["rainfall_hazard_score"] = num(
    kend["rainfall_hazard_score"]
)


kend_out["multi_hazard_score"] = num(
    kend["multi_hazard_score"]
)

kend_out["multi_hazard_category"] = txt(
    kend["multi_hazard_category"]
)

kend_out["hazards_available"] = txt(
    kend["hazards_available"]
)

kend_out["hazard_contribution"] = txt(
    kend["hazard_contribution"]
)


# ============================================================
# COMMON 0-100 RISK SCORE
# ============================================================

kend_out["aashray_risk_score"] = (
    kend_out["multi_hazard_score"] * 100
)


# ============================================================
# COMMON PRIORITY
# ============================================================

def classify_priority(score):

    if pd.isna(score):
        return "DATA-ONLY"

    if score >= 75:
        return "P1"

    if score >= 50:
        return "P2"

    if score >= 25:
        return "P3"

    return "P4"


kend_out["priority"] = (
    kend_out["aashray_risk_score"]
    .apply(classify_priority)
)


kend_out["risk_model"] = (
    "Kendrapara Multi-Hazard Model v1"
)

kend_out["risk_model_note"] = (
    "Existing Kendrapara coastal, flood, "
    "cyclone and rainfall multi-hazard model. "
    "Priority is mapped to the common AASHRAY "
    "0-100 risk scale."
)


# ============================================================
# COMBINE
# ============================================================

print()
print("Combining Kerala + Kendrapara...")

combined = pd.concat(
    [
        kerala_out,
        kend_out
    ],
    ignore_index=True
)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

combined["vlcode"] = (
    combined["vlcode"]
    .astype(str)
    .str.strip()
)

combined = combined.drop_duplicates(
    subset=["state", "vlcode"],
    keep="first"
)


# ============================================================
# SORT
# ============================================================

combined = combined.sort_values(
    [
        "state",
        "district",
        "village"
    ]
).reset_index(
    drop=True
)


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

combined.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 60)
print("AASHRAY UNIFIED DATASET COMPLETE")
print("=" * 60)

print(
    f"Total villages: {len(combined)}"
)

print()
print("State distribution:")

print(
    combined["state"]
    .value_counts()
)


print()
print("Priority distribution:")

print(
    combined["priority"]
    .value_counts()
    .reindex(
        [
            "P1",
            "P2",
            "P3",
            "P4",
            "DATA-ONLY"
        ]
    )
    .fillna(0)
    .astype(int)
)


print()
print("Hazard coverage:")

print(
    "Coastal:",
    combined["coastal_hazard_score"]
    .notna()
    .sum()
)

print(
    "Flood:",
    combined["flood_hazard_score"]
    .notna()
    .sum()
)

print(
    "Cyclone:",
    combined["cyclone_hazard_score"]
    .notna()
    .sum()
)

print(
    "Rainfall:",
    combined["rainfall_hazard_score"]
    .notna()
    .sum()
)

print(
    "Multi-hazard:",
    combined["multi_hazard_score"]
    .notna()
    .sum()
)


print()
print("Output:")

print(
    OUTPUT_FILE
)