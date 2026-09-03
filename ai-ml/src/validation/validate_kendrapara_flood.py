import pandas as pd
import geopandas as gpd


CSV_PATH = "data/processed/features/kendrapara_flood_hazard_features.csv"
GEOJSON_PATH = "data/processed/flood/kendrapara_flood_hazard.geojson"


def main():

    print("=" * 60)
    print("KENDRAPARA FLOOD HAZARD VALIDATION")
    print("=" * 60)

    # --------------------------------------------------------
    # Load files
    # --------------------------------------------------------

    df = pd.read_csv(CSV_PATH)
    gdf = gpd.read_file(GEOJSON_PATH)

    print(f"\nCSV rows: {len(df)}")
    print(f"GeoJSON rows: {len(gdf)}")

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required = [
        "village",
        "vlcode",
        "block",
        "district",
        "flood_hazard_category",
        "flood_hazard_score",
        "flood_occurrence_range",
        "flood_data_source",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    print("\nRequired columns:")

    if missing:
        print("FAILED")
        print("Missing:", missing)
    else:
        print("PASSED")

    # --------------------------------------------------------
    # Village checks
    # --------------------------------------------------------

    print("\nVillage checks:")

    print(
        "Missing village names:",
        df["village"].isna().sum()
    )

    print(
        "Missing village codes:",
        df["vlcode"].isna().sum()
    )

    print(
        "Duplicate village codes:",
        df["vlcode"].duplicated().sum()
    )

    # --------------------------------------------------------
    # District check
    # --------------------------------------------------------

    print("\nDistricts:")

    print(
        df["district"]
        .value_counts(dropna=False)
    )

    # --------------------------------------------------------
    # Flood category distribution
    # --------------------------------------------------------

    print("\nFlood hazard distribution:")

    print(
        df["flood_hazard_category"]
        .value_counts(dropna=False)
    )

    # --------------------------------------------------------
    # Score validation
    # --------------------------------------------------------

    valid_scores = {
        0.0,
        0.10,
        0.30,
        0.55,
        0.80,
        1.00,
    }

    actual_scores = set(
        df["flood_hazard_score"]
        .dropna()
        .round(2)
        .unique()
    )

    invalid_scores = actual_scores - valid_scores

    print("\nFlood score validation:")

    if invalid_scores:
        print("FAILED")
        print("Invalid scores:", invalid_scores)
    else:
        print("PASSED")

    # --------------------------------------------------------
    # CRS check
    # --------------------------------------------------------

    print("\nGeoJSON CRS:")

    print(gdf.crs)

    # --------------------------------------------------------
    # Geometry check
    # --------------------------------------------------------

    print("\nGeometry validation:")

    print(
        "Empty geometries:",
        gdf.geometry.is_empty.sum()
    )

    print(
        "Invalid geometries:",
        (~gdf.geometry.is_valid).sum()
    )

    # --------------------------------------------------------
    # Data coverage
    # --------------------------------------------------------

    total = len(df)

    matched = (
        df["flood_hazard_category"]
        != "NO_DATA"
    ).sum()

    no_data = (
        df["flood_hazard_category"]
        == "NO_DATA"
    ).sum()

    coverage = (
        matched / total * 100
        if total > 0
        else 0
    )

    print("\nCoverage:")

    print(f"Total villages: {total}")
    print(f"Matched flood villages: {matched}")
    print(f"No-data villages: {no_data}")
    print(f"Flood data coverage: {coverage:.2f}%")

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    if (
        len(df) == len(gdf)
        and not missing
        and df["village"].isna().sum() == 0
        and df["vlcode"].duplicated().sum() == 0
        and not invalid_scores
        and gdf.geometry.is_empty.sum() == 0
    ):

        print("\n" + "=" * 60)
        print("✓ KENDRAPARA FLOOD VALIDATION PASSED")
        print("=" * 60)

    else:

        print("\n" + "=" * 60)
        print("⚠ VALIDATION NEEDS REVIEW")
        print("=" * 60)


if __name__ == "__main__":
    main()