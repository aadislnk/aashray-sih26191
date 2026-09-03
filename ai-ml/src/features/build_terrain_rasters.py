from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import xy
from scipy.ndimage import gaussian_filter


# ============================================================
# PATHS
# ============================================================

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


# ============================================================
# SLOPE
# ============================================================

def calculate_slope(
    dem,
    latitude,
    x_resolution,
    y_resolution
):
    """
    Calculate slope in degrees.

    DEM is in EPSG:4326, so the geographic
    resolution is converted approximately
    to metres at the mean latitude.
    """

    meters_per_degree_lat = 111320.0

    meters_per_degree_lon = (
        111320.0
        * np.cos(
            np.radians(latitude)
        )
    )

    dx = (
        x_resolution
        * meters_per_degree_lon
    )

    dy = (
        y_resolution
        * meters_per_degree_lat
    )

    dz_dy, dz_dx = np.gradient(
        dem,
        dy,
        dx
    )

    slope = np.degrees(
        np.arctan(
            np.sqrt(
                dz_dx ** 2
                +
                dz_dy ** 2
            )
        )
    )

    return slope


# ============================================================
# ASPECT
# ============================================================

def calculate_aspect(
    dem,
    latitude,
    x_resolution,
    y_resolution
):
    """
    Calculate aspect in degrees.

    0   = North
    90  = East
    180 = South
    270 = West
    """

    meters_per_degree_lat = 111320.0

    meters_per_degree_lon = (
        111320.0
        * np.cos(
            np.radians(latitude)
        )
    )

    dx = (
        x_resolution
        * meters_per_degree_lon
    )

    dy = (
        y_resolution
        * meters_per_degree_lat
    )

    dz_dy, dz_dx = np.gradient(
        dem,
        dy,
        dx
    )

    aspect = np.degrees(
        np.arctan2(
            -dz_dx,
            dz_dy
        )
    )

    aspect = (
        90.0 - aspect
    ) % 360.0

    return aspect


# ============================================================
# APPROXIMATE FLOW ACCUMULATION
# ============================================================

def calculate_flow_accumulation(
    dem,
    smoothing_sigma=1.0
):
    """
    Create a terrain-based contributing-area proxy.

    This is intentionally labelled as an approximation.

    It is suitable for the AASHRAY pilot/MVP and avoids
    requiring native hydrology packages such as RichDEM.
    """

    # Smooth very small DEM noise.
    smooth_dem = gaussian_filter(
        dem,
        sigma=smoothing_sigma
    )

    # Calculate gradients.
    grad_y, grad_x = np.gradient(
        smooth_dem
    )

    gradient_magnitude = np.sqrt(
        grad_x ** 2
        +
        grad_y ** 2
    )

    # Areas with relatively small local gradient
    # tend to retain/accumulate more water.
    contributing_area = (
        1.0
        /
        (
            gradient_magnitude
            + 0.001
        )
    )

    # Avoid extremely large numerical values.
    contributing_area = np.clip(
        contributing_area,
        1.0,
        np.percentile(
            contributing_area,
            99.5
        )
    )

    return contributing_area


# ============================================================
# TWI
# ============================================================

def calculate_twi(
    dem,
    slope
):
    """
    Calculate an approximate Topographic Wetness Index.

    TWI = ln(A / tan(beta))

    where:

        A    = local contributing-area proxy
        beta = slope angle
    """

    contributing_area = (
        calculate_flow_accumulation(
            dem
        )
    )

    slope_rad = np.radians(
        slope
    )

    tan_slope = np.tan(
        slope_rad
    )

    # Prevent division by zero.
    tan_slope = np.maximum(
        tan_slope,
        0.001
    )

    twi = np.log(
        contributing_area
        /
        tan_slope
    )

    # Prevent extreme numerical values.
    twi = np.clip(
        twi,
        -10,
        20
    )

    return twi


# ============================================================
# SAVE RASTER
# ============================================================

