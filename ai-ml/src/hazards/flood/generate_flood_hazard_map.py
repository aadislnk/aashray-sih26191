import os
import glob
import re
import numpy as np
import rasterio


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

FLOOD_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "flood"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "flood"
)

OUTPUT_INDEX = os.path.join(
    OUTPUT_DIR,
    "wayanad_flood_hazard_index.tif"
)

OUTPUT_CLASS = os.path.join(
    OUTPUT_DIR,
    "wayanad_flood_hazard_class.tif"
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


def main():

    print("=" * 70)
    print("AASHRAY CORRECTED FLOOD HAZARD MAP")
    print("=" * 70)

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    files = sorted(
        glob.glob(
            os.path.join(
                FLOOD_DIR,
                "wayanad_flood_*yr_historical.tif"
            )
        )
    )

    print(
        "\nFlood rasters found:",
        len(files)
    )

    if len(files) == 0:
        raise FileNotFoundError(
            "No flood rasters found."
        )

    layers = []

    reference_profile = None

    # ------------------------------------------------------------
    # LOAD FLOOD RASTERS
    # ------------------------------------------------------------

    for path in files:

        return_period = get_return_period(
            path
        )

        print(
            f"\nLoading {return_period}-year flood..."
        )

        with rasterio.open(path) as src:

            data = src.read(1).astype(
                np.float32
            )

            if reference_profile is None:
                reference_profile = src.profile.copy()

            if src.nodata is not None:

                valid = (
                    data != src.nodata
                )

            else:

                valid = np.isfinite(data)

            valid &= np.isfinite(data)

            # ----------------------------------------------------
            # Convert stored value to metres
            # ----------------------------------------------------

            data_m = np.full(
                data.shape,
                np.nan,
                dtype=np.float32
            )

            data_m[valid] = (
                data[valid] / 100.0
            )

            layers.append(
                (
                    return_period,
                    data_m
                )
            )

            print(
                "  Valid pixels:",
                np.sum(valid)
            )

            if np.any(valid):

                print(
                    f"  Flood level: "
                    f"{np.nanmin(data_m):.2f} - "
                    f"{np.nanmax(data_m):.2f} m"
                )

    # ------------------------------------------------------------
    # CREATE FLOOD HAZARD INDEX
    # ------------------------------------------------------------

    print(
        "\nCalculating flood hazard index..."
    )

    # Each return period gets progressively higher
    # importance because rarer events represent
    # more severe flood scenarios.

    weights = {
        10: 0.05,
        25: 0.10,
        50: 0.15,
        100: 0.20,
        200: 0.20,
        500: 0.30
    }

    weighted_sum = np.zeros(
        layers[0][1].shape,
        dtype=np.float32
    )

    weight_sum = np.zeros(
        layers[0][1].shape,
        dtype=np.float32
    )

    for return_period, data_m in layers:

        valid = np.isfinite(
            data_m
        )

        if return_period not in weights:
            continue

        # --------------------------------------------------------
        # Flood level normalization
        #
        # KSDMA map classes use:
        # <4 m
        # 4-8 m
        # 8-12 m
        # >12 m
        #
        # We therefore cap the normalized flood
        # level at 12 m.
        # --------------------------------------------------------

        normalized = np.clip(
            data_m / 12.0,
            0.0,
            1.0
        )

        weighted_sum[valid] += (
            normalized[valid]
            * weights[return_period]
        )

        weight_sum[valid] += (
            weights[return_period]
        )

    flood_index = np.full(
        weighted_sum.shape,
        np.nan,
        dtype=np.float32
    )

    valid = weight_sum > 0

    flood_index[valid] = (
        weighted_sum[valid]
        / weight_sum[valid]
    )

    # ------------------------------------------------------------
    # CLASSIFICATION
    # ------------------------------------------------------------

    flood_class = np.zeros(
        flood_index.shape,
        dtype=np.uint8
    )

    flood_class[
        (flood_index >= 0.0)
        & (flood_index < 0.3333)
        & np.isfinite(flood_index)
    ] = 1

    flood_class[
        (flood_index >= 0.3333)
        & (flood_index < 0.6667)
        & np.isfinite(flood_index)
    ] = 2

    flood_class[
        (flood_index >= 0.6667)
        & (flood_index < 0.8333)
        & np.isfinite(flood_index)
    ] = 3

    flood_class[
        (flood_index >= 0.8333)
        & np.isfinite(flood_index)
    ] = 4

    # ------------------------------------------------------------
    # STATISTICS
    # ------------------------------------------------------------

    valid_values = flood_index[
        np.isfinite(flood_index)
    ]

    print(
        "\nFlood hazard statistics:"
    )

    print(
        "  Valid pixels:",
        len(valid_values)
    )

    if len(valid_values) > 0:

        print(
            f"  Minimum: "
            f"{np.min(valid_values):.4f}"
        )

        print(
            f"  Mean: "
            f"{np.mean(valid_values):.4f}"
        )

        print(
            f"  Maximum: "
            f"{np.max(valid_values):.4f}"
        )

    # ------------------------------------------------------------
    # CLASS DISTRIBUTION
    # ------------------------------------------------------------

    print(
        "\nFlood hazard classes:"
    )

    class_names = {
        1: "LOW",
        2: "MODERATE",
        3: "HIGH",
        4: "VERY HIGH"
    }

    total = np.sum(
        flood_class > 0
    )

    for class_id, name in class_names.items():

        count = np.sum(
            flood_class == class_id
        )

        percentage = (
            count / total * 100
            if total > 0
            else 0
        )

        print(
            f"  {name:<10} "
            f"{count:>8,} pixels "
            f"({percentage:6.2f}%)"
        )

    # ------------------------------------------------------------
    # SAVE INDEX
    # ------------------------------------------------------------

    print(
        "\nSaving flood hazard index..."
    )

    index_profile = reference_profile.copy()

    index_profile.update(
        dtype="float32",
        count=1,
        nodata=np.nan,
        compress="deflate"
    )

    with rasterio.open(
        OUTPUT_INDEX,
        "w",
        **index_profile
    ) as dst:

        dst.write(
            flood_index.astype(
                np.float32
            ),
            1
        )

    # ------------------------------------------------------------
    # SAVE CLASS
    # ------------------------------------------------------------

    print(
        "Saving flood hazard classes..."
    )

    class_profile = reference_profile.copy()

    class_profile.update(
        dtype="uint8",
        count=1,
        nodata=0,
        compress="deflate"
    )

    with rasterio.open(
        OUTPUT_CLASS,
        "w",
        **class_profile
    ) as dst:

        dst.write(
            flood_class,
            1
        )

    print(
        "\n" + "=" * 70
    )

    print(
        "CORRECTED FLOOD HAZARD MAP COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        "\nGenerated:"
    )

    print(
        f"  {OUTPUT_INDEX}"
    )

    print(
        f"  {OUTPUT_CLASS}"
    )


if __name__ == "__main__":
    main()