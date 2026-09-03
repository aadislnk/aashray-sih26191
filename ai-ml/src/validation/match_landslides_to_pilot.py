from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

LANDSLIDES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "landslides"
    / "wayanad_landslide_inventory_full.csv"
)

VILLAGES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "administrative"
    / "wayanad_pilot_villages.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "landslides"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "pilot_landslide_inventory.geojson"
)


def main():

    print("Loading landslide inventory...")

    landslides = gpd.read_file(
        LANDSLIDES_FILE,
        driver="CSV",
        GEOM_POSSIBLE_NAMES=None,
        KEEP_GEOM_COLUMNS=False
    )

    # Create point geometry from coordinates.
    landslides = gpd.GeoDataFrame(
        landslides,
        geometry=gpd.points_from_xy(
            landslides["longitude"],
            landslides["latitude"]
        ),
        crs="EPSG:4326"
    )

    print(
        f"Landslide records: {len(landslides)}"
    )

    print("\nLoading pilot village boundaries...")

    villages = gpd.read_file(
        VILLAGES_FILE
    )

    print(
        f"Pilot villages: {len(villages)}"
    )

    # Transform landslides into the same CRS.
    landslides = landslides.to_crs(
        villages.crs
    )

    print("\nPerforming spatial join...")

    matched = gpd.sjoin(
        landslides,
        villages[
            [
                "village",
                "vlcode",
                "subdistric",
                "district",
                "geometry"
            ]
        ],
        how="inner",
        predicate="within"
    )

    # Remove spatial-join index.
    if "index_right" in matched.columns:
        matched = matched.drop(
            columns=["index_right"]
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    matched.to_file(
        OUTPUT_FILE,
        driver="GeoJSON"
    )

    print()
    print("=" * 60)
    print("PILOT LANDSLIDE SPATIAL MATCH")
    print("=" * 60)

    print(
        f"Matched landslides: {len(matched)}"
    )

    print("\nLandslides by pilot village:")

    print(
        matched[
            "village"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        f"Saved to:\n{OUTPUT_FILE.resolve()}"
    )

    print("\nSample:")

    print(
        matched[
            [
                "slide_no",
                "latitude",
                "longitude",
                "village",
                "vlcode",
                "movement_type",
                "history"
            ]
        ]
        .head(20)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()