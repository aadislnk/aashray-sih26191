from pathlib import Path

import pandas as pd

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


# ============================================================
# AASHRAY UNIFIED AI/ML API
# Kerala 700 + Odisha 808 = 1508 villages
# ============================================================

app = FastAPI(
    title="AASHRAY AI/ML API",
    description=(
        "AASHRAY Multi-State Disaster Intelligence API "
        "for Kerala and Odisha"
    ),
    version="4.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parents[2]

DATA_FILE = (
    BASE
    / "data"
    / "processed"
    / "combined"
    / "aashray_1508_villages.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Combined dataset not found: {DATA_FILE}"
    )


df = pd.read_csv(DATA_FILE)

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)


# ============================================================
# CLEAN NUMERIC COLUMNS
# ============================================================

NUMERIC_COLUMNS = [
    "population",
    "total_population_village",
    "total_households",
    "total_geographical_area",
    "forest_area",
    "net_area_sown",
    "total_unirrigated_land",
    "area_irrigated_by_source",
    "nearest_town_distance_from_village",
    "latitude",
    "longitude",
    "aashray_risk_score",
    "coastal_hazard_score",
    "flood_hazard_score",
    "cyclone_hazard_score",
    "rainfall_hazard_score",
    "multi_hazard_score",
]


for column in NUMERIC_COLUMNS:

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


# ============================================================
# HELPERS
# ============================================================

def safe_number(value):

    if pd.isna(value):
        return None

    try:
        return float(value)

    except Exception:
        return None


def clean_text(value):

    if pd.isna(value):
        return ""

    return str(value).strip()


def get_coordinates(row):

    latitude = safe_number(
        row.get("latitude")
    )

    longitude = safe_number(
        row.get("longitude")
    )

    return {
        "lat": latitude,
        "lon": longitude,
    }


def get_risk_score(row):

    # Kerala:
    # aashray_risk_score already exists.

    aashray_score = safe_number(
        row.get("aashray_risk_score")
    )

    if aashray_score is not None:
        return round(
            aashray_score,
            2
        )

    # Odisha:
    # multi_hazard_score is 0-1.
    # Convert to common 0-100 scale.

    multi_hazard = safe_number(
        row.get("multi_hazard_score")
    )

    if multi_hazard is not None:

        return round(
            multi_hazard * 100,
            2
        )

    return None


def get_priority(row):

    existing_priority = clean_text(
        row.get("priority")
    )

    if existing_priority in {
        "P1",
        "P2",
        "P3",
        "P4",
    }:

        return existing_priority

    score = get_risk_score(row)

    if score is None:
        return "DATA-ONLY"

    if score >= 75:
        return "P1"

    if score >= 50:
        return "P2"

    if score >= 25:
        return "P3"

    return "P4"


def get_risk_category(row):

    existing_category = clean_text(
        row.get("multi_hazard_category")
    )

    if existing_category:
        return existing_category

    score = get_risk_score(row)

    if score is None:
        return "DATA-ONLY"

    if score >= 75:
        return "VERY HIGH"

    if score >= 50:
        return "HIGH"

    if score >= 25:
        return "MODERATE"

    return "LOW"


def get_hazards(row):

    hazards = {}

    mapping = {
        "coastal": "coastal_hazard_score",
        "flood": "flood_hazard_score",
        "cyclone": "cyclone_hazard_score",
        "rainfall": "rainfall_hazard_score",
    }

    for hazard_name, column in mapping.items():

        value = safe_number(
            row.get(column)
        )

        if value is not None:
            hazards[hazard_name] = round(
                value,
                4
            )

    return hazards


