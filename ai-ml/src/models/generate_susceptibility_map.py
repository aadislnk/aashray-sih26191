from pathlib import Path

import joblib
import numpy as np
import rasterio


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_FILE = (
    PROJECT_ROOT
    / "models"
    / "aashray_susceptibility_rf.joblib"
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

VILLAGE_MASK_FILE = (
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
    / "susceptibility"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "wayanad_pilot_susceptibility.tif"
)

CLASS_FILE = (
    OUTPUT_DIR
    / "wayanad_pilot_susceptibility_class.tif"
)


FEATURES = [
    "elevation",
    "slope",
    "aspect",
    "twi",
]


def load_raster(path):

    with rasterio.open(path) as src:

        data = src.read(
            1
        ).astype(
            "float32"
        )

        profile = src.profile.copy()

        transform = src.transform

        crs = src.crs

        nodata = src.nodata

    return (
        data,
        profile,
        transform,
        crs,
        nodata,
    )


def main():

    print()
    print("=" * 70)
    print("AASHRAY SUSCEPTIBILITY MAP")
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD MODEL
    # --------------------------------------------------------

    print()
    print("Loading Random Forest model...")

    model = joblib.load(
        MODEL_FILE
    )

    print(
        "Model loaded."
    )

    # --------------------------------------------------------
    # LOAD TERRAIN
    # --------------------------------------------------------

    print()
    print("Loading terrain rasters...")

    elevation, profile, transform, crs, _ = (
        load_raster(
            ELEVATION_FILE
        )
    )

    slope, _, _, _, _ = (
        load_raster(
            SLOPE_FILE
        )
    )

    aspect, _, _, _, _ = (
        load_raster(
            ASPECT_FILE
        )
    )

    twi, _, _, _, _ = (
        load_raster(
            TWI_FILE
        )
    )

    print(
        f"Raster shape: "
        f"{elevation.shape}"
    )

    # --------------------------------------------------------
    # CREATE VALID MASK
    # --------------------------------------------------------

    valid = (
        np.isfinite(elevation)
        &
        np.isfinite(slope)
        &
        np.isfinite(aspect)
        &
        np.isfinite(twi)
    )

    print(
        f"Valid pixels: "
        f"{valid.sum():,}"
    )

    # --------------------------------------------------------
    # CREATE FEATURE MATRIX
    # --------------------------------------------------------

    X = np.column_stack(
        [
            elevation[valid],
            slope[valid],
            aspect[valid],
            twi[valid],
        ]
    )

    print(
        f"Feature matrix: "
        f"{X.shape}"
    )

    # --------------------------------------------------------
    # PREDICT
    # --------------------------------------------------------

    print()
    print(
        "Generating susceptibility probabilities..."
    )

    probability = model.predict_proba(
        X
    )[:, 1]

    # --------------------------------------------------------
    # CREATE OUTPUT RASTER
    # --------------------------------------------------------

    susceptibility = np.full(
        elevation.shape,
        -9999.0,
        dtype="float32"
    )

    susceptibility[
        valid
    ] = probability.astype(
        "float32"
    )

    # --------------------------------------------------------
    # SAVE PROBABILITY MAP
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_profile = profile.copy()

    output_profile.update(
        dtype="float32",
        count=1,
        nodata=-9999.0,
        compress="lzw"
    )

    with rasterio.open(
        OUTPUT_FILE,
        "w",
        **output_profile
    ) as dst:

        dst.write(
            susceptibility,
            1
        )

    # --------------------------------------------------------
    # CLASSIFY
    # --------------------------------------------------------

    print()
    print(
        "Classifying susceptibility..."
    )

    classes = np.full(
        elevation.shape,
        0,
        dtype="uint8"
    )

    # 0 = NoData
    # 1 = Low
    # 2 = Moderate
    # 3 = High
    # 4 = Very High

    classes[
        valid
        &
        (susceptibility < 0.25)
    ] = 1

    classes[
        valid
        &
        (susceptibility >= 0.25)
        &
        (susceptibility < 0.50)
    ] = 2

    classes[
        valid
        &
        (susceptibility >= 0.50)
        &
        (susceptibility < 0.75)
    ] = 3

    classes[
        valid
        &
        (susceptibility >= 0.75)
    ] = 4

    class_profile = profile.copy()

    class_profile.update(
        dtype="uint8",
        count=1,
        nodata=0,
        compress="lzw"
    )

    with rasterio.open(
        CLASS_FILE,
        "w",
        **class_profile
    ) as dst:

        dst.write(
            classes,
            1
        )

    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    valid_probability = (
        susceptibility[
            valid
        ]
    )

    print()
    print("=" * 70)
    print("SUSCEPTIBILITY STATISTICS")
    print("=" * 70)

    print()
    print(
        f"Minimum probability: "
        f"{valid_probability.min():.4f}"
    )

    print(
        f"Mean probability: "
        f"{valid_probability.mean():.4f}"
    )

    print(
        f"Maximum probability: "
        f"{valid_probability.max():.4f}"
    )

    print()
    print("Pixel classes:")

    for class_id, name in [
        (1, "LOW"),
        (2, "MODERATE"),
        (3, "HIGH"),
        (4, "VERY HIGH"),
    ]:

        count = np.sum(
            classes == class_id
        )

        percentage = (
            count
            /
            valid.sum()
            *
            100
        )

        print(
            f"{name:10s}: "
            f"{count:,} pixels "
            f"({percentage:.2f}%)"
        )

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    print()
    print(
        f"Probability map:\n"
        f"{OUTPUT_FILE.resolve()}"
    )

    print()
    print(
        f"Class map:\n"
        f"{CLASS_FILE.resolve()}"
    )

    print()
    print("=" * 70)
    print(
        "SUSCEPTIBILITY MAP COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()