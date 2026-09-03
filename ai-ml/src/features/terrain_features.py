from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEM_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "dem"
    / "wayanad_pilot_dem.tif"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "terrain"
)


def calculate_slope_aspect(elevation, transform):
    """
    Calculate slope and aspect from the DEM.

    The DEM is in geographic coordinates (degrees), so we first
    approximate the pixel size in metres at the study latitude.
    """

    pixel_width_deg = abs(transform.a)
    pixel_height_deg = abs(transform.e)

    # Approximate conversion from degrees to metres.
    # Study area is around 11.5 degrees north.
    latitude = 11.5

    meters_per_degree_lat = 111320
    meters_per_degree_lon = 111320 * np.cos(
        np.radians(latitude)
    )

    dx = pixel_width_deg * meters_per_degree_lon
    dy = pixel_height_deg * meters_per_degree_lat

    dz_dy, dz_dx = np.gradient(
        elevation,
        dy,
        dx
    )

    slope = np.degrees(
        np.arctan(
            np.sqrt(
                dz_dx ** 2 +
                dz_dy ** 2
            )
        )
    )

    aspect = np.degrees(
        np.arctan2(
            -dz_dx,
            dz_dy
        )
    )

    aspect = (aspect + 360) % 360

    return slope, aspect


def save_raster(output_file, data, profile):

    profile = profile.copy()

    profile.update(
        dtype="float32",
        count=1,
        compress="lzw"
    )

    with rasterio.open(
        output_file,
        "w",
        **profile
    ) as dst:

        dst.write(
            data.astype("float32"),
            1
        )


def main():

    print("Loading pilot DEM...")

    with rasterio.open(DEM_FILE) as src:

        elevation = src.read(
            1,
            masked=True
        )

        profile = src.profile.copy()
        transform = src.transform

        print(f"DEM shape: {elevation.shape}")
        print(f"DEM CRS: {src.crs}")
        print(f"DEM resolution: {src.res}")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Convert masked array to normal array.
    elevation_data = elevation.filled(np.nan)

    print("\nCalculating slope and aspect...")

    slope, aspect = calculate_slope_aspect(
        elevation_data,
        transform
    )

    # Preserve NoData areas.
    slope[np.isnan(elevation_data)] = np.nan
    aspect[np.isnan(elevation_data)] = np.nan

    print("Saving terrain features...")

    save_raster(
        OUTPUT_DIR / "elevation.tif",
        elevation_data,
        profile
    )

    save_raster(
        OUTPUT_DIR / "slope.tif",
        slope,
        profile
    )

    save_raster(
        OUTPUT_DIR / "aspect.tif",
        aspect,
        profile
    )

    print("\nTerrain feature generation completed.")

    print(f"Output directory:")
    print(OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()