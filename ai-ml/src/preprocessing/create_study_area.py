from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "administrative"
    / "wayanad_villages.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "administrative"
)

OUTPUT_FILE = OUTPUT_DIR / "wayanad_pilot_villages.geojson"


# Official Census village codes
PILOT_CODES = [
    "627337",  # Kottappadi Part
    "627338",  # Thrikkaipatta Part
    "627340",  # Vellarimala
]


def main():

    print("Loading Wayanad village layer...")

    gdf = gpd.read_file(INPUT_FILE)

    # Make sure codes are compared as strings
    gdf["vlcode"] = gdf["vlcode"].astype(str).str.strip()

    print(f"Total Wayanad villages: {len(gdf)}")

    # Select pilot villages
    pilot = gdf[gdf["vlcode"].isin(PILOT_CODES)].copy()

    print(f"Pilot villages found: {len(pilot)}")

    print("\nSelected villages:")
    print(
        pilot[
            ["village", "vlcode", "subdistric", "district"]
        ].to_string(index=False)
    )

    # Safety check
    missing = set(PILOT_CODES) - set(pilot["vlcode"])

    if missing:
        raise ValueError(
            f"Pilot village codes not found: {missing}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pilot.to_file(
        OUTPUT_FILE,
        driver="GeoJSON"
    )

    print("\nPilot study-area saved to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()