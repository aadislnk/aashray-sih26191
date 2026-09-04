from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pyproj import Transformer


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="AASHRAY AI/ML API",
    description="AASHRAY Kerala Village Risk API",
    version="2.0.0"
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
    / "administrative"
    / "kerala_700_selected_villages.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"700 village dataset not found: {DATA_FILE}"
    )

df = pd.read_csv(DATA_FILE)

df.columns = df.columns.str.strip()


# ============================================================
# COORDINATE TRANSFORMATION
# ============================================================

# Kerala village GeoJSON uses geographic coordinates.
# Keep transformer available for future spatial processing.

transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:4326",
    always_xy=True
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


def get_coordinates(row):
    """
    CSV does not contain geometry.
    Coordinates will be populated as null unless longitude/
    latitude columns are available.
    """

    latitude_columns = [
        "latitude",
        "lat",
        "centroid_lat"
    ]

    longitude_columns = [
        "longitude",
        "lon",
        "lng",
        "centroid_lon"
    ]

    lat = None
    lon = None

    for column in latitude_columns:
        if column in row.index:
            lat = safe_number(row[column])
            if lat is not None:
                break

    for column in longitude_columns:
        if column in row.index:
            lon = safe_number(row[column])
            if lon is not None:
                break

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
    """
    Creates transparent descriptive profiles from the
    administrative dataset.

    These are NOT official government hazard classifications.
    """

    population = safe_number(
        row.get("total_population_village")
    ) or 0

    area = safe_number(
        row.get("total_geographical_area")
    ) or 0

    forest = safe_number(
        row.get("forest_area")
    ) or 0

    irrigation = safe_number(
        row.get("area_irrigated_by_source")
    ) or 0

    distance = safe_number(
        row.get("nearest_town_distance_from_village")
    ) or 0

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
        "accessibility_class": accessibility_class
    }


def village_to_dict(row):
    profile = calculate_profile(row)

    village_name = str(
        row.get("village", "")
    ).strip()

    vlcode = str(
        row.get("vlcode", "")
    ).strip()

    district = str(
        row.get("district", "")
    ).strip()

    block = str(
        row.get("block", "")
    ).strip()

    coordinates = get_coordinates(row)

    # The administrative dataset does not contain an
    # official overall hazard score.
    #
    # Therefore we do NOT fabricate one.

    return {
        "id": vlcode,
        "name": village_name,
        "vlcode": vlcode,
        "district": district,
        "block": block,
        "priority": "PENDING",
        "risk_score": None,
        "risk_category": "DATA-ONLY",
        "population": profile["population"],
        "centroid": coordinates,

        "profiles": {
            "population": profile["population_class"],
            "area": profile["area_class"],
            "forest": profile["forest_class"],
            "irrigation": profile["irrigation_class"],
            "accessibility": profile["accessibility_class"]
        }
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "project": "AASHRAY",
        "module": "AI/ML",
        "location": "Kerala",
        "status": "online",
        "villages": len(df),
        "dataset": "700 selected Kerala villages",
        "risk_note": (
            "Current dataset contains administrative and "
            "exposure attributes. Official/modelled hazard "
            "scores are not fabricated when unavailable."
        )
    }


# ============================================================
# ALL VILLAGES
# ============================================================

@app.get("/api/villages")
def get_villages():
    villages = [
        village_to_dict(row)
        for _, row in df.iterrows()
    ]

    return {
        "count": len(villages),
        "villages": villages
    }


# ============================================================
# SINGLE VILLAGE
# ============================================================

@app.get("/api/village/{vlcode}")
def get_village(vlcode: str):

    matches = df[
        df["vlcode"].astype(str).str.strip() == str(vlcode).strip()
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail="Village not found"
        )

    row = matches.iloc[0]

    profile = calculate_profile(row)

    return {
        "id": str(row["vlcode"]),
        "name": str(row["village"]).strip(),
        "vlcode": str(row["vlcode"]),
        "district": str(row["district"]).strip(),
        "block": str(row["block"]).strip(),
        "population": profile["population"],
        "centroid": get_coordinates(row),

        "overall": {
            "score": None,
            "category": "DATA-ONLY",
            "priority": "PENDING"
        },

        "hazards": {},

        "hazards_available": [],

        "hazard_contribution": "No official hazard score attached",

        "profiles": {
            "population": profile["population_class"],
            "area": profile["area_class"],
            "forest": profile["forest_class"],
            "irrigation": profile["irrigation_class"],
            "accessibility": profile["accessibility_class"]
        },

        "raw_data": {
            "total_households": safe_number(
                row.get("total_households")
            ),
            "total_geographical_area": profile["area"],
            "forest_area": profile["forest_area"],
            "net_area_sown": safe_number(
                row.get("net_area_sown")
            ),
            "total_unirrigated_land": safe_number(
                row.get("total_unirrigated_land")
            ),
            "area_irrigated_by_source": profile["irrigation_area"],
            "nearest_town_distance": profile[
                "nearest_town_distance"
            ]
        },

        "data_note": (
            "Administrative village data from the selected "
            "700-village Kerala dataset. Hazard values are "
            "not fabricated."
        )
    }


# ============================================================
# STATISTICS
# ============================================================

@app.get("/api/statistics")
def statistics():

    population = pd.to_numeric(
        df["total_population_village"],
        errors="coerce"
    ).fillna(0)

    area = pd.to_numeric(
        df["total_geographical_area"],
        errors="coerce"
    ).fillna(0)

    forest = pd.to_numeric(
        df["forest_area"],
        errors="coerce"
    ).fillna(0)

    return {
        "total_villages": len(df),
        "districts": int(df["district"].nunique()),
        "blocks": int(df["block"].nunique()),
        "population": {
            "total": float(population.sum()),
            "average": float(population.mean()),
            "maximum": float(population.max())
        },
        "area": {
            "total": float(area.sum()),
            "average": float(area.mean()),
            "maximum": float(area.max())
        },
        "forest": {
            "total": float(forest.sum()),
            "average": float(forest.mean()),
            "maximum": float(forest.max())
        }
    }


# ============================================================
# TOP RISK
# ============================================================

@app.get("/api/top-risk")
def top_risk():

    # No official hazard score is currently attached to the
    # 700-village administrative dataset.

    return {
        "count": 0,
        "villages": [],
        "message": (
            "Hazard ranking will be populated when "
            "validated hazard layers are attached."
        )
    }


# ============================================================
# MAP
# ============================================================

@app.get("/api/map")
def map_data():

    features = []

    for _, row in df.iterrows():

        coordinates = get_coordinates(row)

        if (
            coordinates["lat"] is None
            or coordinates["lon"] is None
        ):
            continue

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    coordinates["lon"],
                    coordinates["lat"]
                ]
            },
            "properties": {
                "id": str(row["vlcode"]),
                "name": str(row["village"]).strip(),
                "district": str(row["district"]).strip(),
                "block": str(row["block"]).strip()
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }