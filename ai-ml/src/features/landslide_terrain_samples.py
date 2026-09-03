from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import rowcol
from scipy.ndimage import sobel
from rasterstats import point_query


PROJECT_ROOT = Path(__file__).resolve().parents[2]

LANDSLIDE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "landslides"
    / "pilot_landslide_inventory_clean.csv"
)

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
    / "features"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "pilot_landslide_terrain_samples.csv"
)


def calculate_slope_aspect(dem, xres, yres):

    """
    Calculate slope and aspect from DEM.

    DEM elevation is in metres.
    xres/yres are converted approximately to metres
    using the latitude of the DEM.
    """

    # Estimate metres per degree.
    # Pilot area is around 11.5 degrees latitude.

    meters_per_degree_lat = 111320.0

    meters_per_degree_lon = (
        111320.0
        * np.cos(
            np.radians(11.5)
        )
    )

    dx = xres * meters_per_degree_lon
    dy = yres * meters_per_degree_lat

    # Gradient.
    dz_dy, dz_dx = np.gradient(
        dem,
        dy,
        dx
    )

    # Slope in degrees.
    slope = np.degrees(
        np.arctan(
            np.sqrt(
                dz_dx ** 2
                +
                dz_dy ** 2
            )
        )
    )

    # Aspect.
    aspect = np.degrees(
        np.arctan2(
            -dz_dx,
            dz_dy
        )
    )

    aspect = (
        90.0 - aspect
    ) % 360.0

    return slope, aspect


def calculate_twi(
    dem,
    slope,
    xres,
    yres
):

    """
    Approximate TWI.

    TWI = ln(
        upslope contributing area
        /
        tan(slope)
    )

    For the pilot MVP we estimate local
    contributing area using a neighbourhood
    approximation.

    This is a terrain-derived indicator,
    not a hydrological simulation.
    """

    slope_rad = np.radians(
        slope
    )

    tan_slope = np.tan(
        slope_rad
    )

    # Avoid division by zero.
    tan_slope = np.maximum(
        tan_slope,
        0.001
    )

    # Simple local contributing-area proxy.
    #
    # The DEM gradient magnitude indicates
    # local drainage tendency. We use a
    # smoothed neighbourhood proxy rather
    # than pretending to calculate a full
    # flow-routing model.

    elevation_gradient = np.sqrt(
        np.gradient(
            dem,
            axis=0
        ) ** 2
        +
        np.gradient(
            dem,
            axis=1
        ) ** 2
    )

    # Convert to a positive contributing-area
    # proxy.
    contributing_area = (
        1.0
        +
        1.0
        /
        (
            elevation_gradient
            +
            0.001
        )
    )

    twi = np.log(
        contributing_area
        /
        tan_slope
    )

    return twi


def sample_raster(
    raster,
    transform,
    gdf
):

    values = []

    for point in gdf.geometry:

        row, col = rowcol(
            transform,
            point.x,
            point.y
        )

        if (
            0 <= row < raster.shape[0]
            and
            0 <= col < raster.shape[1]
        ):

            values.append(
                float(
                    raster[row, col]
                )
            )

        else:

            values.append(
                np.nan
            )

    return values


def main():

    print(
        "Loading historical landslide points..."
    )

    df = pd.read_csv(
        LANDSLIDE_FILE
    )

    print(
        f"Landslide points: {len(df)}"
    )

    # --------------------------------------------------------
    # CREATE POINTS
    # --------------------------------------------------------

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df["longitude"],
            df["latitude"]
        ),
        crs="EPSG:4326"
    )

    # --------------------------------------------------------
    # LOAD DEM
    # --------------------------------------------------------

    print(
        "\nLoading DEM..."
    )

    with rasterio.open(
        DEM_FILE
    ) as src:

        dem = src.read(
            1
        ).astype(
            "float64"
        )

        transform = src.transform

        crs = src.crs

        xres = abs(
            src.res[0]
        )

        yres = abs(
            src.res[1]
        )

        nodata = src.nodata

        print(
            f"DEM CRS: {crs}"
        )

        print(
            f"DEM resolution: "
            f"{src.res}"
        )

        print(
            f"DEM shape: "
            f"{dem.shape}"
        )

        print(
            f"DEM nodata: "
            f"{nodata}"
        )

    # --------------------------------------------------------
    # HANDLE NODATA
    # --------------------------------------------------------

    if nodata is not None:

        dem[
            dem == nodata
        ] = np.nan

    # --------------------------------------------------------
    # ELEVATION
    # --------------------------------------------------------

    print(
        "\nExtracting elevation..."
    )

    gdf = gdf.to_crs(
        crs
    )

    gdf["elevation"] = sample_raster(
        dem,
        transform,
        gdf
    )

    # --------------------------------------------------------
    # SLOPE + ASPECT
    # --------------------------------------------------------

    print(
        "Calculating slope..."
    )

    slope, aspect = (
        calculate_slope_aspect(
            dem,
            xres,
            yres
        )
    )

    print(
        "Extracting slope..."
    )

    gdf["slope"] = sample_raster(
        slope,
        transform,
        gdf
    )

    print(
        "Extracting aspect..."
    )

    gdf["aspect"] = sample_raster(
        aspect,
        transform,
        gdf
    )

    # --------------------------------------------------------
    # TWI
    # --------------------------------------------------------

    print(
        "Calculating TWI..."
    )

    twi = calculate_twi(
        dem,
        slope,
        xres,
        yres
    )

    print(
        "Extracting TWI..."
    )

    gdf["twi"] = sample_raster(
        twi,
        transform,
        gdf
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    output_columns = [
        "slide_no",
        "village",
        "vlcode",
        "latitude",
        "longitude",
        "movement_type",
        "history",
        "event_year",
        "source_page",
        "elevation",
        "slope",
        "aspect",
        "twi",
    ]

    result = gdf[
        output_columns
    ].copy()

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print()
    print(
        "=" * 60
    )

    print(
        "LANDSLIDE TERRAIN SAMPLES"
    )

    print(
        "=" * 60
    )

    print(
        f"Records: {len(result)}"
    )

    print()

    print(
        "Missing values:"
    )

    print(
        result[
            [
                "elevation",
                "slope",
                "aspect",
                "twi"
            ]
        ]
        .isna()
        .sum()
        .to_string()
    )

    print()

    print(
        "Terrain statistics:"
    )

    print(
        result[
            [
                "elevation",
                "slope",
                "aspect",
                "twi"
            ]
        ]
        .describe()
        .to_string()
    )

    print()

    print(
        f"Saved to:\n"
        f"{OUTPUT_FILE.resolve()}"
    )

    print()

    print(
        "First 15 records:"
    )

    print(
        result.head(15)
        .to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()