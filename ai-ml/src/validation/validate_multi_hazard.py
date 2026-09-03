import os
import numpy as np
import rasterio


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

INDEX_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "multi_hazard",
    "wayanad_multi_hazard_index.tif"
)

CLASS_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "multi_hazard",
    "wayanad_multi_hazard_class.tif"
)

SUSCEPTIBILITY_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "susceptibility",
    "wayanad_pilot_susceptibility.tif"
)

FLOOD_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "flood",
    "wayanad_flood_hazard_index.tif"
)


def inspect_raster(path, name):

    print("\n" + "-" * 70)
    print(name)
    print("-" * 70)

    with rasterio.open(path) as src:

        data = src.read(1)

        print("Shape:", src.shape)
        print("CRS:", src.crs)
        print("Resolution:", src.res)
        print("Bounds:", src.bounds)
        print("NoData:", src.nodata)

        valid = np.isfinite(data)

        if src.nodata is not None:
            valid &= data != src.nodata

        values = data[valid]

        print("Valid pixels:", len(values))

        if len(values) > 0:

            print(
                f"Minimum: {np.min(values):.4f}"
            )

            print(
                f"Mean:    {np.mean(values):.4f}"
            )

            print(
                f"Maximum: {np.max(values):.4f}"
            )

        return src.shape, src.crs, src.bounds, valid


def main():

    print("=" * 70)
    print("AASHRAY MULTI-HAZARD VALIDATION")
    print("=" * 70)

    # ------------------------------------------------------------
    # CHECK INPUT RASTERS
    # ------------------------------------------------------------

    sus_shape, sus_crs, sus_bounds, sus_valid = inspect_raster(
        SUSCEPTIBILITY_PATH,
        "LANDSLIDE SUSCEPTIBILITY"
    )

    flood_shape, flood_crs, flood_bounds, flood_valid = inspect_raster(
        FLOOD_PATH,
        "FLOOD HAZARD"
    )

    # ------------------------------------------------------------
    # CHECK FINAL INDEX
    # ------------------------------------------------------------

    index_shape, index_crs, index_bounds, index_valid = inspect_raster(
        INDEX_PATH,
        "MULTI-HAZARD INDEX"
    )

    # ------------------------------------------------------------
    # CHECK FINAL CLASS
    # ------------------------------------------------------------

    class_shape, class_crs, class_bounds, class_valid = inspect_raster(
        CLASS_PATH,
        "MULTI-HAZARD CLASS"
    )

    # ------------------------------------------------------------
    # SHAPE CHECK
    # ------------------------------------------------------------

    print("\n" + "=" * 70)
    print("GRID CONSISTENCY")
    print("=" * 70)

    print(
        "Susceptibility shape:",
        sus_shape
    )

    print(
        "Flood shape:",
        flood_shape
    )

    print(
        "Multi-hazard shape:",
        index_shape
    )

    print(
        "Multi-hazard class shape:",
        class_shape
    )

    if index_shape == sus_shape:
        print(
            "✓ Multi-hazard matches susceptibility grid"
        )
    else:
        print(
            "✗ GRID MISMATCH"
        )

    # ------------------------------------------------------------
    # CRS CHECK
    # ------------------------------------------------------------

    print("\n" + "=" * 70)
    print("CRS CHECK")
    print("=" * 70)

    print(
        "Susceptibility:",
        sus_crs
    )

    print(
        "Flood:",
        flood_crs
    )

    print(
        "Multi-hazard:",
        index_crs
    )

    if (
        sus_crs == index_crs
        and flood_crs == index_crs
    ):
        print(
            "✓ CRS consistent"
        )
    else:
        print(
            "✗ CRS mismatch"
        )

    # ------------------------------------------------------------
    # BOUNDS CHECK
    # ------------------------------------------------------------

    print("\n" + "=" * 70)
    print("SPATIAL EXTENT CHECK")
    print("=" * 70)

    print(
        "Susceptibility bounds:",
        sus_bounds
    )

    print(
        "Flood bounds:",
        flood_bounds
    )

    print(
        "Multi-hazard bounds:",
        index_bounds
    )

    # ------------------------------------------------------------
    # FINAL CLASS COUNTS
    # ------------------------------------------------------------

    print("\n" + "=" * 70)
    print("FINAL MULTI-HAZARD CLASSES")
    print("=" * 70)

    with rasterio.open(CLASS_PATH) as src:

        classes = src.read(1)

    total = np.sum(
        classes > 0
    )

    class_names = {
        1: "LOW",
        2: "MODERATE",
        3: "HIGH",
        4: "VERY HIGH"
    }

    for class_id, name in class_names.items():

        count = np.sum(
            classes == class_id
        )

        percentage = (
            count / total * 100
            if total > 0
            else 0
        )

        print(
            f"{name:<10}: "
            f"{count:>8,} pixels "
            f"({percentage:6.2f}%)"
        )

    # ------------------------------------------------------------
    # FINAL RESULT
    # ------------------------------------------------------------

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)

    if (
        index_shape == sus_shape
        and sus_crs == index_crs
        and flood_crs == index_crs
        and total > 0
    ):

        print(
            "\n✓ MULTI-HAZARD RASTER PASSED BASIC VALIDATION"
        )

    else:

        print(
            "\n✗ MULTI-HAZARD RASTER NEEDS CORRECTION"
        )


if __name__ == "__main__":
    main()