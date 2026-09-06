from pathlib import Path
import pandas as pd
import geopandas as gpd


BASE = Path(__file__).resolve().parents[2]

# ============================================================
# INPUTS
# ============================================================

ODISHA_HAZARD = (
    BASE
    / "data"
    / "processed"
    / "multi_hazard"
    / "kendrapara_multi_hazard_summary.csv"
)

ODISHA_ADMIN = (
    BASE
    / "data"
    / "processed"
    / "administrative"
    / "kendrapara_villages.geojson"
)

KERALA_PRIORITY = (
    BASE
    / "data"
    / "processed"
    / "risk"
    / "kerala_700_priority_dataset.csv"
)

# ============================================================
# OUTPUT
# ============================================================

OUTPUT_DIR = (
    BASE
    / "data"
    / "processed"
    / "combined"
)

OUTPUT = (
    OUTPUT_DIR
    / "aashray_1508_villages.csv"
)


# ============================================================
# HELPERS
# ============================================================

def clean_columns(df):
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )
    return df


def clean_vlcode(series):
    return (
        series
        .astype(str)
        .str.replace(
            r"\.0$",
            "",
            regex=True
        )
        .str.strip()
    )


def numeric(series):
    return pd.to_numeric(
        series,
        errors="coerce"
    )


# ============================================================
# ODISHA
# ============================================================

def build_odisha():

    print("Loading Odisha hazard data...")

    hazard = pd.read_csv(
        ODISHA_HAZARD
    )

    hazard = clean_columns(hazard)

    hazard["vlcode"] = clean_vlcode(
        hazard["vlcode"]
    )

    print("Loading Odisha administrative data...")

    admin = gpd.read_file(
        ODISHA_ADMIN
    )

    admin = clean_columns(admin)

    admin["vlcode"] = clean_vlcode(
        admin["vlcode"]
    )

    admin = admin.drop_duplicates(
        "vlcode"
    )

    # --------------------------------------------------------
    # Administrative fields
    # --------------------------------------------------------

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

    available = [
        c
        for c in admin_columns
        if c in admin.columns
    ]

    admin = admin[
        available
    ].copy()

    # --------------------------------------------------------
    # Merge hazard + administrative data
    # --------------------------------------------------------

    odisha = hazard.merge(
        admin,
        on="vlcode",
        how="left",
        suffixes=(
            "",
            "_admin"
        ),
    )

    if "village_admin" in odisha.columns:
        odisha["village"] = (
            odisha["village_admin"]
            .fillna(
                odisha["village"]
            )
        )

    odisha["state"] = "Odisha"

    # --------------------------------------------------------
    # Population
    # --------------------------------------------------------

    odisha[
        "total_population_village"
    ] = numeric(
        odisha.get(
            "total_population_village"
        )
    )

    odisha["population"] = (
        odisha[
            "total_population_village"
        ]
    )

    # --------------------------------------------------------
    # Odisha risk score
    # --------------------------------------------------------

    if "multi_hazard_score" in odisha.columns:

        odisha[
            "multi_hazard_score"
        ] = numeric(
            odisha[
                "multi_hazard_score"
            ]
        )

        odisha[
            "aashray_risk_score"
        ] = (
            odisha[
                "multi_hazard_score"
            ] * 100
        )

    else:

        odisha[
            "multi_hazard_score"
        ] = pd.NA

        odisha[
            "aashray_risk_score"
        ] = pd.NA

    # --------------------------------------------------------
    # Odisha priority
    # --------------------------------------------------------

    def odisha_priority(score):

        if pd.isna(score):
            return "DATA-ONLY"

        if score >= 75:
            return "P1"

        if score >= 50:
            return "P2"

        if score >= 25:
            return "P3"

        return "P4"

    odisha[
        "priority"
    ] = odisha[
        "aashray_risk_score"
    ].apply(
        odisha_priority
    )

    def odisha_category(score):

        if pd.isna(score):
            return "DATA-ONLY"

        if score >= 75:
            return "VERY HIGH"

        if score >= 50:
            return "HIGH"

        if score >= 25:
            return "MODERATE"

        return "LOW"

    odisha[
        "risk_category"
    ] = odisha[
        "aashray_risk_score"
    ].apply(
        odisha_category
    )

    odisha[
        "risk_model"
    ] = "Kendrapara multi-hazard model"

    odisha[
        "risk_model_note"
    ] = (
        "Composite coastal, flood, cyclone and "
        "rainfall hazard model."
    )

    # --------------------------------------------------------
    # Hazard availability
    # --------------------------------------------------------

    odisha[
        "hazards_available"
    ] = (
        "coastal,flood,cyclone,rainfall"
    )

    odisha[
        "hazard_contribution"
    ] = (
        "coastal 30%; flood 25%; "
        "cyclone 25%; rainfall 20%"
    )

    # --------------------------------------------------------
    # Coordinates
    # --------------------------------------------------------

    admin_geo = gpd.read_file(
        ODISHA_ADMIN
    )

    admin_geo = clean_columns(
        admin_geo
    )

    admin_geo["vlcode"] = clean_vlcode(
        admin_geo["vlcode"]
    )

    admin_geo = admin_geo.drop_duplicates(
        "vlcode"
    )

    geometry = admin_geo[
        [
            "vlcode",
            "geometry"
        ]
    ].copy()

    if geometry.crs is not None:

        projected = geometry.to_crs(
            "EPSG:7755"
        )

        projected[
            "geometry"
        ] = projected.geometry.centroid

        geometry = projected.to_crs(
            "EPSG:4326"
        )

    centroid_df = pd.DataFrame(
        {
            "vlcode":
                geometry[
                    "vlcode"
                ],

            "longitude":
                geometry.geometry.x,

            "latitude":
                geometry.geometry.y,
        }
    )

    odisha = odisha.drop(
        columns=[
            "latitude",
            "longitude"
        ],
        errors="ignore"
    )

    odisha = odisha.merge(
        centroid_df,
        on="vlcode",
        how="left"
    )

    odisha = odisha.drop(
        columns=[
            "geometry"
        ],
        errors="ignore"
    )

    return odisha


