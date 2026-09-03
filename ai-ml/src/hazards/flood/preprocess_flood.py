from pathlib import Path
import rasterio
from rasterio.mask import mask
import geopandas as gpd
import numpy as np


# ============================================================
# AASHRAY FLOOD DATA PREPROCESSING
# ============================================================

BASE = Path(__file__).resolve().parents[3]

FLOOD_RAW = BASE / "data" / "raw" / "flood"
FLOOD_OUT = BASE / "data" / "processed" / "flood"

# Existing pilot village boundary
BOUNDARY_CANDIDATES = [
    BASE / "data" / "processed" / "administrative" / "wayanad_pilot_villages.geojson",
    BASE / "data" / "processed" / "administrative" / "pilot_villages.geojson",
]


RETURN_PERIODS = [10, 25, 50, 100, 200, 500]


def find_raster(return_period):

    all_files = list(FLOOD_RAW.rglob("*.tif"))

    target = f"Kerala_Flood_{return_period}_yr_Historical.tif"

    exact_matches = [
        f for f in all_files
        if f.name.lower() == target.lower()
    ]

    if exact_matches:
        return exact_matches[0]

    raise FileNotFoundError(
        f"Could not find exact {return_period}-year flood raster."
    )


def find_boundary():

    for path in BOUNDARY_CANDIDATES:
        if path.exists():
            return path

    # Last-resort search
    matches = list(
        (BASE / "data").rglob("*.geojson")
    )

    for path in matches:
        name = path.name.lower()

        if "pilot" in name and "village" in name:
            return path

    return None


def inspect_raster(path):

    with rasterio.open(path) as src:

        data = src.read(1, masked=True)

        print(f"\n{'-' * 60}")
        print(f"File: {path.name}")
        print(f"CRS: {src.crs}")
        print(f"Shape: {src.shape}")
        print(f"Resolution: {src.res}")
        print(f"Bounds: {src.bounds}")
        print(f"NoData: {src.nodata}")

        valid = data.compressed()

        if len(valid) > 0:

            print(f"Valid pixels: {len(valid):,}")
            print(f"Minimum: {valid.min()}")
            print(f"Maximum: {valid.max()}")
            print(f"Mean: {valid.mean()}")

        else:

            print("WARNING: No valid pixels.")


def clip_raster(input_path, geometry, output_path):

    with rasterio.open(input_path) as src:

        clipped, transform = mask(
            src,
            geometry,
            crop=True,
            filled=True,
            nodata=src.nodata if src.nodata is not None else 0
        )

        profile = src.profile.copy()

        profile.update(
            driver="GTiff",
            height=clipped.shape[1],
            width=clipped.shape[2],
            transform=transform,
            compress="deflate",
            predictor=2
        )

        with rasterio.open(output_path, "w", **profile) as dst:

            dst.write(clipped)


def main():

    print("=" * 70)
    print("AASHRAY FLOOD DATA PREPROCESSING")
    print("=" * 70)

    FLOOD_OUT.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # FIND SIX RASTERS
    # --------------------------------------------------------

    print("\nSearching for six KSDMA flood rasters...")

    rasters = {}

    for rp in RETURN_PERIODS:

        try:

            path = find_raster(rp)

            rasters[rp] = path

            print(
                f"{rp:>3}-year -> {path.name}"
            )

        except FileNotFoundError as e:

            print(f"\nERROR: {e}")
            return

    print(
        f"\nFound {len(rasters)} / {len(RETURN_PERIODS)} rasters."
    )

    # --------------------------------------------------------
    # INSPECT
    # --------------------------------------------------------

    print("\nInspecting rasters...")

    for rp, path in rasters.items():

        print(f"\n[{rp}-YEAR]")

        inspect_raster(path)

    # --------------------------------------------------------
    # FIND PILOT BOUNDARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("LOCATING PILOT VILLAGE BOUNDARY")
    print("=" * 70)

    boundary_path = find_boundary()

    if boundary_path is None:

        print(
            "\nWARNING: Pilot village boundary was not found."
        )

        print(
            "\nFlood rasters are valid and ready."
        )

        print(
            "No clipping performed."
        )

        return

    print(
        f"\nBoundary found:\n{boundary_path}"
    )

    villages = gpd.read_file(boundary_path)

    print(
        f"\nPilot villages: {len(villages)}"
    )

    if "village" in villages.columns:

        print(
            villages["village"].to_string(index=False)
        )

    # --------------------------------------------------------
    # REPROJECT
    # --------------------------------------------------------

    reference_raster = rasters[10]

    with rasterio.open(reference_raster) as src:

        raster_crs = src.crs

    if villages.crs != raster_crs:

        print(
            f"\nReprojecting boundaries:"
            f" {villages.crs} -> {raster_crs}"
        )

        villages = villages.to_crs(raster_crs)

    # --------------------------------------------------------
    # MERGE PILOT VILLAGES
    # --------------------------------------------------------

    print("\nCreating unified pilot study area...")

    study_geometry = [
        villages.geometry.unary_union
    ]

    # --------------------------------------------------------
    # CLIP ALL SIX RASTERS
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("CLIPPING FLOOD RASTERS")
    print("=" * 70)

    for rp, input_path in rasters.items():

        output_path = (
            FLOOD_OUT /
            f"wayanad_flood_{rp}yr_historical.tif"
        )

        print(
            f"\nProcessing {rp}-year flood..."
        )

        clip_raster(
            input_path,
            study_geometry,
            output_path
        )

        print(
            f"Saved: {output_path}"
        )

    # --------------------------------------------------------
    # VERIFY OUTPUT
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("VERIFYING OUTPUTS")
    print("=" * 70)

    outputs = list(
        FLOOD_OUT.glob(
            "wayanad_flood_*yr_historical.tif"
        )
    )

    print(
        f"\nProcessed flood rasters: {len(outputs)}"
    )

    for output in sorted(outputs):

        with rasterio.open(output) as src:

            print(
                f"{output.name} "
                f"| shape={src.shape} "
                f"| CRS={src.crs}"
            )

    print("\n" + "=" * 70)
    print("FLOOD PREPROCESSING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()