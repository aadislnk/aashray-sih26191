from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="AASHRAY AI/ML API",
    description="AASHRAY Multi-State Disaster Intelligence API",
    version="3.0.0",
)

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

df.columns = df.columns.str.strip()


# ============================================================
# CLEAN DATA
# ============================================================

for column in [
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
]:
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
    lat = safe_number(
        row.get("latitude")
    )

    lon = safe_number(
        row.get("longitude")
    )

    if lat is None or lon is None:
        return {
            "lat": None,
            "lon": None
        }

    return {
        "lat": lat,
        "lon": lon
    }


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

    if distance <= 10:
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


def get_priority(score):
    if score is None:
        return "PENDING"

    if score >= 80:
        return "P1"

    if score >= 60:
        return "P2"

    if score >= 40:
        return "P3"

    return "P4"


def village_to_dict(row):
    state = clean_text(
        row.get("state")
    )

    multi_hazard = safe_number(
        row.get(
            "multi_hazard_score"
        )
    )

    profile = calculate_profile(row)

    hazards = {}

    hazard_mapping = {
        "coastal": "coastal_hazard_score",
        "flood": "flood_hazard_score",
        "cyclone": "cyclone_hazard_score",
        "rainfall": "rainfall_hazard_score",
    }

    for name, column in hazard_mapping.items():

        value = safe_number(
            row.get(column)
        )

        if value is not None:
            hazards[name] = value

    if multi_hazard is not None:
        risk_score = round(
            multi_hazard * 100,
            2
        )

        risk_category = clean_text(
            row.get(
                "multi_hazard_category"
            )
        )

        if not risk_category:
            if risk_score >= 75:
                risk_category = "VERY HIGH"
            elif risk_score >= 50:
                risk_category = "HIGH"
            elif risk_score >= 25:
                risk_category = "MODERATE"
            else:
                risk_category = "LOW"

        priority = get_priority(
            risk_score
        )

    else:
        risk_score = None
        risk_category = "DATA-ONLY"
        priority = "PENDING"

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

        "state": state,

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
                profile["population_class"],

            "area":
                profile["area_class"],

            "forest":
                profile["forest_class"],

            "irrigation":
                profile["irrigation_class"],

            "accessibility":
                profile["accessibility_class"],
        },
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "project": "AASHRAY",

        "module": "AI/ML",

        "status": "online",

        "coverage": {
            "total_villages": len(df),
            "odisha": int(
                (
                    df["state"] == "Odisha"
                ).sum()
            ),
            "kerala": int(
                (
                    df["state"] == "Kerala"
                ).sum()
            ),
        },

        "states": int(
            df["state"].nunique()
        ),

        "message":
            "Multi-state AASHRAY village API",
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
            state.strip().lower()
        )

        data = data[
            data["state"]
            .astype(str)
            .str.strip()
            .str.lower()
            == state_clean
        ]

    villages = [
        village_to_dict(row)
        for _, row in data.iterrows()
    ]

    return {
        "count": len(villages),
        "villages": villages,
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
        == str(vlcode).strip()
    ]

    if matches.empty:

        raise HTTPException(
            status_code=404,
            detail="Village not found",
        )

    row = matches.iloc[0]

    result = village_to_dict(row)

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
    }

    if result["hazards_available"]:

        result["data_note"] = (
            "Validated hazard data is available "
            "for this village."
        )

    else:

        result["data_note"] = (
            "Current record contains administrative "
            "and exposure information. Validated "
            "hazard scores are not currently attached."
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
            state.strip().lower()
        )

        data = data[
            data["state"]
            .astype(str)
            .str.strip()
            .str.lower()
            == state_clean
        ]

    population = pd.to_numeric(
        data["population"],
        errors="coerce"
    )

    population = population.fillna(
        pd.to_numeric(
            data["total_population_village"],
            errors="coerce"
        )
    )

    area = pd.to_numeric(
        data["total_geographical_area"],
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

    return {
        "total_villages": len(data),

        "states": int(
            data["state"].nunique()
        ),

        "districts": int(
            data["district"].nunique()
        ),

        "blocks": int(
            data["block"].nunique()
        ),

        "population": {
            "total": float(
                population.fillna(0).sum()
            ),

            "average": float(
                population.mean()
            ),

            "maximum": float(
                population.max()
            ),
        },

        "area": {
            "total": float(
                area.sum()
            ),

            "average": float(
                area.mean()
            ),

            "maximum": float(
                area.max()
            ),
        },

        "forest": {
            "total": float(
                forest.sum()
            ),

            "average": float(
                forest.mean()
            ),

            "maximum": float(
                forest.max()
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
            state.strip().lower()
        )

        data = data[
            data["state"]
            .astype(str)
            .str.strip()
            .str.lower()
            == state_clean
        ]

    data["risk"] = pd.to_numeric(
        data["multi_hazard_score"],
        errors="coerce"
    )

    data = data.dropna(
        subset=["risk"]
    )

    data = data.sort_values(
        "risk",
        ascending=False
    ).head(20)

    villages = [
        village_to_dict(row)
        for _, row in data.iterrows()
    ]

    return {
        "count": len(villages),
        "villages": villages,
    }


# ============================================================
# MAP
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
            state.strip().lower()
        )

        data = data[
            data["state"]
            .astype(str)
            .str.strip()
            .str.lower()
            == state_clean
        ]

    features = []

    for _, row in data.iterrows():

        coordinates = get_coordinates(
            row
        )

        lat = coordinates["lat"]
        lon = coordinates["lon"]

        if lat is None or lon is None:
            continue

        features.append({
            "type": "Feature",

            "geometry": {
                "type": "Point",

                "coordinates": [
                    lon,
                    lat,
                ],
            },

            "properties": {
                "id": clean_text(
                    row.get("vlcode")
                ),

                "name": clean_text(
                    row.get("village")
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

                "risk_score": safe_number(
                    row.get(
                        "multi_hazard_score"
                    )
                ),
            },
        })

    return {
        "type":
            "FeatureCollection",

        "features":
            features,
    }