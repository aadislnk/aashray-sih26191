from pathlib import Path

import geopandas as gpd
import pandas as pd
import rasterio
from rasterstats import zonal_stats


PROJECT_ROOT = Path(__file__).resolve().parents[2]

VILLAGES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "administrative"
    / "wayanad_pilot_villages.geojson"
)

TERRAIN_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "terrain"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "features"
    / "village_terrain_features.csv"
)


def extract_mean(villages, raster_file):
    """
    Extract the mean raster value inside each village polygon.
    """

    with rasterio.open(raster_file) as src:

        villages = villages.to_crs(src.crs)

        stats = zonal_stats(
            villages.geometry,
            raster_file,
            stats=["mean"],
            nodata=src.nodata
        )

    return [
        item["mean"]
        for item in stats
    ]


def main():

    print("Loading pilot villages...")

    villages = gpd.read_file(VILLAGES_FILE)

    print(f"Villages: {len(villages)}")

    print("\nVillages selected:")

    print(
        villages[
            ["village", "vlcode"]
        ].to_string(index=False)
    )

    print("\nExtracting elevation...")

    villages["elevation_mean"] = extract_mean(
        villages,
        TERRAIN_DIR / "elevation.tif"
    )

    print("Extracting slope...")

    villages["slope_mean"] = extract_mean(
        villages,
        TERRAIN_DIR / "slope.tif"
    )

    print("Extracting aspect...")

    villages["aspect_mean"] = extract_mean(
        villages,
        TERRAIN_DIR / "aspect.tif"
    )

    print("Extracting TWI...")

    villages["twi_mean"] = extract_mean(
        villages,
        TERRAIN_DIR / "twi.tif"
    )

    # Keep only the information needed by the AI pipeline.
    df = villages[
        [
            "village",
            "vlcode",
            "subdistric",
            "district",
            "elevation_mean",
            "slope_mean",
            "aspect_mean",
            "twi_mean"
        ]
    ].copy()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nVillage terrain feature extraction completed.")

    print(
        f"Saved to:\n{OUTPUT_FILE.resolve()}"
    )

    print("\nFinal feature table:")

    print(
        df.to_string(index=False)
    )


if __name__ == "__main__":
    main()