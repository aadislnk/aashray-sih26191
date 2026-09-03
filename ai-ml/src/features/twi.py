from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import uniform_filter


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ELEVATION_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "terrain"
    / "elevation.tif"
)

SLOPE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "terrain"
    / "slope.tif"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "terrain"
)

OUTPUT_FILE = OUTPUT_DIR / "twi.tif"


def main():

    print("Loading elevation and slope...")

    with rasterio.open(ELEVATION_FILE) as elev_src:
        elevation = elev_src.read(1, masked=True)
        profile = elev_src.profile.copy()

    with rasterio.open(SLOPE_FILE) as slope_src:
        slope = slope_src.read(1, masked=True)

    elevation_data = elevation.filled(np.nan)
    slope_data = slope.filled(np.nan)

    print("Calculating terrain wetness indicator...")

    # Convert slope from degrees to radians.
    slope_rad = np.radians(slope_data)

    # Prevent division by zero.
    slope_rad = np.maximum(
        slope_rad,
        np.radians(0.1)
    )

    # Simple local accumulation proxy.
    valid_elevation = np.nan_to_num(
        elevation_data,
        nan=0.0
    )

    local_elevation = uniform_filter(
        valid_elevation,
        size=5
    )

    accumulation = np.maximum(
        local_elevation - elevation_data + 1.0,
        1.0
    )

    twi = np.log(
        accumulation / np.tan(slope_rad)
    )

    twi[np.isnan(elevation_data)] = np.nan

    profile.update(
        dtype="float32",
        count=1,
        compress="lzw"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with rasterio.open(
        OUTPUT_FILE,
        "w",
        **profile
    ) as dst:

        dst.write(
            twi.astype("float32"),
            1
        )

    print("\nTWI generation completed.")

    print("Saved to:")
    print(OUTPUT_FILE.resolve())


if __name__ == "__main__":
    main()