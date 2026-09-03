from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# IMPORTANT:
# Use the feature dataset because it contains:
# rainfall_mm
# rainfall_3day
# rainfall_7day
# rainfall_30day

RAINFALL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "features"
    / "aashray_feature_dataset_2024.csv"
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

SUMMARY_FILE = (
    OUTPUT_DIR
    / "dynamic_risk_summary_2024.csv"
)


# ============================================================
# RAINFALL TRIGGER
# ============================================================

def calculate_trigger(
    rainfall_1d,
    rainfall_3d,
    rainfall_7d,
    rainfall_30d
):
    """
    Calculate a transparent rainfall-trigger score.

    This is a prototype rule-based trigger.
    It is NOT a calibrated probability.
    """

    score = 0

    # --------------------------------------------------------
    # 1-DAY RAINFALL
    # --------------------------------------------------------

    if rainfall_1d >= 100:
        score += 3

    elif rainfall_1d >= 50:
        score += 2

    elif rainfall_1d >= 25:
        score += 1

    # --------------------------------------------------------
    # 3-DAY ACCUMULATION
    # --------------------------------------------------------

    if rainfall_3d >= 200:
        score += 3

    elif rainfall_3d >= 100:
        score += 2

    elif rainfall_3d >= 50:
        score += 1

    # --------------------------------------------------------
    # 7-DAY ACCUMULATION
    # --------------------------------------------------------

    if rainfall_7d >= 300:
        score += 3

    elif rainfall_7d >= 150:
        score += 2

    elif rainfall_7d >= 75:
        score += 1

    # --------------------------------------------------------
    # 30-DAY ACCUMULATION
    # --------------------------------------------------------

    if rainfall_30d >= 600:
        score += 3

    elif rainfall_30d >= 300:
        score += 2

    elif rainfall_30d >= 150:
        score += 1

    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------

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
# RISK CLASSIFICATION
# ============================================================

def classify_risk(value):

    if value < 0.25:
        return 1

    if value < 0.50:
        return 2

    if value < 0.75:
        return 3

    return 4


# ============================================================
# GENERATE ONE SPATIAL MAP
# ============================================================

