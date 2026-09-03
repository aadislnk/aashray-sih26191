from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

VILLAGES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "administrative"
    / "wayanad_pilot_villages.geojson"
)

SUSCEPTIBILITY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "susceptibility"
    / "wayanad_pilot_susceptibility.tif"
)

RAINFALL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "features"
    / "aashray_feature_dataset_2024.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "risk"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "village_risk_2024.csv"
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

    score = 0

    # 1-day rainfall
    if rainfall_1d >= 100:
        score += 3
    elif rainfall_1d >= 50:
        score += 2
    elif rainfall_1d >= 25:
        score += 1

    # 3-day accumulation
    if rainfall_3d >= 200:
        score += 3
    elif rainfall_3d >= 100:
        score += 2
    elif rainfall_3d >= 50:
        score += 1

    # 7-day accumulation
    if rainfall_7d >= 300:
        score += 3
    elif rainfall_7d >= 150:
        score += 2
    elif rainfall_7d >= 75:
        score += 1

    # 30-day accumulation
    if rainfall_30d >= 600:
        score += 3
    elif rainfall_30d >= 300:
        score += 2
    elif rainfall_30d >= 150:
        score += 1

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
# RISK CATEGORY
# ============================================================

def risk_category(value):

    if value < 0.25:
        return "LOW"

    if value < 0.50:
        return "MODERATE"

    if value < 0.75:
        return "HIGH"

    return "VERY HIGH"


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("AASHRAY VILLAGE-LEVEL RISK ENGINE")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # LOAD VILLAGES
    # ========================================================

    print()
    print("Loading pilot villages...")

    villages = gpd.read_file(
        VILLAGES_FILE
    )

    print(
        f"Villages: {len(villages)}"
    )

    print()
    print(
        villages[
            ["village", "vlcode"]
        ]
        .to_string(index=False)
    )

    # ========================================================
    # LOAD SUSCEPTIBILITY
    # ========================================================

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

        transform = src.transform

        raster_crs = src.crs

        raster_shape = (
            src.height,
            src.width
        )

        raster_bounds = src.bounds

    print(
        f"Raster shape: "
        f"{raster_shape}"
    )

    print(
        f"Raster CRS: "
        f"{raster_crs}"
    )

    # ========================================================
    # CRS ALIGNMENT
    # ========================================================

    if villages.crs != raster_crs:

        print()
        print(
            "Reprojecting village boundaries "
            "to raster CRS..."
        )

        villages = villages.to_crs(
            raster_crs
        )

    # ========================================================
    # VALID PIXELS
    # ========================================================

    valid = (
        np.isfinite(
            susceptibility
        )
        &
        (susceptibility >= 0)
    )

    # ========================================================
    # LOAD RAINFALL
    # ========================================================

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

    required_columns = [
        "date",
        "rainfall_mm",
        "rainfall_3day",
        "rainfall_7day",
        "rainfall_30day",
    ]

    missing = [
        column
        for column in required_columns
        if column not in rainfall.columns
    ]

    if missing:

        raise ValueError(
            "Missing rainfall columns: "
            f"{missing}"
        )

    rainfall = rainfall[
        required_columns
    ].copy()

    # One rainfall record per date
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
        f"Rainfall dates: "
        f"{len(rainfall)}"
    )

    # ========================================================
    # CREATE VILLAGE PIXEL MASKS
    # ========================================================

    print()
    print(
        "Creating village raster masks..."
    )

    village_masks = {}

    for _, village_row in villages.iterrows():

        village_name = str(
            village_row["village"]
        )

        vlcode = village_row[
            "vlcode"
        ]

        geometry = village_row[
            "geometry"
        ]

        mask = geometry_mask(
            [geometry],
            transform=transform,
            invert=True,
            out_shape=raster_shape
        )

        mask = (
            mask
            &
            valid
        )

        village_masks[
            village_name
        ] = {
            "vlcode": vlcode,
            "mask": mask
        }

        print(
            f"  {village_name}: "
            f"{int(mask.sum()):,} valid pixels"
        )

    # ========================================================
    # GENERATE VILLAGE RISK FOR EVERY DATE
    # ========================================================

    print()
    print(
        "Calculating village-level risk..."
    )

    results = []

    total_dates = len(
        rainfall
    )

    for date_index, rainfall_row in rainfall.iterrows():

        date = rainfall_row[
            "date"
        ]

        rainfall_1d = float(
            rainfall_row[
                "rainfall_mm"
            ]
        )

        rainfall_3d = float(
            rainfall_row[
                "rainfall_3day"
            ]
        )

        rainfall_7d = float(
            rainfall_row[
                "rainfall_7day"
            ]
        )

        rainfall_30d = float(
            rainfall_row[
                "rainfall_30day"
            ]
        )

        # --------------------------------------------
        # Rainfall trigger
        # --------------------------------------------

        trigger = calculate_trigger(
            rainfall_1d,
            rainfall_3d,
            rainfall_7d,
            rainfall_30d
        )

        # --------------------------------------------
        # Each village
        # --------------------------------------------

        for village_name, village_data in village_masks.items():

            mask = village_data[
                "mask"
            ]

            pixels = susceptibility[
                mask
            ]

            if len(pixels) == 0:
                continue

            # ----------------------------------------
            # Susceptibility statistics
            # ----------------------------------------

            mean_susceptibility = float(
                np.mean(
                    pixels
                )
            )

            median_susceptibility = float(
                np.median(
                    pixels
                )
            )

            max_susceptibility = float(
                np.max(
                    pixels
                )
            )

            high_pixels = int(
                np.sum(
                    pixels >= 0.50
                )
            )

            very_high_pixels = int(
                np.sum(
                    pixels >= 0.75
                )
            )

            high_percentage = (
                high_pixels
                /
                len(pixels)
                *
                100
            )

            very_high_percentage = (
                very_high_pixels
                /
                len(pixels)
                *
                100
            )

            # ----------------------------------------
            # Dynamic risk
            # ----------------------------------------

            dynamic_risk = (
                0.70
                *
                mean_susceptibility
                +
                0.30
                *
                trigger
            )

            category = risk_category(
                dynamic_risk
            )

            # ----------------------------------------
            # Save result
            # ----------------------------------------

            results.append(
                {
                    "date": date,

                    "village":
                        village_name,

                    "vlcode":
                        village_data[
                            "vlcode"
                        ],

                    "rainfall_mm":
                        rainfall_1d,

                    "rainfall_3day":
                        rainfall_3d,

                    "rainfall_7day":
                        rainfall_7d,

                    "rainfall_30day":
                        rainfall_30d,

                    "rainfall_trigger":
                        trigger,

                    "mean_susceptibility":
                        mean_susceptibility,

                    "median_susceptibility":
                        median_susceptibility,

                    "max_susceptibility":
                        max_susceptibility,

                    "high_risk_pixels":
                        high_pixels,

                    "very_high_risk_pixels":
                        very_high_pixels,

                    "high_risk_percentage":
                        high_percentage,

                    "very_high_risk_percentage":
                        very_high_percentage,

                    "dynamic_risk":
                        dynamic_risk,

                    "risk_category":
                        category,
                }
            )

        # Progress
        if (
            (date_index + 1) % 30 == 0
            or
            (date_index + 1) == total_dates
        ):

            print(
                f"Processed "
                f"{date_index + 1}/"
                f"{total_dates} dates"
            )

    # ========================================================
    # CREATE DATAFRAME
    # ========================================================

    results_df = pd.DataFrame(
        results
    )

    # ========================================================
    # SAVE
    # ========================================================

    results_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # LATEST DATE
    # ========================================================

    latest_date = (
        results_df["date"].max()
    )

    latest = (
        results_df[
            results_df["date"]
            == latest_date
        ]
        .sort_values(
            "dynamic_risk",
            ascending=False
        )
    )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print()
    print("=" * 70)
    print("VILLAGE-LEVEL RISK RESULTS")
    print("=" * 70)

    print()
    print(
        f"Latest date: "
        f"{latest_date.date()}"
    )

    print()

    display_columns = [
        "village",
        "mean_susceptibility",
        "high_risk_percentage",
        "very_high_risk_percentage",
        "rainfall_mm",
        "rainfall_3day",
        "rainfall_7day",
        "rainfall_trigger",
        "dynamic_risk",
        "risk_category",
    ]

    print(
        latest[
            display_columns
        ]
        .to_string(
            index=False
        )
    )

    # ========================================================
    # HIGHEST VILLAGE RISK
    # ========================================================

    highest = (
        results_df
        .sort_values(
            "dynamic_risk",
            ascending=False
        )
        .head(10)
    )

    print()
    print("=" * 70)
    print("TOP 10 VILLAGE-RISK RECORDS")
    print("=" * 70)

    print(
        highest[
            [
                "date",
                "village",
                "dynamic_risk",
                "risk_category",
                "rainfall_mm",
                "rainfall_3day",
                "rainfall_7day",
            ]
        ]
        .to_string(
            index=False
        )
    )

    # ========================================================
    # CATEGORY COUNTS
    # ========================================================

    print()
    print("=" * 70)
    print("RISK CATEGORY COUNTS")
    print("=" * 70)

    print(
        results_df[
            "risk_category"
        ]
        .value_counts()
        .to_string()
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    print()
    print("=" * 70)
    print("VILLAGE RISK ENGINE COMPLETE")
    print("=" * 70)

    print()
    print(
        f"Total records: "
        f"{len(results_df)}"
    )

    print(
        f"Villages: "
        f"{results_df['village'].nunique()}"
    )

    print(
        f"Dates: "
        f"{results_df['date'].nunique()}"
    )

    print()
    print(
        f"Saved to:\n"
        f"{OUTPUT_FILE.resolve()}"
    )

    print()
    print(
        "Risk equation:"
    )

    print(
        "Dynamic Risk = "
        "0.70 × Village Susceptibility "
        "+ "
        "0.30 × Rainfall Trigger"
    )

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()