# ============================================================
# KERALA
# ============================================================

def build_kerala():

    print(
        "Loading Kerala 700 priority villages..."
    )

    kerala = pd.read_csv(
        KERALA_PRIORITY
    )

    kerala = clean_columns(
        kerala
    )

    kerala["state"] = "Kerala"

    # --------------------------------------------------------
    # Ensure population
    # --------------------------------------------------------

    if "population" not in kerala.columns:

        kerala["population"] = numeric(
            kerala.get(
                "total_population_village"
            )
        )

    if (
        "total_population_village"
        not in kerala.columns
    ):

        kerala[
            "total_population_village"
        ] = kerala[
            "population"
        ]

    # --------------------------------------------------------
    # Preserve Kerala priority model
    # --------------------------------------------------------

    if "aashray_risk_score" not in kerala.columns:

        kerala[
            "aashray_risk_score"
        ] = numeric(
            kerala.get(
                "risk_score"
            )
        )

    if "priority" not in kerala.columns:

        def priority_from_score(score):

            if pd.isna(score):
                return "DATA-ONLY"

            if score >= 70:
                return "P1"

            if score >= 50:
                return "P2"

            if score >= 30:
                return "P3"

            return "P4"

        kerala[
            "priority"
        ] = kerala[
            "aashray_risk_score"
        ].apply(
            priority_from_score
        )

    # --------------------------------------------------------
    # Kerala risk category
    # --------------------------------------------------------

    if "risk_category" not in kerala.columns:

        def category_from_score(score):

            if pd.isna(score):
                return "DATA-ONLY"

            if score >= 70:
                return "VERY HIGH"

            if score >= 50:
                return "HIGH"

            if score >= 30:
                return "MODERATE"

            return "LOW"

        kerala[
            "risk_category"
        ] = kerala[
            "aashray_risk_score"
        ].apply(
            category_from_score
        )

    # --------------------------------------------------------
    # Kerala model metadata
    # --------------------------------------------------------

    if "risk_model" not in kerala.columns:

        kerala[
            "risk_model"
        ] = (
            "Kerala vulnerability and "
            "exposure priority model"
        )

    if "risk_model_note" not in kerala.columns:

        kerala[
            "risk_model_note"
        ] = (
            "Population, household pressure, "
            "water-service, drainage, accessibility "
            "and land/environment exposure model."
        )

    # Kerala does NOT have fabricated hazard values.
    for column in [
        "coastal_hazard_score",
        "flood_hazard_score",
        "cyclone_hazard_score",
        "rainfall_hazard_score",
        "multi_hazard_score",
        "multi_hazard_category",
        "hazard_contribution",
    ]:

        if column not in kerala.columns:
            kerala[column] = pd.NA

    if "hazards_available" not in kerala.columns:

        kerala[
            "hazards_available"
        ] = "vulnerability,exposure"

    return kerala


# ============================================================
# MAIN
# ============================================================

def main():

    odisha = build_odisha()

    kerala = build_kerala()

    # --------------------------------------------------------
    # Common schema
    # --------------------------------------------------------

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

        "aashray_risk_score",
        "priority",
        "risk_category",

        "risk_model",
        "risk_model_note",

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

    odisha = odisha[
        final_columns
    ]

    kerala = kerala[
        final_columns
    ]

    combined = pd.concat(
        [
            odisha,
            kerala
        ],
        ignore_index=True
    )

    combined["vlcode"] = clean_vlcode(
        combined["vlcode"]
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    print()
    print(
        "COMBINED DATASET CREATED"
    )
    print(
        "-------------------------"
    )

    print(
        "TOTAL:",
        len(combined)
    )

    print(
        "ODISHA:",
        (
            combined["state"]
            == "Odisha"
        ).sum()
    )

    print(
        "KERALA:",
        (
            combined["state"]
            == "Kerala"
        ).sum()
    )

    print()

    print(
        "PRIORITY COUNTS:"
    )

    print(
        combined[
            "priority"
        ].value_counts()
        .sort_index()
    )

    print()

    print(
        "ODISHA POPULATION AVAILABLE:",
        combined.loc[
            combined["state"]
            == "Odisha",
            "population"
        ].notna().sum()
    )

    print(
        "KERALA POPULATION AVAILABLE:",
        combined.loc[
            combined["state"]
            == "Kerala",
            "population"
        ].notna().sum()
    )

    print(
        "COORDINATES AVAILABLE:",
        combined[
            [
                "latitude",
                "longitude"
            ]
        ]
        .notna()
        .all(axis=1)
        .sum()
    )

    print(
        "DUPLICATE CODES:",
        combined[
            "vlcode"
        ].duplicated().sum()
    )

    print()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    combined.to_csv(
        OUTPUT,
        index=False
    )

    print(
        "OUTPUT:",
        OUTPUT
    )


if __name__ == "__main__":
    main()