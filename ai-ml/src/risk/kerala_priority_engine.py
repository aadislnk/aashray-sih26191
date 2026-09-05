from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# AASHRAY KERALA VILLAGE PRIORITY ENGINE
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "administrative"
    / "kerala_700_selected_villages.csv"
)

OUTPUT_DIR = BASE_DIR / "data" / "processed" / "risk"

OUTPUT_FILE = (
    OUTPUT_DIR
    / "kerala_700_priority_dataset.csv"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def numeric(series):
    return pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0)


def percentile_score(series):
    values = numeric(series)

    if values.nunique() <= 1:
        return pd.Series(
            0.0,
            index=series.index
        )

    return (
        values.rank(
            method="average",
            pct=True
        ) * 100
    )


def availability_vulnerability(series):
    text = (
        series
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return text.map(
        {
            "available": 0.0,
            "not available": 100.0,
        }
    ).fillna(50.0)


def open_drainage_vulnerability(series):
    text = (
        series
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return text.map(
        {
            "available": 100.0,
            "not available": 0.0,
        }
    ).fillna(50.0)


def ratio_score(numerator, denominator):
    num = numeric(numerator)
    den = numeric(denominator)

    ratio = np.where(
        den > 0,
        (num / den) * 100,
        0
    )

    return pd.Series(
        ratio,
        index=numerator.index
    ).clip(0, 100)


def get_column(df, possible_names, default=0):
    """
    Find the first matching column from a list of possible names.
    This prevents the engine from breaking because of minor
    dataset column-name differences.
    """

    for name in possible_names:
        if name in df.columns:
            return df[name]

    return pd.Series(
        default,
        index=df.index
    )


def assign_priority_by_rank(score):
    """
    700 villages:

    Top 10%    -> P1
    Next 20%   -> P2
    Next 30%   -> P3
    Bottom 40% -> P4
    """

    n = len(score)

    order = (
        score
        .sort_values(
            ascending=False,
            kind="mergesort"
        )
        .index
    )

    priority = pd.Series(
        "P4",
        index=score.index,
        dtype="object"
    )

    p1_count = int(np.ceil(n * 0.10))
    p2_count = int(np.ceil(n * 0.20))
    p3_count = int(np.ceil(n * 0.30))

    priority.loc[
        order[:p1_count]
    ] = "P1"

    priority.loc[
        order[
            p1_count:
            p1_count + p2_count
        ]
    ] = "P2"

    priority.loc[
        order[
            p1_count + p2_count:
            p1_count + p2_count + p3_count
        ]
    ] = "P3"

    return priority


# ============================================================
# LOAD DATA
# ============================================================

print("Loading 700-village dataset...")

df = pd.read_csv(INPUT_FILE)

print(
    f"Input villages: {len(df)}"
)


# ============================================================
# POPULATION EXPOSURE
# ============================================================

population = get_column(
    df,
    [
        "total_population_village",
        "total_population",
        "population"
    ]
)

population_score = percentile_score(
    population
)


# ============================================================
# HOUSEHOLD PRESSURE
# ============================================================

households = get_column(
    df,
    [
        "total_households",
        "households",
        "total_household"
    ]
)

household_score = percentile_score(
    households
)


# ============================================================
# WATER VULNERABILITY
# ============================================================

treated_water = get_column(
    df,
    [
        "tapwater_treated_status"
    ],
    default=""
)

handpump = get_column(
    df,
    [
        "handpump_status"
    ],
    default=""
)

tubewell = get_column(
    df,
    [
        "tubewell_borehole_status",
        "tubewell_status"
    ],
    default=""
)

treated_water_score = availability_vulnerability(
    treated_water
)

handpump_score = availability_vulnerability(
    handpump
)

tubewell_score = availability_vulnerability(
    tubewell
)

water_score = (
    0.50 * treated_water_score
    + 0.25 * handpump_score
    + 0.25 * tubewell_score
)


# ============================================================
# DRAINAGE VULNERABILITY
# ============================================================

closed_drainage = get_column(
    df,
    [
        "closed_drainage_status"
    ],
    default=""
)

open_drainage = get_column(
    df,
    [
        "open_drainage_status"
    ],
    default=""
)

closed_drainage_score = availability_vulnerability(
    closed_drainage
)

open_drainage_score = open_drainage_vulnerability(
    open_drainage
)

drainage_score = (
    0.65 * closed_drainage_score
    + 0.35 * open_drainage_score
)


# ============================================================
# ACCESSIBILITY
# ============================================================

town_distance = get_column(
    df,
    [
        "distance_from_nearest_town_km",
        "distance_to_nearest_town_km",
        "nearest_town_distance_km",
        "town_distance_km",
        "distance_from_town_km"
    ],
    default=0
)

accessibility_score = percentile_score(
    town_distance
)


# ============================================================
# LAND / ENVIRONMENT
# ============================================================

forest_area = get_column(
    df,
    [
        "forest_area"
    ]
)

total_area = get_column(
    df,
    [
        "total_geographical_area",
        "geographical_area",
        "total_area"
    ]
)

net_sown_area = get_column(
    df,
    [
        "net_sown_area"
    ]
)

current_fallow = get_column(
    df,
    [
        "current_fallow_land"
    ]
)

other_fallow = get_column(
    df,
    [
        "other_fallow_land"
    ]
)

unirrigated_area = get_column(
    df,
    [
        "unirrigated_area"
    ]
)


forest_ratio = ratio_score(
    forest_area,
    total_area
)


agriculture_area = (
    numeric(net_sown_area)
    + numeric(current_fallow)
    + numeric(other_fallow)
)


agriculture_ratio = ratio_score(
    agriculture_area,
    total_area
)


unirrigated_ratio = ratio_score(
    unirrigated_area,
    net_sown_area
)


land_environment_score = (
    0.35 * forest_ratio
    + 0.30 * agriculture_ratio
    + 0.35 * unirrigated_ratio
)


# ============================================================
# COMPOSITE AASHRAY SCORE
# ============================================================

raw_score = (
    0.25 * population_score
    + 0.10 * household_score
    + 0.15 * water_score
    + 0.15 * drainage_score
    + 0.15 * accessibility_score
    + 0.20 * land_environment_score
)


# ============================================================
# NORMALIZE TO 0-100
# ============================================================

minimum = raw_score.min()
maximum = raw_score.max()

if maximum > minimum:

    aashray_risk_score = (
        (raw_score - minimum)
        / (maximum - minimum)
    ) * 100

else:

    aashray_risk_score = pd.Series(
        0.0,
        index=df.index
    )


aashray_risk_score = (
    aashray_risk_score
    .round(2)
)


# ============================================================
# PRIORITY
# ============================================================

priority = assign_priority_by_rank(
    aashray_risk_score
)


# ============================================================
# ADD OUTPUT COLUMNS
# ============================================================

df["population_exposure_score"] = (
    population_score.round(2)
)

df["household_pressure_score"] = (
    household_score.round(2)
)

df["water_vulnerability_score"] = (
    water_score.round(2)
)

df["drainage_vulnerability_score"] = (
    drainage_score.round(2)
)

df["accessibility_vulnerability_score"] = (
    accessibility_score.round(2)
)

df["land_environment_score"] = (
    land_environment_score.round(2)
)

df["aashray_risk_score"] = (
    aashray_risk_score
)

df["priority"] = priority


# ============================================================
# MODEL INFORMATION
# ============================================================

df["risk_model"] = (
    "AASHRAY Vulnerability & Priority Model v1"
)

df["risk_model_note"] = (
    "Modelled village-level exposure and "
    "infrastructure vulnerability score; "
    "not an official government hazard classification."
)


# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    by="aashray_risk_score",
    ascending=False
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

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# REPORT
# ============================================================

print()
print("=" * 50)
print("AASHRAY PRIORITY ENGINE COMPLETE")
print("=" * 50)

print(
    f"Villages: {len(df)}"
)

print()
print("Priority distribution:")

print(
    df["priority"]
    .value_counts()
    .reindex(
        ["P1", "P2", "P3", "P4"]
    )
    .fillna(0)
    .astype(int)
)

print()
print("Risk score statistics:")

print(
    df["aashray_risk_score"]
    .describe()
    .round(2)
)

print()
print("Average score by priority:")

print(
    df.groupby(
        "priority"
    )["aashray_risk_score"]
    .mean()
    .reindex(
        ["P1", "P2", "P3", "P4"]
    )
    .round(2)
)

print()
print("Top 10 villages:")

print(
    df[
        [
            "village",
            "district",
            "block",
            "vlcode",
            "aashray_risk_score",
            "priority",
            "total_population_village"
        ]
    ]
    .head(10)
    .to_string(index=False)
)

print()
print("Output:")

print(
    OUTPUT_FILE
)