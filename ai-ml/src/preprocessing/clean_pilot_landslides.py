from pathlib import Path

import geopandas as gpd
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "landslides"
    / "pilot_landslide_inventory.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "landslides"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "pilot_landslide_inventory_clean.csv"
)


def main():

    print("Loading pilot landslide inventory...")

    gdf = gpd.read_file(INPUT_FILE)

    print(
        f"Input records: {len(gdf)}"
    )

    # --------------------------------------------------------
    # CLEAN HISTORY
    # --------------------------------------------------------

    gdf["history"] = (
        gdf["history"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Convert recognizable dates.
    gdf["event_date"] = pd.to_datetime(
        gdf["history"],
        errors="coerce",
        dayfirst=True
    )

    gdf["event_year"] = (
        gdf["event_date"]
        .dt.year
        .astype("Int64")
    )

    # --------------------------------------------------------
    # CLEAN MOVEMENT TYPE
    # --------------------------------------------------------

    gdf["movement_type"] = (
        gdf["movement_type"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    gdf["movement_type"] = (
        gdf["movement_type"]
        .replace("", "Unknown")
    )

    # --------------------------------------------------------
    # SELECT FINAL ATTRIBUTES
    # --------------------------------------------------------

    columns = [
        "slide_no",
        "village",
        "vlcode",
        "latitude",
        "longitude",
        "movement_type",
        "history",
        "event_date",
        "event_year",
        "source_page",
    ]

    df = gdf[columns].copy()

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    before = len(df)

    df = df.drop_duplicates(
        subset=[
            "slide_no",
            "latitude",
            "longitude",
        ]
    )

    removed = before - len(df)

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    df = df.sort_values(
        [
            "village",
            "event_year",
            "latitude",
            "longitude",
        ],
        na_position="last"
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

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("CLEAN PILOT LANDSLIDE INVENTORY")
    print("=" * 60)

    print(
        f"Final records: {len(df)}"
    )

    print(
        f"Duplicates removed: {removed}"
    )

    print()
    print("Events by village:")

    print(
        df["village"]
        .value_counts()
        .to_string()
    )

    print()
    print("Events by year:")

    print(
        df["event_year"]
        .value_counts(dropna=False)
        .sort_index()
        .to_string()
    )

    print()
    print("Known dates:")

    print(
        df["event_date"]
        .notna()
        .sum()
    )

    print()
    print(
        f"Saved to:\n"
        f"{OUTPUT_FILE.resolve()}"
    )

    print()
    print("First 20 records:")

    print(
        df.head(20)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()