from pathlib import Path

import geopandas as gpd


# ---------------------------------------------------------
# AASHRAY - Village Boundary Preprocessing
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_BOUNDARY = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "administrative"
    / "village_boundary"
    / "vb_soi_kl.GeoJSON"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "administrative"
)

OUTPUT_FILE = OUTPUT_DIR / "wayanad_villages.geojson"


def load_boundaries():
    """Load the raw Kerala village boundary dataset."""

    print("Loading village boundary data...")

    gdf = gpd.read_file(RAW_BOUNDARY)

    # Clean column names
    gdf.columns = (
        gdf.columns
        .str.replace("\n", "", regex=False)
        .str.strip()
    )

    print(f"Total records: {len(gdf)}")
    print(f"CRS: {gdf.crs}")

    return gdf


def validate_boundaries(gdf):
    """Perform basic geometry validation."""

    print("\nChecking geometry...")

    invalid = (~gdf.geometry.is_valid).sum()
    missing = gdf.geometry.isna().sum()

    print(f"Invalid geometries: {invalid}")
    print(f"Missing geometries: {missing}")

    return gdf


def filter_wayanad(gdf):
    """Keep only villages belonging to Wayanad district."""

    print("\nFiltering Wayanad...")

    wayanad = gdf[
        gdf["district"]
        .astype(str)
        .str.strip()
        .str.lower()
        == "wayanad"
    ].copy()

    print(f"Wayanad records: {len(wayanad)}")

    return wayanad


def select_columns(gdf):
    """Keep fields required for the AASHRAY pipeline."""

    columns = [
        "village",
        "vlcode",
        "block",
        "bkcode",
        "subdistric",
        "sdcode",
        "district",
        "dtcode",
        "state",
        "stcode",
        "total_households",
        "total_population_village",
        "total_geographical_area",
        "geometry",
    ]

    return gdf[columns].copy()


def save_boundaries(gdf):
    """Save the processed Wayanad boundary layer."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    gdf.to_file(
        OUTPUT_FILE,
        driver="GeoJSON"
    )

    print("\nSaved processed layer:")
    print(OUTPUT_FILE)


def main():

    gdf = load_boundaries()

    gdf = validate_boundaries(gdf)

    gdf = filter_wayanad(gdf)

    gdf = select_columns(gdf)

    save_boundaries(gdf)

    print("\nAASHRAY boundary preprocessing completed successfully.")


if __name__ == "__main__":
    main()