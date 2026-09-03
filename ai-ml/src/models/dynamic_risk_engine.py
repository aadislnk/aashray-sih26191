from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAINFALL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "rainfall"
    / "wayanad_rainfall_2024.csv"
)

SUSCEPTIBILITY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "susceptibility"
    / "wayanad_pilot_susceptibility.tif"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "risk"
)

OUTPUT_CSV = (
    OUTPUT_DIR
    / "dynamic_risk_2024.csv"
)


# ============================================================
# RAINFALL SCORING
# ============================================================

def rainfall_score(
    rainfall_1d,
    rainfall_3d,
    rainfall_7d,
    rainfall_30d
):
    """
    Transparent rainfall trigger score.

    The score is intentionally rule-based for the pilot.
    It is NOT presented as a calibrated probability.

    0 = low rainfall trigger
    1 = moderate
    2 = high
    3 = very high
    """

    score = 0

    # Short-term intense rainfall
    if rainfall_1d >= 100:
        score += 3
    elif rainfall_1d >= 50:
        score += 2
    elif rainfall_1d >= 25:
        score += 1

    # 3-day accumulated rainfall
    if rainfall_3d >= 200:
        score += 3
    elif rainfall_3d >= 100:
        score += 2
    elif rainfall_3d >= 50:
        score += 1

    # 7-day accumulated rainfall
    if rainfall_7d >= 300:
        score += 3
    elif rainfall_7d >= 150:
        score += 2
    elif rainfall_7d >= 75:
        score += 1

    # 30-day accumulated rainfall
    if rainfall_30d >= 600:
        score += 3
    elif rainfall_30d >= 300:
        score += 2
    elif rainfall_30d >= 150:
        score += 1

    return score


# ============================================================
# NORMALIZE RAINFALL SCORE
# ============================================================

def normalize_rainfall_score(score):

    if score >= 8:
        return 1.0

    if score >= 5:
        return 0.75

    if score >= 3:
        return 0.50

    if score >= 1:
        return 0.25

    return 0.0


# ============================================================
# SUSCEPTIBILITY CATEGORY
# ============================================================

def susceptibility_category(probability):

    if probability < 0.25:
        return "LOW"

    if probability < 0.50:
        return "MODERATE"

    if probability < 0.75:
        return "HIGH"

    return "VERY HIGH"


# ============================================================
# DYNAMIC RISK
# ============================================================

def calculate_dynamic_risk(
    susceptibility,
    rainfall_trigger
):
    """
    Combine terrain susceptibility with rainfall trigger.

    Terrain contributes 70%.
    Rainfall contributes 30%.

    This is a pilot risk index, not a calibrated
    landslide probability.
    """

    risk = (
        0.70 * susceptibility
        +
        0.30 * rainfall_trigger
    )

    return risk


# ============================================================
# RISK CATEGORY
# ============================================================

def risk_category(risk):

    if risk < 0.25:
        return "LOW"

    if risk < 0.50:
        return "MODERATE"

    if risk < 0.75:
        return "HIGH"

    return "VERY HIGH"


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("AASHRAY DYNAMIC RISK ENGINE")
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD RAINFALL
    # --------------------------------------------------------

    print()
    print("Loading rainfall features...")

    rainfall = pd.read_csv(
        RAINFALL_FILE
    )

    rainfall["date"] = pd.to_datetime(
        rainfall["date"]
    )

    print(
        f"Rainfall records: "
        f"{len(rainfall)}"
    )

    # --------------------------------------------------------
    # LOAD SUSCEPTIBILITY MAP
    # --------------------------------------------------------

    print()
    print(
        "Loading susceptibility map..."
    )

    with rasterio.open(
        SUSCEPTIBILITY_FILE
    ) as src:

        susceptibility = src.read(
            1
        ).astype(
            "float32"
        )

    valid_pixels = (
        np.isfinite(
            susceptibility
        )
        &
        (susceptibility >= 0)
    )

    print(
        f"Valid susceptibility pixels: "
        f"{valid_pixels.sum():,}"
    )

    # --------------------------------------------------------
    # STATIC REGION STATISTICS
    # --------------------------------------------------------

    susceptibility_values = (
        susceptibility[
            valid_pixels
        ]
    )

    mean_susceptibility = float(
        np.mean(
            susceptibility_values
        )
    )

    high_susceptibility_pixels = (
        susceptibility_values
        >= 0.50
    )

    very_high_pixels = (
        susceptibility_values
        >= 0.75
    )

    print()
    print(
        f"Mean susceptibility: "
        f"{mean_susceptibility:.4f}"
    )

    print(
        f"High+ pixels: "
        f"{high_susceptibility_pixels.sum():,}"
    )

    print(
        f"Very-high pixels: "
        f"{very_high_pixels.sum():,}"
    )

    # --------------------------------------------------------
    # CALCULATE DAILY RISK
    # --------------------------------------------------------

    print()
    print(
        "Calculating daily rainfall triggers..."
    )

    results = []

    for _, row in rainfall.iterrows():

        rainfall_1d = float(
            row["rainfall_mm"]
        )

        rainfall_3d = float(
            row["rainfall_3day"]
        )

        rainfall_7d = float(
            row["rainfall_7day"]
        )

        rainfall_30d = float(
            row["rainfall_30day"]
        )

        trigger_score = rainfall_score(
            rainfall_1d,
            rainfall_3d,
            rainfall_7d,
            rainfall_30d
        )

        trigger = normalize_rainfall_score(
            trigger_score
        )

        # Region-wide risk index.
        risk = calculate_dynamic_risk(
            mean_susceptibility,
            trigger
        )

        results.append(
            {
                "date": row["date"],
                "rainfall_mm": rainfall_1d,
                "rainfall_3day": rainfall_3d,
                "rainfall_7day": rainfall_7d,
                "rainfall_30day": rainfall_30d,
                "rainfall_trigger_score": trigger_score,
                "rainfall_trigger": trigger,
                "mean_susceptibility": mean_susceptibility,
                "dynamic_risk": risk,
                "risk_category": risk_category(
                    risk
                ),
                "susceptibility_category":
                    susceptibility_category(
                        mean_susceptibility
                    ),
            }
        )

    result = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    result.to_csv(
        OUTPUT_CSV,
        index=False
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("DYNAMIC RISK SUMMARY")
    print("=" * 70)

    print()
    print(
        result[
            "risk_category"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "Highest-risk dates:"
    )

    print(
        result.sort_values(
            "dynamic_risk",
            ascending=False
        )
        [
            [
                "date",
                "rainfall_mm",
                "rainfall_3day",
                "rainfall_7day",
                "dynamic_risk",
                "risk_category",
            ]
        ]
        .head(15)
        .to_string(
            index=False
        )
    )

    print()
    print(
        f"Saved to:\n"
        f"{OUTPUT_CSV.resolve()}"
    )

    print()
    print("=" * 70)
    print(
        "DYNAMIC RISK ENGINE COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()