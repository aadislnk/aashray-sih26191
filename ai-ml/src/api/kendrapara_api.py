from pathlib import Path

import geopandas as gpd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


# ============================================================
# PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RISK_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "multi_hazard"
    / "kendrapara_multi_hazard_risk.geojson"
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="AASHRAY Kendrapara Risk API",
    description="Village-level multi-hazard disaster risk API",
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
# LOAD DATA ON STARTUP
# ============================================================

risk_data = gpd.read_file(RISK_FILE)

print(
    f"AASHRAY loaded {len(risk_data)} Kendrapara villages"
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():

    return {
        "project": "AASHRAY",
        "region": "Kendrapara, Odisha",
        "status": "online",
        "villages": len(risk_data),
    }


# ============================================================
# ALL VILLAGES
# ============================================================

@app.get("/api/villages")
def get_villages():

    result = []

    for _, row in risk_data.iterrows():

        result.append(
            {
                "village": row["village"],
                "vlcode": row["vlcode"],
                "risk_score": float(
                    row["multi_hazard_score"]
                ),
                "risk_category": row[
                    "multi_hazard_category"
                ],
            }
        )

    return {
        "count": len(result),
        "villages": result,
    }


# ============================================================
# SINGLE VILLAGE
# ============================================================

@app.get("/api/village/{vlcode}")
def get_village(vlcode: str):

    matches = risk_data[
        risk_data["vlcode"].astype(str) == str(vlcode)
    ]

    if matches.empty:

        raise HTTPException(
            status_code=404,
            detail="Village not found",
        )

    row = matches.iloc[0]

    def value(column):

        if column not in row.index:
            return None

        if row[column] != row[column]:
            return None

        return float(row[column])

    return {
        "village": row["village"],
        "vlcode": row["vlcode"],
        "block": row.get("block"),
        "district": row.get("district"),

        "overall": {
            "score": value("multi_hazard_score"),
            "category": row[
                "multi_hazard_category"
            ],
        },

        "hazards": {
            "coastal": value(
                "coastal_hazard_score"
            ),
            "flood": value(
                "flood_hazard_score"
            ),
            "cyclone": value(
                "cyclone_hazard_score"
            ),
            "rainfall": value(
                "rainfall_hazard_score"
            ),
        },

        "hazards_available": int(
            row["hazards_available"]
        ),

        "hazard_contribution": row[
            "hazard_contribution"
        ],
    }


# ============================================================
# RISK STATISTICS
# ============================================================

@app.get("/api/statistics")
def get_statistics():

    categories = (
        risk_data["multi_hazard_category"]
        .value_counts()
        .to_dict()
    )

    return {
        "total_villages": len(risk_data),

        "risk_distribution": {
            key: int(value)
            for key, value in categories.items()
        },

        "mean_risk": float(
            risk_data[
                "multi_hazard_score"
            ].mean()
        ),

        "minimum_risk": float(
            risk_data[
                "multi_hazard_score"
            ].min()
        ),

        "maximum_risk": float(
            risk_data[
                "multi_hazard_score"
            ].max()
        ),
    }


# ============================================================
# TOP RISK VILLAGES
# ============================================================

@app.get("/api/top-risk")
def get_top_risk():

    top = (
        risk_data[
            [
                "village",
                "vlcode",
                "multi_hazard_score",
                "multi_hazard_category",
            ]
        ]
        .sort_values(
            "multi_hazard_score",
            ascending=False,
        )
        .head(10)
    )

    return {
        "villages": [
            {
                "village": row["village"],
                "vlcode": row["vlcode"],
                "risk_score": float(
                    row["multi_hazard_score"]
                ),
                "risk_category": row[
                    "multi_hazard_category"
                ],
            }
            for _, row in top.iterrows()
        ]
    }


# ============================================================
# GEOJSON
# ============================================================

@app.get("/api/map")
def get_map():

    return risk_data.to_json()