def save_raster(
    output_file,
    data,
    profile
):

    output_profile = profile.copy()

    output_profile.update(
        dtype="float32",
        count=1,
        compress="lzw",
        nodata=-9999.0
    )

    data = np.where(
        np.isfinite(data),
        data,
        -9999.0
    ).astype(
        "float32"
    )

    with rasterio.open(
        output_file,
        "w",
        **output_profile
    ) as dst:

        dst.write(
            data,
            1
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("AASHRAY TERRAIN RASTER GENERATION")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # LOAD DEM
    # --------------------------------------------------------

    print()
    print("Loading DEM...")

    with rasterio.open(
        DEM_FILE
    ) as src:

        dem = src.read(
            1
        ).astype(
            "float64"
        )

        profile = src.profile.copy()

        transform = src.transform

        crs = src.crs

        x_resolution = abs(
            src.res[0]
        )

        y_resolution = abs(
            src.res[1]
        )

        nodata = src.nodata

        bounds = src.bounds

        height = src.height
        width = src.width

    print(
        f"CRS: {crs}"
    )

    print(
        f"Size: {width} x {height}"
    )

    print(
        f"Resolution: "
        f"{x_resolution}, "
        f"{y_resolution}"
    )

    print(
        f"Bounds: {bounds}"
    )

    # --------------------------------------------------------
    # NODATA
    # --------------------------------------------------------

    if nodata is not None:

        dem[
            dem == nodata
        ] = np.nan

    # Fill NaNs temporarily for gradient calculations.
    if np.isnan(dem).any():

        median_elevation = np.nanmedian(
            dem
        )

        dem_for_calc = np.where(
            np.isnan(dem),
            median_elevation,
            dem
        )

    else:

        dem_for_calc = dem

    # --------------------------------------------------------
    # MEAN LATITUDE
    # --------------------------------------------------------

    top_lat = bounds.top
    bottom_lat = bounds.bottom

    mean_latitude = (
        top_lat
        +
        bottom_lat
    ) / 2.0

    print(
        f"Mean latitude: "
        f"{mean_latitude:.4f}"
    )

    # --------------------------------------------------------
    # SLOPE
    # --------------------------------------------------------

    print()
    print("Calculating slope...")

    slope = calculate_slope(
        dem_for_calc,
        mean_latitude,
        x_resolution,
        y_resolution
    )

    print(
        "Slope calculation completed."
    )

    # --------------------------------------------------------
    # ASPECT
    # --------------------------------------------------------

    print()
    print("Calculating aspect...")

    aspect = calculate_aspect(
        dem_for_calc,
        mean_latitude,
        x_resolution,
        y_resolution
    )

    print(
        "Aspect calculation completed."
    )

    # --------------------------------------------------------
    # TWI
    # --------------------------------------------------------

    print()
    print(
        "Calculating TWI..."
    )

    twi = calculate_twi(
        dem_for_calc,
        slope
    )

    print(
        "TWI calculation completed."
    )

    # --------------------------------------------------------
    # RESTORE NODATA
    # --------------------------------------------------------

    if np.isnan(dem).any():

        slope[
            np.isnan(dem)
        ] = np.nan

        aspect[
            np.isnan(dem)
        ] = np.nan

        twi[
            np.isnan(dem)
        ] = np.nan

    # --------------------------------------------------------
    # OUTPUT FILES
    # --------------------------------------------------------

    slope_file = (
        OUTPUT_DIR
        / "wayanad_pilot_slope.tif"
    )

    aspect_file = (
        OUTPUT_DIR
        / "wayanad_pilot_aspect.tif"
    )

    twi_file = (
        OUTPUT_DIR
        / "wayanad_pilot_twi.tif"
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    print()
    print("Saving terrain rasters...")

    save_raster(
        slope_file,
        slope,
        profile
    )

    print(
        f"Saved slope:\n"
        f"{slope_file}"
    )

    save_raster(
        aspect_file,
        aspect,
        profile
    )

    print(
        f"Saved aspect:\n"
        f"{aspect_file}"
    )

    save_raster(
        twi_file,
        twi,
        profile
    )

    print(
        f"Saved TWI:\n"
        f"{twi_file}"
    )

    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("TERRAIN RASTER STATISTICS")
    print("=" * 70)

    print()
    print("Slope:")
    print(
        f"Min:  {np.nanmin(slope):.3f}"
    )
    print(
        f"Mean: {np.nanmean(slope):.3f}"
    )
    print(
        f"Max:  {np.nanmax(slope):.3f}"
    )

    print()
    print("Aspect:")
    print(
        f"Min:  {np.nanmin(aspect):.3f}"
    )
    print(
        f"Mean: {np.nanmean(aspect):.3f}"
    )
    print(
        f"Max:  {np.nanmax(aspect):.3f}"
    )

    print()
    print("TWI:")
    print(
        f"Min:  {np.nanmin(twi):.3f}"
    )
    print(
        f"Mean: {np.nanmean(twi):.3f}"
    )
    print(
        f"Max:  {np.nanmax(twi):.3f}"
    )

    print()
    print("=" * 70)
    print("TERRAIN RASTER GENERATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()