def calculate_profile(row):

    population = (
        safe_number(
            row.get("population")
        )
        or safe_number(
            row.get(
                "total_population_village"
            )
        )
        or 0
    )

    area = (
        safe_number(
            row.get(
                "total_geographical_area"
            )
        )
        or 0
    )

    forest = (
        safe_number(
            row.get("forest_area")
        )
        or 0
    )

    irrigation = (
        safe_number(
            row.get(
                "area_irrigated_by_source"
            )
        )
        or 0
    )

    distance = (
        safe_number(
            row.get(
                "nearest_town_distance_from_village"
            )
        )
        or 0
    )

    if population < 5000:

        population_class = "LOW"

    elif population < 15000:

        population_class = "MODERATE"

    elif population < 30000:

        population_class = "HIGH"

    else:

        population_class = "VERY HIGH"


    if area < 1000:

        area_class = "SMALL"

    elif area < 3000:

        area_class = "MEDIUM"

    elif area < 7000:

        area_class = "LARGE"

    else:

        area_class = "VERY LARGE"


    if forest == 0:

        forest_class = "NONE"

    elif area > 0 and forest / area < 0.25:

        forest_class = "LOW"

    elif area > 0 and forest / area < 0.50:

        forest_class = "MODERATE"

    else:

        forest_class = "HIGH"


    if irrigation == 0:

        irrigation_class = "NONE"

    elif area > 0 and irrigation / area < 0.25:

        irrigation_class = "LOW"

    elif area > 0 and irrigation / area < 0.50:

        irrigation_class = "MODERATE"

    else:

        irrigation_class = "HIGH"


    if distance == 0:

        accessibility_class = "UNKNOWN"

    elif distance <= 10:

        accessibility_class = "VERY HIGH"

    elif distance <= 25:

        accessibility_class = "HIGH"

    elif distance <= 50:

        accessibility_class = "MODERATE"

    else:

        accessibility_class = "LOW"


    return {
        "population": population,
        "population_class": population_class,
        "area": area,
        "area_class": area_class,
        "forest_area": forest,
        "forest_class": forest_class,
        "irrigation_area": irrigation,
        "irrigation_class": irrigation_class,
        "nearest_town_distance": distance,
        "accessibility_class": accessibility_class,
    }


