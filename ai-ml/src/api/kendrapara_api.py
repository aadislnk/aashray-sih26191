from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pyproj import Transformer


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

SUMMARY_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "multi_hazard"
    / "kendrapara_multi_hazard_summary.csv"
)

EXPOSURE_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "kendrapara_coastal_exposure_features.csv"
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AASHRAY AI/ML API",
    description="Multi-hazard disaster risk API for Kendrapara, Odisha",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# LOAD DATA
# ============================================================

if not SUMMARY_FILE.exists():
    raise FileNotFoundError(f"Missing file: {SUMMARY_FILE}")

if not EXPOSURE_FILE.exists():
    raise FileNotFoundError(f"Missing file: {EXPOSURE_FILE}")


risk_df = pd.read_csv(SUMMARY_FILE, dtype={"vlcode": str})
exposure_df = pd.read_csv(EXPOSURE_FILE, dtype={"vlcode": str})


# Clean village codes
risk_df["vlcode"] = risk_df["vlcode"].astype(str).str.strip()
exposure_df["vlcode"] = exposure_df["vlcode"].astype(str).str.strip()


# ============================================================
# CENTROID CONVERSION
# EPSG:7755 -> EPSG:4326
# ============================================================

transformer = Transformer.from_crs(
    "EPSG:7755",
    "EPSG:4326",
    always_xy=True,
)


def convert_centroid(row):
    try:
        x = float(row["centroid_x"])
        y = float(row["centroid_y"])

        lon, lat = transformer.transform(x, y)

        return {
            "lat": lat,
            "lon": lon,
        }

    except Exception:
        return {
            "lat": None,
            "lon": None,
        }


centroids = exposure_df.apply(convert_centroid, axis=1)

exposure_df["centroid_lat"] = [
    item["lat"] for item in centroids
]

exposure_df["centroid_lon"] = [
    item["lon"] for item in centroids
]


# ============================================================
# MERGE RISK + LOCATION DATA
# ============================================================

location_columns = [
    "vlcode",
    "block",
    "district",
    "centroid_lat",
    "centroid_lon",
]

location_df = exposure_df[
    [c for c in location_columns if c in exposure_df.columns]
].drop_duplicates("vlcode")


