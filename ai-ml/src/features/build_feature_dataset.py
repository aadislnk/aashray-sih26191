from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TERRAIN_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "features"
    / "village_terrain_features.csv"
)

RAINFALL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "rainfall"
    / "wayanad_rainfall_features_2024.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "features"
    / "aashray_feature_dataset_2024.csv"
)


def main():

    print("Loading terrain features...")

    terrain = pd.read_csv(TERRAIN_FILE)

    print(f"Terrain villages: {len(terrain)}")

    print("\nLoading rainfall features...")

    rainfall = pd.read_csv(
        RAINFALL_FILE,
        parse_dates=["date"]
    )

    print(f"Rainfall records: {len(rainfall)}")

    # Create every combination of village × date.
    terrain["_key"] = 1
    rainfall["_key"] = 1

    df = terrain.merge(
        rainfall,
        on="_key",
        how="inner"
    )

    df = df.drop(
        columns=["_key"]
    )

    # Remove unnecessary metadata from the final AI table.
    df = df[
        [
            "date",
            "village",
            "vlcode",
            "subdistric",
            "district",
            "elevation_mean",
            "slope_mean",
            "aspect_mean",
            "twi_mean",
            "rainfall_mm",
            "rainfall_3day",
            "rainfall_7day",
            "rainfall_30day",
            "heavy_rainfall_day"
        ]
    ]

    # Sort for easier inspection.
    df = df.sort_values(
        ["date", "village"]
    ).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nAASHRAY feature dataset created successfully.")

    print(
        f"Rows: {len(df)}"
    )

    print(
        f"Columns: {len(df.columns)}"
    )

    print(
        f"Saved to:\n{OUTPUT_FILE.resolve()}"
    )

    print("\nColumns:")

    print(
        df.columns.tolist()
    )

    print("\nFirst 10 rows:")

    print(
        df.head(10).to_string(index=False)
    )


if __name__ == "__main__":
    main()