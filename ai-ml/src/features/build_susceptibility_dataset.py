from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from shapely.geometry import Point


PROJECT_ROOT = Path(__file__).resolve().parents[2]

LANDSLIDE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "landslides"
    / "pilot_landslide_inventory_clean.csv"
)

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

ELEVATION_FILE = (
    TERRAIN_DIR
    / "elevation.tif"
)

SLOPE_FILE = (
    TERRAIN_DIR
    / "slope_latest.tif"
)

ASPECT_FILE = (
    TERRAIN_DIR
    / "aspect_latest.tif"
)

TWI_FILE = (
    TERRAIN_DIR
    / "twi_latest.tif"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ml"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "susceptibility_dataset.csv"
)


RANDOM_SEED = 42

BACKGROUND_RATIO = 3

MIN_BACKGROUND_DISTANCE_METERS = 100


def sample_raster(
    raster_path,
    points
):

    with rasterio.open(
        raster_path
    ) as src:

        values = list(
            src.sample(
                [
                    (
                        point.x,
                        point.y
                    )
                    for point in points
                ]
            )
        )

        values = [
            float(value[0])
            for value in values
        ]

    return values


def main():

    np.random.seed(
        RANDOM_SEED
    )

    print(
        "Loading historical landslides..."
    )

    landslides = pd.read_csv(
        LANDSLIDE_FILE
    )

    print(
        f"Historical events: "
        f"{len(landslides)}"
    )

    # --------------------------------------------------------
    # CREATE LANDSLIDE POINTS
    # --------------------------------------------------------

    positive = gpd.GeoDataFrame(
        landslides,
        geometry=gpd.points_from_xy(
            landslides["longitude"],
            landslides["latitude"]
        ),
        crs="EPSG:4326"
    )

    # --------------------------------------------------------
    # LOAD VILLAGES
    # --------------------------------------------------------

    print(
        "\nLoading pilot villages..."
    )

    villages = gpd.read_file(
        VILLAGES_FILE
    )

    print(
        f"Pilot villages: "
        f"{len(villages)}"
    )

    # --------------------------------------------------------
    # PROJECT TO METRIC CRS
    # --------------------------------------------------------

    # EPSG:7755 is already being used by
    # the village dataset and is appropriate
    # for metric distance calculations.

    positive_metric = positive.to_crs(
        "EPSG:7755"
    )

    villages_metric = villages.to_crs(
        "EPSG:7755"
    )

    # Combine village polygons.
    pilot_area = villages_metric.geometry.union_all()

    # --------------------------------------------------------
    # GENERATE BACKGROUND POINTS
    # --------------------------------------------------------

    target_background = (
        len(positive)
        * BACKGROUND_RATIO
    )

    print()
    print(
        "Generating background points..."
    )

    print(
        f"Target background points: "
        f"{target_background}"
    )

    positive_geometries = list(
        positive_metric.geometry
    )

    minx, miny, maxx, maxy = (
        pilot_area.bounds
    )

    background_points = []

    attempts = 0

    max_attempts = (
        target_background
        * 1000
    )

    while (
        len(background_points)
        <
        target_background
        and
        attempts
        <
        max_attempts
    ):

        attempts += 1

        x = np.random.uniform(
            minx,
            maxx
        )

        y = np.random.uniform(
            miny,
            maxy
        )

        candidate = Point(
            x,
            y
        )

        # Must be inside pilot area.
        if not pilot_area.contains(
            candidate
        ):
            continue

        # Must be sufficiently far from
        # every historical landslide.
        too_close = False

        for event_point in positive_geometries:

            if (
                candidate.distance(
                    event_point
                )
                <
                MIN_BACKGROUND_DISTANCE_METERS
            ):

                too_close = True
                break

        if too_close:
            continue

        background_points.append(
            candidate
        )

    print(
        f"Background points created: "
        f"{len(background_points)}"
    )

    if len(background_points) < target_background:

        print()
        print(
            "WARNING:"
        )

        print(
            "Could not generate the requested "
            "number of background points."
        )

    # --------------------------------------------------------
    # CONVERT BACK TO WGS84
    # --------------------------------------------------------

    negative = gpd.GeoDataFrame(
        {
            "label": [
                0
            ]
            * len(background_points)
        },
        geometry=background_points,
        crs="EPSG:7755"
    )

    negative = negative.to_crs(
        "EPSG:4326"
    )

    # --------------------------------------------------------
    # CREATE LABELS
    # --------------------------------------------------------

    positive["label"] = 1

    positive = positive[
        [
            "slide_no",
            "village",
            "vlcode",
            "latitude",
            "longitude",
            "label",
            "geometry"
        ]
    ]

    negative["latitude"] = (
        negative.geometry.y
    )

    negative["longitude"] = (
        negative.geometry.x
    )

    negative["slide_no"] = ""

    negative["village"] = ""

    negative["vlcode"] = ""

    negative = negative[
        [
            "slide_no",
            "village",
            "vlcode",
            "latitude",
            "longitude",
            "label",
            "geometry"
        ]
    ]

    # --------------------------------------------------------
    # COMBINE
    # --------------------------------------------------------

    samples = pd.concat(
        [
            positive,
            negative
        ],
        ignore_index=True
    )

    samples = gpd.GeoDataFrame(
        samples,
        geometry="geometry",
        crs="EPSG:4326"
    )

    # --------------------------------------------------------
    # SAMPLE TERRAIN
    # --------------------------------------------------------

    print()
    print(
        "Extracting terrain features..."
    )

    samples["elevation"] = sample_raster(
        ELEVATION_FILE,
        list(samples.geometry)
    )

    samples["slope"] = sample_raster(
        SLOPE_FILE,
        list(samples.geometry)
    )

    samples["aspect"] = sample_raster(
        ASPECT_FILE,
        list(samples.geometry)
    )

    samples["twi"] = sample_raster(
        TWI_FILE,
        list(samples.geometry)
    )

    # --------------------------------------------------------
    # REMOVE INVALID VALUES
    # --------------------------------------------------------

    feature_columns = [
        "elevation",
        "slope",
        "aspect",
        "twi"
    ]

    before = len(samples)

    samples = samples.dropna(
        subset=feature_columns
    )

    removed = (
        before - len(samples)
    )

    # --------------------------------------------------------
    # FINAL TABLE
    # --------------------------------------------------------

    result = samples[
        [
            "latitude",
            "longitude",
            "elevation",
            "slope",
            "aspect",
            "twi",
            "label",
            "slide_no",
            "village",
            "vlcode"
        ]
    ].copy()

    result = result.sample(
        frac=1,
        random_state=RANDOM_SEED
    ).reset_index(
        drop=True
    )

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
    print("=" * 70)
    print(
        "SUSCEPTIBILITY DATASET"
    )
    print("=" * 70)

    print(
        f"Total samples: {len(result)}"
    )

    print()
    print(
        "Labels:"
    )

    print(
        result["label"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()
    print(
        f"Invalid samples removed: "
        f"{removed}"
    )

    print()
    print(
        "Feature missing values:"
    )

    print(
        result[
            feature_columns
        ]
        .isna()
        .sum()
        .to_string()
    )

    print()
    print(
        f"Saved to:\n"
        f"{OUTPUT_FILE.resolve()}"
    )

    print()
    print(
        "Feature statistics:"
    )

    print(
        result[
            feature_columns
        ]
        .describe()
        .to_string()
    )


if __name__ == "__main__":
    main()