def village_to_dict(row):

    hazards = get_hazards(
        row
    )

    risk_score = get_risk_score(
        row
    )

    priority = get_priority(
        row
    )

    risk_category = get_risk_category(
        row
    )

    profile = calculate_profile(
        row
    )

    return {

        "id": clean_text(
            row.get("vlcode")
        ),

        "name": clean_text(
            row.get("village")
        ),

        "vlcode": clean_text(
            row.get("vlcode")
        ),

        "state": clean_text(
            row.get("state")
        ),

        "district": clean_text(
            row.get("district")
        ),

        "block": clean_text(
            row.get("block")
        ),

        "priority": priority,

        "risk_score": risk_score,

        "risk_category": risk_category,

        "population": (
            profile["population"]
            if profile["population"] != 0
            else None
        ),

        "centroid": get_coordinates(
            row
        ),

        "hazards": hazards,

        "hazards_available": list(
            hazards.keys()
        ),

        "hazard_contribution": clean_text(
            row.get(
                "hazard_contribution"
            )
        ),

        "profiles": {

            "population":
                profile[
                    "population_class"
                ],

            "area":
                profile[
                    "area_class"
                ],

            "forest":
                profile[
                    "forest_class"
                ],

            "irrigation":
                profile[
                    "irrigation_class"
                ],

            "accessibility":
                profile[
                    "accessibility_class"
                ],
        },

        "data_note": clean_text(
            row.get(
                "risk_model_note"
            )
        ),
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    state_counts = (
        df["state"]
        .astype(str)
        .str.strip()
        .value_counts()
    )

    return {

        "project": "AASHRAY",

        "module": "AI/ML",

        "version": "4.0.0",

        "status": "online",

        "coverage": {

            "total_villages":
                len(df),

            "odisha":
                int(
                    state_counts.get(
                        "Odisha",
                        0
                    )
                ),

            "kerala":
                int(
                    state_counts.get(
                        "Kerala",
                        0
                    )
                ),
        },

        "states": int(
            df["state"].nunique()
        ),

        "message":
            "Unified Kerala + Odisha AASHRAY village API",
    }


# ============================================================
# ALL VILLAGES
# ============================================================

@app.get("/api/villages")
def get_villages(
    state: str | None = Query(
        default=None
    )
):

    data = df.copy()

    if state:

        state_clean = (
            state
            .strip()
            .lower()
        )

        data = data[
            data["state"]
            .astype(str)
            .str.strip()
            .str.lower()
            == state_clean
        ]

    villages = [

        village_to_dict(
            row
        )

        for _, row in data.iterrows()
    ]

    return {

        "count":
            len(villages),

        "villages":
            villages,
    }


# ============================================================
# SINGLE VILLAGE
# ============================================================

@app.get("/api/village/{vlcode}")
def get_village(
    vlcode: str
):

    matches = df[
        df["vlcode"]
        .astype(str)
        .str.strip()
        ==
        str(vlcode).strip()
    ]

    if matches.empty:

        raise HTTPException(
            status_code=404,
            detail="Village not found",
        )

    row = matches.iloc[0]

    result = village_to_dict(
        row
    )


    # ========================================================
    # RAW DATA
    # ========================================================

    result["raw_data"] = {

        "total_households":
            safe_number(
                row.get(
                    "total_households"
                )
            ),

        "total_geographical_area":
            safe_number(
                row.get(
                    "total_geographical_area"
                )
            ),

        "forest_area":
            safe_number(
                row.get(
                    "forest_area"
                )
            ),

        "net_area_sown":
            safe_number(
                row.get(
                    "net_area_sown"
                )
            ),

        "total_unirrigated_land":
            safe_number(
                row.get(
                    "total_unirrigated_land"
                )
            ),

        "area_irrigated_by_source":
            safe_number(
                row.get(
                    "area_irrigated_by_source"
                )
            ),

        "nearest_town_distance":
            safe_number(
                row.get(
                    "nearest_town_distance_from_village"
                )
            ),

        "aashray_risk_score":
            get_risk_score(
                row
            ),

        "priority":
            get_priority(
                row
            ),

        "risk_model":
            clean_text(
                row.get(
                    "risk_model"
                )
            ),
    }


    result["data_note"] = clean_text(
        row.get(
            "risk_model_note"
        )
    )

    return result


# ============================================================
# STATISTICS
# ============================================================

@app.get("/api/statistics")
def statistics(
    state: str | None = Query(
        default=None
    )
):

    data = df.copy()

    if state:

        state_clean = (
            state
            .strip()
            .lower()
        )

        data = data[
            data["state"]
            .astype(str)
            .str.strip()
            .str.lower()
            ==
            state_clean
        ]


    population = pd.to_numeric(
        data["population"],
        errors="coerce"
    )

    if "total_population_village" in data:

        population = population.fillna(
            pd.to_numeric(
                data[
                    "total_population_village"
                ],
                errors="coerce"
            )
        )


    area = pd.to_numeric(
        data[
            "total_geographical_area"
        ],
        errors="coerce"
    ).fillna(0)


    forest = pd.to_numeric(
        data.get(
            "forest_area",
            pd.Series(
                0,
                index=data.index
            )
        ),
        errors="coerce"
    ).fillna(0)


    risk_scores = pd.Series(
        [
            get_risk_score(row)

            for _, row in data.iterrows()
        ],
        index=data.index,
        dtype="float64"
    )


    priorities = pd.Series(
        [
            get_priority(row)

            for _, row in data.iterrows()
        ],
        index=data.index
    )


    return {

        "total_villages":
            len(data),

        "states":
            int(
                data["state"]
                .nunique()
            ),

        "districts":
            int(
                data["district"]
                .nunique()
            ),

        "blocks":
            int(
                data["block"]
                .nunique()
            ),

        "population": {

            "total":
                float(
                    population
                    .fillna(0)
                    .sum()
                ),

            "average":
                float(
                    population.mean()
                ),

            "maximum":
                float(
                    population.max()
                ),
        },

        "area": {

            "total":
                float(
                    area.sum()
                ),

            "average":
                float(
                    area.mean()
                ),

            "maximum":
                float(
                    area.max()
                ),
        },

        "forest": {

            "total":
                float(
                    forest.sum()
                ),

            "average":
                float(
                    forest.mean()
                ),

            "maximum":
                float(
                    forest.max()
                ),
        },

        "risk": {

            "average":
                safe_number(
                    risk_scores.mean()
                ),

            "maximum":
                safe_number(
                    risk_scores.max()
                ),
        },

        "priority_distribution": {

            "P1":
                int(
                    (
                        priorities
                        == "P1"
                    ).sum()
                ),

            "P2":
                int(
                    (
                        priorities
                        == "P2"
                    ).sum()
                ),

            "P3":
                int(
                    (
                        priorities
                        == "P3"
                    ).sum()
                ),

            "P4":
                int(
                    (
                        priorities
                        == "P4"
                    ).sum()
                ),

            "DATA-ONLY":
                int(
                    (
                        priorities
                        == "DATA-ONLY"
                    ).sum()
                ),
        },
    }


# ============================================================
# TOP RISK
# ============================================================

@app.get("/api/top-risk")
def top_risk(
    state: str | None = Query(
        default=None
    )
):

    data = df.copy()

    if state:

        state_clean = (
            state
            .strip()
            .lower()
        )

        data = data[
            data["state"]
            .astype(str)
            .str.strip()
            .str.lower()
            ==
            state_clean
        ]


    data["_risk"] = [

        get_risk_score(row)

        for _, row in data.iterrows()
    ]


    data = data.dropna(
        subset=["_risk"]
    )


    data = data.sort_values(
        "_risk",
        ascending=False
    ).head(20)


    villages = [

        village_to_dict(
            row
        )

        for _, row in data.iterrows()
    ]


    return {

        "count":
            len(villages),

        "villages":
            villages,
    }


# ============================================================
# MAP DATA
# ============================================================

@app.get("/api/map")
def map_data(
    state: str | None = Query(
        default=None
    )
):

    data = df.copy()

    if state:

        state_clean = (
            state
            .strip()
            .lower()
        )

        data = data[
            data["state"]
            .astype(str)
            .str.strip()
            .str.lower()
            ==
            state_clean
        ]


    features = []


    for _, row in data.iterrows():

        coordinates = get_coordinates(
            row
        )

        latitude = coordinates["lat"]

        longitude = coordinates["lon"]


        if (
            latitude is None
            or longitude is None
        ):
            continue


        features.append({

            "type": "Feature",

            "geometry": {

                "type": "Point",

                "coordinates": [
                    longitude,
                    latitude,
                ],
            },

            "properties": {

                "id":
                    clean_text(
                        row.get(
                            "vlcode"
                        )
                    ),

                "name":
                    clean_text(
                        row.get(
                            "village"
                        )
                    ),

                "state":
                    clean_text(
                        row.get(
                            "state"
                        )
                    ),

                "district":
                    clean_text(
                        row.get(
                            "district"
                        )
                    ),

                "block":
                    clean_text(
                        row.get(
                            "block"
                        )
                    ),

                "risk_score":
                    get_risk_score(
                        row
                    ),

                "priority":
                    get_priority(
                        row
                    ),

                "risk_category":
                    get_risk_category(
                        row
                    ),
            },
        })


    return {

        "type":
            "FeatureCollection",

        "features":
            features,
    }


# ============================================================
# HEALTH / VALIDATION ENDPOINT
# ============================================================

@app.get("/api/health")
def health():

    return {

        "status": "healthy",

        "dataset":
            "aashray_1508_villages.csv",

        "villages":
            len(df),

        "states":
            int(
                df["state"]
                .nunique()
            ),

        "kerala":
            int(
                (
                    df["state"]
                    == "Kerala"
                ).sum()
            ),

        "odisha":
            int(
                (
                    df["state"]
                    == "Odisha"
                ).sum()
            ),
    }