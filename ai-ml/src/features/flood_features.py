import os
import glob
import re
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

FLOOD_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "flood"
)

VILLAGE_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "administrative",
    "wayanad_pilot_villages.geojson"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "features"
)

OUTPUT_PATH = os.path.join(
    OUTPUT_DIR,
    "pilot_flood_features.csv"
)


def get_return_period(path):

    filename = os.path.basename(path)

    match = re.search(
        r"wayanad_flood_(\d+)yr",
        filename
    )

    if match:
        return int(match.group(1))

    return None


def classify_flood(level_m):

    if np.isnan(level_m):
        return "NO_DATA"

    if level_m < 4:
        return "LOW"

    if level_m < 8:
        return "MODERATE"

    if level_m < 12:
        return "HIGH"

    return "VERY HIGH"


def main():

    print("=" * 70)
    print("AASHRAY CORRECTED FLOOD FEATURE EXTRACTION")
    print("=" * 70)

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    # ------------------------------------------------------------
    # LOAD VILLAGES
    # ------------------------------------------------------------

    print("\nLoading pilot villages...")

    villages = gpd.read_file(
        VILLAGE_PATH
    )

    print(
        "Villages loaded:",
        len(villages)
    )

    # ------------------------------------------------------------
    # FIND FLOOD RASTERS
    # ------------------------------------------------------------

    flood_files = sorted(
        glob.glob(
            os.path.join(
                FLOOD_DIR,
                "wayanad_flood_*yr_historical.tif"
            )
        )
    )

    print(
        "\nFlood rasters found:",
        len(flood_files)
    )

    results = []

    # ------------------------------------------------------------
    # PROCESS EACH VILLAGE
    # ------------------------------------------------------------

    for _, village in villages.iterrows():

        village_name = village["village"]
        village_code = village["vlcode"]

        print("\n" + "-" * 70)
        print(village_name)
        print("-" * 70)

        village_geometry = [village.geometry]

        return_period_levels = {}

        # --------------------------------------------------------
        # PROCESS EACH RETURN PERIOD
        # --------------------------------------------------------

        for flood_path in flood_files:

            return_period = get_return_period(
                flood_path
            )

            if return_period is None:
                continue

            with rasterio.open(flood_path) as src:

                geometry = village_geometry

                if villages.crs != src.crs:
                    temp = gpd.GeoSeries(
                        village.geometry,
                        crs=villages.crs
                    ).to_crs(src.crs)

                    geometry = [
                        temp.iloc[0]
                    ]

                try:

                    clipped, _ = mask(
                        src,
                        geometry,
                        crop=True,
                        filled=False
                    )

                    values = clipped[0]

                    values = values.compressed()

                    values = values[
                        np.isfinite(values)
                    ]

                except Exception:

                    values = np.array([])

            if len(values) == 0:

                level_m = np.nan

                print(
                    f"  {return_period:>3}-year: "
                    "NO FLOOD DATA"
                )

            else:

                # KSDMA raster stores flood level
                # approximately 100 times the metre value.
                level_m = float(
                    np.median(values) / 100.0
                )

                print(
                    f"  {return_period:>3}-year: "
                    f"{level_m:.2f} m "
                    f"({len(values)} pixels)"
                )

            return_period_levels[
                return_period
            ] = level_m

        # --------------------------------------------------------
        # AVAILABLE LEVELS
        # --------------------------------------------------------

        valid_levels = [
            value
            for value in return_period_levels.values()
            if np.isfinite(value)
        ]

        if len(valid_levels) == 0:

            flood_level = np.nan
            flood_category = "NO_DATA"
            coverage_status = "NO_DATA"

        else:

            # Conservative hazard representation:
            # use the maximum available modeled flood level.
            flood_level = float(
                np.max(valid_levels)
            )

            flood_category = classify_flood(
                flood_level
            )

            coverage_status = "AVAILABLE"

        # --------------------------------------------------------
        # RETURN PERIOD VALUES
        # --------------------------------------------------------

        result = {
            "village": village_name,
            "vlcode": village_code,

            "flood_level_10yr_m":
                return_period_levels.get(
                    10,
                    np.nan
                ),

            "flood_level_25yr_m":
                return_period_levels.get(
                    25,
                    np.nan
                ),

            "flood_level_50yr_m":
                return_period_levels.get(
                    50,
                    np.nan
                ),

            "flood_level_100yr_m":
                return_period_levels.get(
                    100,
                    np.nan
                ),

            "flood_level_200yr_m":
                return_period_levels.get(
                    200,
                    np.nan
                ),

            "flood_level_500yr_m":
                return_period_levels.get(
                    500,
                    np.nan
                ),

            "max_flood_level_m":
                flood_level,

            "flood_category":
                flood_category,

            "coverage_status":
                coverage_status,

            "available_return_periods":
                len(valid_levels)
        }

        results.append(result)

    # ------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------

    df = pd.DataFrame(
        results
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    # ------------------------------------------------------------
    # DISPLAY
    # ------------------------------------------------------------

    print("\n" + "=" * 70)
    print("FLOOD FEATURE SUMMARY")
    print("=" * 70)

    print(
        df.to_string(
            index=False
        )
    )

    print("\n" + "=" * 70)
    print("CORRECTED FLOOD FEATURES SAVED")
    print("=" * 70)

    print(
        OUTPUT_PATH
    )


if __name__ == "__main__":
    main()