def generate_map(
    susceptibility,
    valid,
    profile,
    date,
    rainfall_row
):

    # --------------------------------------------------------
    # RAINFALL VALUES
    # --------------------------------------------------------

    rainfall_1d = float(
        rainfall_row["rainfall_mm"]
    )

    rainfall_3d = float(
        rainfall_row["rainfall_3day"]
    )

    rainfall_7d = float(
        rainfall_row["rainfall_7day"]
    )

    rainfall_30d = float(
        rainfall_row["rainfall_30day"]
    )

    # --------------------------------------------------------
    # RAINFALL TRIGGER
    # --------------------------------------------------------

    trigger = calculate_trigger(
        rainfall_1d,
        rainfall_3d,
        rainfall_7d,
        rainfall_30d
    )

    # --------------------------------------------------------
    # DYNAMIC RISK
    # --------------------------------------------------------

    risk = np.full(
        susceptibility.shape,
        -9999.0,
        dtype="float32"
    )

    risk[valid] = (
        0.70
        *
        susceptibility[valid]
        +
        0.30
        *
        trigger
    )

    # --------------------------------------------------------
    # RISK CLASSES
    #
    # 0 = NoData
    # 1 = Low
    # 2 = Moderate
    # 3 = High
    # 4 = Very High
    # --------------------------------------------------------

    risk_class = np.zeros(
        susceptibility.shape,
        dtype="uint8"
    )

    values = risk[valid]

    classified = np.select(
        [
            values < 0.25,
            values < 0.50,
            values < 0.75,
        ],
        [
            1,
            2,
            3,
        ],
        default=4
    )

    risk_class[valid] = (
        classified.astype("uint8")
    )

    # --------------------------------------------------------
    # FILE NAMES
    # --------------------------------------------------------

    date_string = date.strftime(
        "%Y%m%d"
    )

    probability_file = (
        OUTPUT_DIR
        /
        f"dynamic_risk_{date_string}.tif"
    )

    class_file = (
        OUTPUT_DIR
        /
        f"dynamic_risk_class_{date_string}.tif"
    )

    # --------------------------------------------------------
    # PROBABILITY / RISK RASTER
    # --------------------------------------------------------

    probability_profile = (
        profile.copy()
    )

    probability_profile.update(
        dtype="float32",
        count=1,
        nodata=-9999,
        compress="lzw"
    )

    with rasterio.open(
        probability_file,
        "w",
        **probability_profile
    ) as dst:

        dst.write(
            risk,
            1
        )

    # --------------------------------------------------------
    # CLASS RASTER
    # --------------------------------------------------------

    class_profile = (
        profile.copy()
    )

    class_profile.update(
        dtype="uint8",
        count=1,
        nodata=0,
        compress="lzw"
    )

    with rasterio.open(
        class_file,
        "w",
        **class_profile
    ) as dst:

        dst.write(
            risk_class,
            1
        )

    return (
        trigger,
        risk,
        risk_class,
        probability_file,
        class_file
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("AASHRAY DYNAMIC RISK MAP GENERATOR")
    print("=" * 70)

    # --------------------------------------------------------
    # OUTPUT DIRECTORY
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # LOAD SUSCEPTIBILITY
    # --------------------------------------------------------

    print()
    print(
        "Loading susceptibility raster..."
    )

    with rasterio.open(
        SUSCEPTIBILITY_FILE
    ) as src:

        susceptibility = src.read(
            1
        ).astype(
            "float32"
        )

        profile = src.profile.copy()

    valid = (
        np.isfinite(
            susceptibility
        )
        &
        (susceptibility >= 0)
    )

    print(
        f"Valid pixels: "
        f"{valid.sum():,}"
    )

    # --------------------------------------------------------
    # LOAD RAINFALL FEATURES
    # --------------------------------------------------------

    print()
    print(
        "Loading rainfall features..."
    )

    rainfall = pd.read_csv(
        RAINFALL_FILE
    )

    rainfall["date"] = pd.to_datetime(
        rainfall["date"]
    )

    # --------------------------------------------------------
    # VERIFY REQUIRED COLUMNS
    # --------------------------------------------------------

    required_columns = [
        "date",
        "rainfall_mm",
        "rainfall_3day",
        "rainfall_7day",
        "rainfall_30day",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in rainfall.columns
    ]

    if missing_columns:

        raise ValueError(
            "Rainfall dataset is missing "
            f"columns: {missing_columns}"
        )

    # --------------------------------------------------------
    # KEEP ONLY RAINFALL COLUMNS
    # --------------------------------------------------------

    rainfall = rainfall[
        required_columns
    ].copy()

    # --------------------------------------------------------
    # REMOVE DUPLICATE VILLAGE RECORDS
    # --------------------------------------------------------
    #
    # The AASHRAY feature dataset contains
    # three rows per date because we have
    # three villages.
    #
    # Rainfall is common to the pilot region,
    # so we only need one row per date.
    # --------------------------------------------------------

    rainfall = (
        rainfall
        .drop_duplicates(
            subset=["date"]
        )
        .sort_values(
            "date"
        )
        .reset_index(
            drop=True
        )
    )

    print(
        f"Unique rainfall dates: "
        f"{len(rainfall)}"
    )

    # --------------------------------------------------------
    # CHECK FOR MISSING RAINFALL
    # --------------------------------------------------------

    rainfall_columns = [
        "rainfall_mm",
        "rainfall_3day",
        "rainfall_7day",
        "rainfall_30day",
    ]

    missing_rainfall = (
        rainfall[
            rainfall_columns
        ]
        .isna()
        .sum()
    )

    if missing_rainfall.any():

        print()
        print(
            "WARNING: Missing rainfall values:"
        )

        print(
            missing_rainfall[
                missing_rainfall > 0
            ]
            .to_string()
        )

        rainfall[
            rainfall_columns
        ] = (
            rainfall[
                rainfall_columns
            ]
            .fillna(0)
        )

    # --------------------------------------------------------
    # STATIC SUSCEPTIBILITY
    # --------------------------------------------------------

    mean_susceptibility = float(
        np.mean(
            susceptibility[
                valid
            ]
        )
    )

    print()
    print(
        f"Mean susceptibility: "
        f"{mean_susceptibility:.4f}"
    )

    # --------------------------------------------------------
    # DAILY SUMMARY
    # --------------------------------------------------------

    print()
    print(
        "Calculating daily dynamic risk..."
    )

    summary = []

    for _, row in rainfall.iterrows():

        trigger = calculate_trigger(
            float(
                row["rainfall_mm"]
            ),
            float(
                row["rainfall_3day"]
            ),
            float(
                row["rainfall_7day"]
            ),
            float(
                row["rainfall_30day"]
            )
        )

        mean_risk = (
            0.70
            *
            mean_susceptibility
            +
            0.30
            *
            trigger
        )

        summary.append(
            {
                "date": row["date"],

                "rainfall_mm":
                    row["rainfall_mm"],

                "rainfall_3day":
                    row["rainfall_3day"],

                "rainfall_7day":
                    row["rainfall_7day"],

                "rainfall_30day":
                    row["rainfall_30day"],

                "rainfall_trigger":
                    trigger,

                "mean_susceptibility":
                    mean_susceptibility,

                "mean_dynamic_risk":
                    mean_risk,

                "risk_category":
                    (
                        "LOW"
                        if mean_risk < 0.25
                        else
                        "MODERATE"
                        if mean_risk < 0.50
                        else
                        "HIGH"
                        if mean_risk < 0.75
                        else
                        "VERY HIGH"
                    )
            }
        )

    summary_df = pd.DataFrame(
        summary
    )

    # --------------------------------------------------------
    # SAVE SUMMARY
    # --------------------------------------------------------

    summary_df.to_csv(
        SUMMARY_FILE,
        index=False
    )

    print()
    print(
        f"Daily summary saved:\n"
        f"{SUMMARY_FILE.resolve()}"
    )

    # --------------------------------------------------------
    # SELECT DEMONSTRATION DATES
    # --------------------------------------------------------

    print()
    print(
        "Selecting demonstration dates..."
    )

    selected_dates = set()

    # Highest 1-day rainfall
    selected_dates.add(
        summary_df.loc[
            summary_df[
                "rainfall_mm"
            ].idxmax(),
            "date"
        ]
    )

    # Highest 3-day rainfall
    selected_dates.add(
        summary_df.loc[
            summary_df[
                "rainfall_3day"
            ].idxmax(),
            "date"
        ]
    )

    # Highest 7-day rainfall
    selected_dates.add(
        summary_df.loc[
            summary_df[
                "rainfall_7day"
            ].idxmax(),
            "date"
        ]
    )

    # --------------------------------------------------------
    # HISTORICAL DATES
    # --------------------------------------------------------
    #
    # Our current rainfall dataset is 2024.
    #
    # We therefore do NOT fabricate rainfall
    # for 2018.
    # --------------------------------------------------------

    selected_dates.add(
        pd.Timestamp(
            "2018-08-08"
        )
    )

    selected_dates.add(
        pd.Timestamp(
            "2018-08-09"
        )
    )

    # --------------------------------------------------------
    # GENERATE SELECTED MAPS
    # --------------------------------------------------------

    print()
    print(
        "Generating selected demonstration maps..."
    )

    generated = 0

    for date in sorted(
        selected_dates
    ):

        matching = rainfall[
            rainfall["date"] == date
        ]

        if matching.empty:

            print()
            print(
                f"Skipping {date.date()} "
                f"(no rainfall data available)"
            )

            continue

        row = matching.iloc[0]

        (
            trigger,
            risk,
            risk_class,
            probability_file,
            class_file
        ) = generate_map(
            susceptibility,
            valid,
            profile,
            date,
            row
        )

        generated += 1

        print()
        print(
            f"Generated map: "
            f"{date.date()}"
        )

        print(
            f"  1-day rainfall: "
            f"{float(row['rainfall_mm']):.2f} mm"
        )

        print(
            f"  3-day rainfall: "
            f"{float(row['rainfall_3day']):.2f} mm"
        )

        print(
            f"  7-day rainfall: "
            f"{float(row['rainfall_7day']):.2f} mm"
        )

        print(
            f"  30-day rainfall: "
            f"{float(row['rainfall_30day']):.2f} mm"
        )

        print(
            f"  Rainfall trigger: "
            f"{trigger:.2f}"
        )

        print(
            f"  Mean dynamic risk: "
            f"{float(np.mean(risk[valid])):.4f}"
        )

        print(
            f"  Probability map: "
            f"{probability_file.name}"
        )

        print(
            f"  Class map: "
            f"{class_file.name}"
        )

    # --------------------------------------------------------
    # TOP RISK DAYS
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("TOP DYNAMIC-RISK DAYS")
    print("=" * 70)

    top_days = (
        summary_df
        .sort_values(
            "mean_dynamic_risk",
            ascending=False
        )
        .head(10)
    )

    print(
        top_days[
            [
                "date",
                "rainfall_mm",
                "rainfall_3day",
                "rainfall_7day",
                "rainfall_trigger",
                "mean_dynamic_risk",
                "risk_category",
            ]
        ]
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # RISK DISTRIBUTION
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("RISK CATEGORY DISTRIBUTION")
    print("=" * 70)

    print(
        summary_df[
            "risk_category"
        ]
        .value_counts()
        .to_string()
    )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("DYNAMIC RISK GENERATION COMPLETE")
    print("=" * 70)

    print()
    print(
        f"Daily records: "
        f"{len(summary_df)}"
    )

    print(
        f"Demonstration maps generated: "
        f"{generated}"
    )

    print()
    print(
        "Risk equation:"
    )

    print(
        "Dynamic Risk = "
        "0.70 × Susceptibility "
        "+ "
        "0.30 × Rainfall Trigger"
    )

    print()
    print(
        f"Output directory:\n"
        f"{OUTPUT_DIR.resolve()}"
    )

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()