import os
import geopandas as gpd
import numpy as np


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

INPUT_PATH = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "administrative",
    "odisha_village_boundaries",
    "vb_soi_or.GeoJSON"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "administrative"
)

OUTPUT_PATH = os.path.join(
    OUTPUT_DIR,
    "kendrapara_villages.geojson"
)


def main():

    print("=" * 70)
    print("AASHRAY KENDRAPARA VILLAGE EXTRACTION")
    print("=" * 70)

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    print("\nLoading Odisha village boundaries...")

    gdf = gpd.read_file(
        INPUT_PATH
    )

    print(
        "Total Odisha villages:",
        len(gdf)
    )

    # ------------------------------------------------------------
    # FILTER KENDRAPARA DISTRICT
    # ------------------------------------------------------------

    kendrapara = gdf[
        gdf["district"]
        .astype(str)
        .str.strip()
        .str.lower()
        == "kendrapara"
    ].copy()

    print(
        "\nKendrapara villages:",
        len(kendrapara)
    )

    if len(kendrapara) == 0:

        print(
            "\nERROR: Kendrapara district not found."
        )

        print(
            "\nAvailable districts containing 'kend':"
        )

        districts = (
            gdf["district"]
            .dropna()
            .astype(str)
            .unique()
        )

        for district in sorted(districts):

            if "kend" in district.lower():

                print(
                    " ",
                    district
                )

        raise ValueError(
            "Kendrapara district could not be extracted."
        )

    # ------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------

    kendrapara.to_file(
        OUTPUT_PATH,
        driver="GeoJSON"
    )

    print(
        "\nSaved:",
        OUTPUT_PATH
    )

    # ------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------

    print(
        "\nBlocks represented:"
    )

    for block in sorted(
        kendrapara["block"]
        .dropna()
        .astype(str)
        .unique()
    ):

        count = np.sum(
            kendrapara["block"]
            .astype(str)
            == block
        )

        print(
            f"  {block}: {count} villages"
        )

    print(
        "\nKendrapara district bounds:"
    )

    print(
        kendrapara.total_bounds
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "KENDRAPARA EXTRACTION COMPLETE"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()