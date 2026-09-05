from pathlib import Path
import pandas as pd
import geopandas as gpd

BASE = Path(__file__).resolve().parents[2]

ODISHA_HAZARD = (
    BASE
    / "data"
    / "processed"
    / "multi_hazard"
    / "kendrapara_multi_hazard_summary.csv"
)

ODISHA_ADMIN = Path(
    r"C:\Users\laxmi\Documents\SIH 2026\AASHRAY\AI-ML\data\processed\administrative\kendrapara_villages.geojson"
)

KERALA_DATA = (
    BASE
    / "data"
    / "processed"
    / "administrative"
    / "kerala_700_selected_villages.csv"
)

OUTPUT_DIR = BASE / "data" / "processed" / "combined"
OUTPUT = OUTPUT_DIR / "aashray_1508_villages.csv"


def clean_columns(df):
    df.columns = df.columns.astype(str).str.strip()
    return df


def main():
    print("Loading Odisha hazard data...")
    odisha_hazard = pd.read_csv(ODISHA_HAZARD)
    odisha_hazard = clean_columns(odisha_hazard)

    print("Loading Odisha administrative data...")
    odisha_admin = gpd.read_file(ODISHA_ADMIN)
    odisha_admin = clean_columns(odisha_admin)

    # Keep only the administrative fields needed by the API.
    admin_columns = [
        "vlcode",
        "village",
        "block",
        "district",
        "total_population_village",
        "total_households",
        "total_geographical_area",
        "forest_area",
        "net_area_sown",
        "total_unirrigated_land",
        "area_irrigated_by_source",
        "nearest_town_distance_from_village",
        "geometry",
    ]

    available_admin_columns = [
        c for c in admin_columns if c in odisha_admin.columns
    ]

    odisha_admin = odisha_admin[available_admin_columns].copy()

    odisha_admin["vlcode"] = (
        odisha_admin["vlcode"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )

    odisha_hazard["vlcode"] = (
        odisha_hazard["vlcode"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )

    # Use administrative village name as the primary Odisha village name.
    odisha_admin = odisha_admin.drop_duplicates("vlcode")

    odisha = odisha_hazard.merge(
        odisha_admin,
        on="vlcode",
        how="left",
        suffixes=("", "_admin"),
    )

    # Prefer administrative values where available.
    if "village_admin" in odisha.columns:
        odisha["village"] = odisha["village_admin"].fillna(odisha["village"])

    # Odisha state information.
    odisha["state"] = "Odisha"

    # Population field expected by the API.
    odisha["population"] = pd.to_numeric(
        odisha.get("total_population_village"),
        errors="coerce",
    )

    # Calculate real village centroids from the administrative polygons.
    admin_geo = gpd.read_file(ODISHA_ADMIN)
    admin_geo = clean_columns(admin_geo)

    admin_geo["vlcode"] = (
        admin_geo["vlcode"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )

    admin_geo = admin_geo.drop_duplicates("vlcode")

    centroids = admin_geo[["vlcode", "geometry"]].copy()

    # Reproject before centroid calculation for better geometric accuracy.
    if centroids.crs is not None:
        centroid_projected = centroids.to_crs("EPSG:7755")
        centroid_projected["geometry"] = centroid_projected.geometry.centroid
        centroid_wgs84 = centroid_projected.to_crs("EPSG:4326")
    else:
        centroid_wgs84 = centroids

    centroid_df = pd.DataFrame({
        "vlcode": centroid_wgs84["vlcode"],
        "longitude": centroid_wgs84.geometry.x,
        "latitude": centroid_wgs84.geometry.y,
    })

    odisha = odisha.drop(
        columns=["latitude", "longitude"],
        errors="ignore",
    )

    odisha = odisha.merge(
        centroid_df,
        on="vlcode",
        how="left",
    )

    # Remove geometry before writing CSV.
    odisha = odisha.drop(columns=["geometry"], errors="ignore")

    # Keep the Kerala 700 records exactly as selected.
    print("Loading Kerala 700 villages...")
    kerala = pd.read_csv(KERALA_DATA)
    kerala = clean_columns(kerala)

    kerala["state"] = "Kerala"

    if "population" not in kerala.columns:
        kerala["population"] = pd.to_numeric(
            kerala["total_population_village"],
            errors="coerce",
        )

    # Kerala already has coordinates from the previous step.
    # Hazard values remain missing because we have not fabricated them.
    for column in [
        "coastal_hazard_score",
        "flood_hazard_score",
        "cyclone_hazard_score",
        "rainfall_hazard_score",
        "multi_hazard_score",
        "multi_hazard_category",
        "hazards_available",
        "hazard_contribution",
    ]:
        if column not in kerala.columns:
            kerala[column] = pd.NA

    # Ensure both datasets have the same final schema.
    final_columns = [
        "village",
        "vlcode",
        "state",
        "district",
        "block",
        "population",
        "total_population_village",
        "total_households",
        "total_geographical_area",
        "latitude",
        "longitude",
        "coastal_hazard_score",
        "flood_hazard_score",
        "cyclone_hazard_score",
        "rainfall_hazard_score",
        "multi_hazard_score",
        "multi_hazard_category",
        "hazards_available",
        "hazard_contribution",
        "forest_area",
        "net_area_sown",
        "total_unirrigated_land",
        "area_irrigated_by_source",
        "nearest_town_distance_from_village",
    ]

    for column in final_columns:
        if column not in odisha.columns:
            odisha[column] = pd.NA

        if column not in kerala.columns:
            kerala[column] = pd.NA

    odisha = odisha[final_columns]
    kerala = kerala[final_columns]

    combined = pd.concat(
        [odisha, kerala],
        ignore_index=True,
    )

    combined["vlcode"] = (
        combined["vlcode"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUTPUT, index=False)

    print()
    print("COMBINED DATASET CREATED")
    print("-------------------------")
    print("TOTAL:", len(combined))
    print("ODISHA:", (combined["state"] == "Odisha").sum())
    print("KERALA:", (combined["state"] == "Kerala").sum())
    print(
        "ODISHA POPULATION AVAILABLE:",
        combined.loc[
            combined["state"] == "Odisha",
            "population"
        ].notna().sum(),
    )
    print(
        "ODISHA COORDINATES AVAILABLE:",
        combined.loc[
            combined["state"] == "Odisha",
            ["latitude", "longitude"]
        ].notna().all(axis=1).sum(),
    )
    print(
        "DUPLICATE CODES:",
        combined["vlcode"].duplicated().sum(),
    )
    print()
    print("OUTPUT:", OUTPUT)


if __name__ == "__main__":
    main()