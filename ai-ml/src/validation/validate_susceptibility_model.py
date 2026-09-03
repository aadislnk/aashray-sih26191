from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.sample import sample_gen


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LANDSLIDES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "landslides"
    / "pilot_landslide_inventory_clean.csv"
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
    / "validation"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "landslide_susceptibility_validation.csv"
)


# ============================================================
# CLASSIFICATION
# ============================================================

def classify(value):

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
    print("AASHRAY SUSCEPTIBILITY MODEL VALIDATION")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # LOAD LANDSLIDES
    # ========================================================

    print()
    print(
        "Loading historical landslides..."
    )

    landslides = pd.read_csv(
        LANDSLIDES_FILE
    )

    print(
        f"Landslide events: "
        f"{len(landslides)}"
    )

    # ========================================================
    # LOAD SUSCEPTIBILITY RASTER
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
        )

        transform = src.transform

        crs = src.crs

        nodata = src.nodata

        print(
            f"Raster shape: "
            f"{susceptibility.shape}"
        )

        print(
            f"Raster CRS: "
            f"{crs}"
        )

        print(
            f"Raster nodata: "
            f"{nodata}"
        )

        # ----------------------------------------------------
        # Coordinates
        # ----------------------------------------------------

        coordinates = list(
            zip(
                landslides[
                    "longitude"
                ].astype(float),

                landslides[
                    "latitude"
                ].astype(float)
            )
        )

        # ----------------------------------------------------
        # Sample raster
        # ----------------------------------------------------

        samples = list(
            src.sample(
                coordinates
            )
        )

    values = np.array(
        [
            float(sample[0])
            for sample in samples
        ]
    )

    landslides[
        "susceptibility"
    ] = values

    # ========================================================
    # REMOVE INVALID
    # ========================================================

    invalid = (
        ~np.isfinite(
            landslides[
                "susceptibility"
            ]
        )
        |
        (
            landslides[
                "susceptibility"
            ] < 0
        )
    )

    invalid_count = int(
        invalid.sum()
    )

    if invalid_count > 0:

        print()
        print(
            f"Removing invalid samples: "
            f"{invalid_count}"
        )

        landslides = landslides[
            ~invalid
        ].copy()

    # ========================================================
    # CLASSIFY
    # ========================================================

    landslides[
        "susceptibility_class"
    ] = (
        landslides[
            "susceptibility"
        ]
        .apply(classify)
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("HISTORICAL LANDSLIDE SUSCEPTIBILITY")
    print("=" * 70)

    print()

    print(
        "Mean susceptibility:",
        f"{landslides['susceptibility'].mean():.4f}"
    )

    print(
        "Median susceptibility:",
        f"{landslides['susceptibility'].median():.4f}"
    )

    print(
        "Minimum susceptibility:",
        f"{landslides['susceptibility'].min():.4f}"
    )

    print(
        "Maximum susceptibility:",
        f"{landslides['susceptibility'].max():.4f}"
    )

    # ========================================================
    # CLASS DISTRIBUTION
    # ========================================================

    print()
    print("=" * 70)
    print("LANDSLIDES BY SUSCEPTIBILITY CLASS")
    print("=" * 70)

    class_counts = (
        landslides[
            "susceptibility_class"
        ]
        .value_counts()
    )

    print(
        class_counts.to_string()
    )

    # ========================================================
    # HIGH + VERY HIGH
    # ========================================================

    high_count = int(
        landslides[
            "susceptibility_class"
        ]
        .isin(
            [
                "HIGH",
                "VERY HIGH"
            ]
        )
        .sum()
    )

    high_percentage = (
        high_count
        /
        len(landslides)
        *
        100
    )

    print()
    print(
        "Landslides in HIGH/VERY HIGH zones:",
        high_count,
        f"({high_percentage:.2f}%)"
    )

    # ========================================================
    # VERY HIGH
    # ========================================================

    very_high_count = int(
        (
            landslides[
                "susceptibility_class"
            ]
            == "VERY HIGH"
        )
        .sum()
    )

    very_high_percentage = (
        very_high_count
        /
        len(landslides)
        *
        100
    )

    print(
        "Landslides in VERY HIGH zones:",
        very_high_count,
        f"({very_high_percentage:.2f}%)"
    )

    # ========================================================
    # VILLAGE ANALYSIS
    # ========================================================

    print()
    print("=" * 70)
    print("VILLAGE-WISE VALIDATION")
    print("=" * 70)

    village_summary = (
        landslides
        .groupby(
            "village"
        )
        .agg(
            landslide_count=(
                "slide_no",
                "count"
            ),

            mean_susceptibility=(
                "susceptibility",
                "mean"
            ),

            median_susceptibility=(
                "susceptibility",
                "median"
            ),

            max_susceptibility=(
                "susceptibility",
                "max"
            )
        )
        .reset_index()
    )

    village_summary[
        "high_very_high_count"
    ] = (
        landslides
        .assign(
            high_or_very_high=
            landslides[
                "susceptibility_class"
            ].isin(
                [
                    "HIGH",
                    "VERY HIGH"
                ]
            )
        )
        .groupby(
            "village"
        )[
            "high_or_very_high"
        ]
        .sum()
        .values
    )

    village_summary[
        "high_very_high_percentage"
    ] = (
        village_summary[
            "high_very_high_count"
        ]
        /
        village_summary[
            "landslide_count"
        ]
        *
        100
    )

    print(
        village_summary.to_string(
            index=False
        )
    )

    # ========================================================
    # MOVEMENT TYPE
    # ========================================================

    print()
    print("=" * 70)
    print("MOVEMENT TYPE VALIDATION")
    print("=" * 70)

    movement_summary = (
        landslides
        .groupby(
            "movement_type"
        )
        .agg(
            events=(
                "slide_no",
                "count"
            ),

            mean_susceptibility=(
                "susceptibility",
                "mean"
            )
        )
        .sort_values(
            "events",
            ascending=False
        )
        .reset_index()
    )

    print(
        movement_summary.to_string(
            index=False
        )
    )

    # ========================================================
    # SAVE
    # ========================================================

    landslides.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)

    print()
    print(
        f"Validated events: "
        f"{len(landslides)}"
    )

    print(
        f"Invalid samples removed: "
        f"{invalid_count}"
    )

    print()
    print(
        f"Saved to:\n"
        f"{OUTPUT_FILE.resolve()}"
    )

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()