risk_df = risk_df.merge(
    location_df,
    on="vlcode",
    how="left",
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_float(value):
    if pd.isna(value):
        return None

    try:
        return float(value)
    except Exception:
        return None


def priority_from_score(score):
    """
    UI priority mapping.

    This is NOT an official government priority.
    It converts the model score into the frontend's
    existing P1-P4 format.
    """

    if score >= 80:
        return "P1"

    if score >= 60:
        return "P2"

    if score >= 40:
        return "P3"

    return "P4"


def village_to_frontend(row):
    score = safe_float(row["multi_hazard_score"])

    if score is None:
        risk_score = None
        priority = "P4"
    else:
        risk_score = round(score * 100, 2)
        priority = priority_from_score(risk_score)

    lat = safe_float(row.get("centroid_lat"))
    lon = safe_float(row.get("centroid_lon"))

    return {
        "id": str(row["vlcode"]),
        "name": str(row["village"]),
        "vlcode": str(row["vlcode"]),

        "priority": priority,

        "risk_score": risk_score,
        "risk_category": str(row["multi_hazard_category"]),

        # Population is not available in the current dataset.
        "population": None,

        "centroid": {
            "lat": lat,
            "lon": lon,
        },

        "block": (
            None
            if pd.isna(row.get("block"))
            else str(row.get("block"))
        ),

        "district": (
            None
            if pd.isna(row.get("district"))
            else str(row.get("district"))
        ),
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "project": "AASHRAY",
        "module": "AI/ML",
        "location": "Kendrapara, Odisha",
        "status": "online",
        "villages": len(risk_df),
    }


# ============================================================
# GET ALL VILLAGES
# ============================================================

@app.get("/api/villages")
def get_villages():

    villages = []

    for _, row in risk_df.iterrows():
        villages.append(
            village_to_frontend(row)
        )

    return {
        "count": len(villages),
        "villages": villages,
    }


# ============================================================
# GET SINGLE VILLAGE
# ============================================================

@app.get("/api/village/{vlcode}")
def get_village(vlcode: str):

    vlcode = str(vlcode).strip()

    matches = risk_df[
        risk_df["vlcode"] == vlcode
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Village with vlcode {vlcode} not found",
        )

    row = matches.iloc[0]

    overall_score = safe_float(
        row["multi_hazard_score"]
    )

    overall_score_100 = (
        round(overall_score * 100, 2)
        if overall_score is not None
        else None
    )

    hazards = {
        "coastal": safe_float(
            row.get("coastal_hazard_score")
        ),
        "flood": safe_float(
            row.get("flood_hazard_score")
        ),
        "cyclone": safe_float(
            row.get("cyclone_hazard_score")
        ),
        "rainfall": safe_float(
            row.get("rainfall_hazard_score")
        ),
    }

    hazards_available = [
        name
        for name, value in hazards.items()
        if value is not None
    ]

    return {
        "id": vlcode,
        "name": str(row["village"]),
        "vlcode": vlcode,

        "block": (
            None
            if pd.isna(row.get("block"))
            else str(row.get("block"))
        ),

        "district": (
            None
            if pd.isna(row.get("district"))
            else str(row.get("district"))
        ),

        "population": None,

        "centroid": {
            "lat": safe_float(row.get("centroid_lat")),
            "lon": safe_float(row.get("centroid_lon")),
        },

        "overall": {
            "score": overall_score_100,
            "category": str(
                row["multi_hazard_category"]
            ),
            "priority": priority_from_score(
                overall_score_100
            )
            if overall_score_100 is not None
            else "P4",
        },

        "hazards": hazards,

        "hazards_available": hazards_available,

        "hazard_contribution": row.get(
            "hazard_contribution"
        ),

        "data_note": (
            "Population data is not available in the "
            "current AI/ML dataset."
        ),
    }


# ============================================================
# STATISTICS
# ============================================================

@app.get("/api/statistics")
def get_statistics():

    scores = pd.to_numeric(
        risk_df["multi_hazard_score"],
        errors="coerce",
    ).dropna()

    categories = (
        risk_df["multi_hazard_category"]
        .value_counts()
        .to_dict()
    )

    return {
        "total_villages": len(risk_df),

        "risk_distribution": categories,

        "mean_risk_score": round(
            float(scores.mean() * 100),
            2,
        ),

        "min_risk_score": round(
            float(scores.min() * 100),
            2,
        ),

        "max_risk_score": round(
            float(scores.max() * 100),
            2,
        ),
    }


# ============================================================
# TOP RISK VILLAGES
# ============================================================

@app.get("/api/top-risk")
def get_top_risk():

    top = risk_df.sort_values(
        "multi_hazard_score",
        ascending=False,
    ).head(10)

    villages = []

    for _, row in top.iterrows():
        villages.append(
            village_to_frontend(row)
        )

    return {
        "count": len(villages),
        "villages": villages,
    }


# ============================================================
# MAP GEOJSON
# ============================================================

@app.get("/api/map")
def get_map():

    features = []

    for _, row in risk_df.iterrows():

        lat = safe_float(
            row.get("centroid_lat")
        )

        lon = safe_float(
            row.get("centroid_lon")
        )

        if lat is None or lon is None:
            continue

        score = safe_float(
            row["multi_hazard_score"]
        )

        feature = {
            "type": "Feature",

            "geometry": {
                "type": "Point",
                "coordinates": [
                    lon,
                    lat,
                ],
            },

            "properties": {
                "id": str(row["vlcode"]),
                "vlcode": str(row["vlcode"]),
                "name": str(row["village"]),

                "risk_score": (
                    round(score * 100, 2)
                    if score is not None
                    else None
                ),

                "risk_category": str(
                    row["multi_hazard_category"]
                ),

                "priority": (
                    priority_from_score(score * 100)
                    if score is not None
                    else "P4"
                ),
            },
        }

        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }