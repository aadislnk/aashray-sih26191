from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "rainfall"
    / "wayanad_rainfall_2024.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "rainfall"
    / "wayanad_rainfall_features_2024.csv"
)


def main():

    print("Loading rainfall data...")

    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=["date"]
    )

    df = df.sort_values("date")

    print(f"Records: {len(df)}")

    # Rolling rainfall totals
    df["rainfall_3day"] = (
        df["rainfall_mm"]
        .rolling(window=3, min_periods=1)
        .sum()
    )

    df["rainfall_7day"] = (
        df["rainfall_mm"]
        .rolling(window=7, min_periods=1)
        .sum()
    )

    df["rainfall_30day"] = (
        df["rainfall_mm"]
        .rolling(window=30, min_periods=1)
        .sum()
    )

    # Simple heavy-rainfall indicator.
    # Threshold can be refined later using IMD criteria.
    df["heavy_rainfall_day"] = (
        df["rainfall_mm"] >= 64.5
    ).astype(int)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nRainfall feature generation completed.")

    print(
        f"Saved to:\n{OUTPUT_FILE.resolve()}"
    )

    print("\nColumns:")

    print(
        df.columns.tolist()
    )

    print("\nSample:")

    print(
        df.head(10).to_string(index=False)
    )


if __name__ == "__main__":
    main()