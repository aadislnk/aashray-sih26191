from pathlib import Path

import xarray as xr
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAINFALL_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "rainfall"
    / "imd"
    / "imd_rainfall_2024.nc"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "rainfall"
)

OUTPUT_FILE = OUTPUT_DIR / "wayanad_rainfall_2024.csv"


# Center of our 3-village pilot area
PILOT_LAT = 11.54
PILOT_LON = 76.13


def main():

    print("Loading IMD rainfall data...")

    ds = xr.open_dataset(RAINFALL_FILE)

    print(f"Time points: {len(ds.TIME)}")
    print(f"Latitude points: {len(ds.LATITUDE)}")
    print(f"Longitude points: {len(ds.LONGITUDE)}")

    print("\nSelecting nearest IMD grid cell...")

    rainfall = ds["RAINFALL"].sel(
        LATITUDE=PILOT_LAT,
        LONGITUDE=PILOT_LON,
        method="nearest"
    )

    selected_lat = float(
        rainfall.LATITUDE.values
    )

    selected_lon = float(
        rainfall.LONGITUDE.values
    )

    print(f"Requested location: {PILOT_LAT}, {PILOT_LON}")

    print(
        f"Selected IMD grid cell: "
        f"{selected_lat}, {selected_lon}"
    )

    df = rainfall.to_dataframe(
        name="rainfall_mm"
    ).reset_index()

    df["date"] = pd.to_datetime(df["TIME"])

    df = df[
        ["date", "rainfall_mm"]
    ]

    # Remove missing rainfall values.
    df = df.dropna(
        subset=["rainfall_mm"]
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    ds.close()

    print("\nRainfall extraction completed.")

    print(
        f"Records: {len(df)}"
    )

    print(
        f"Saved to:\n{OUTPUT_FILE.resolve()}"
    )

    print("\nFirst 10 records:")

    print(
        df.head(10).to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()