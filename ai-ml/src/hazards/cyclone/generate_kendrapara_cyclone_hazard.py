import os
import numpy as np
import pandas as pd
import geopandas as gpd


# ============================================================
# AASHRAY - KENDRAPARA CYCLONE HAZARD
# Historical IMD Best-Track Based Proxy
# ============================================================

TRACK_FILE = (
    r"data\processed\cyclone"
    r"\kendrapara_cyclone_track_points.csv"
)

VILLAGE_FILE = (
    r"data\processed\administrative"
    r"\kendrapara_coastal_villages.geojson"
)

OUTPUT_DIR = r"data\processed\cyclone"

OUTPUT_GEOJSON = os.path.join(
    OUTPUT_DIR,
    "kendrapara_cyclone_hazard.geojson"
)

OUTPUT_CSV = os.path.join(
    OUTPUT_DIR,
    "kendrapara_cyclone_hazard_summary.csv"
)


# ============================================================
# MODEL PARAMETERS
# ============================================================

# Only systems reaching Cyclonic Storm strength
# are considered.
MIN_CYCLONE_WIND_KT = 34.0

# Maximum distance at which a historical cyclone
# contributes to village hazard.
MAX_INFLUENCE_DISTANCE_KM = 200.0

# Distance decay.
# Smaller value = stronger effect of nearby tracks.
DISTANCE_SCALE_KM = 60.0

# Wind normalization.
MAX_REFERENCE_WIND_KT = 140.0


# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("AASHRAY - KENDRAPARA CYCLONE HAZARD")
print("=" * 70)
print()


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# LOAD TRACKS
# ============================================================

print("Loading IMD cyclone track data...")

tracks = pd.read_csv(
    TRACK_FILE
)

print(
    f"Track points loaded: {len(tracks):,}"
)

print(
    f"Historical events in track dataset: "
    f"{tracks['cyclone_event_id'].nunique()}"
)


# ============================================================
# CLEAN NUMERIC DATA
# ============================================================

tracks["latitude"] = pd.to_numeric(
    tracks["latitude"],
    errors="coerce"
)

tracks["longitude"] = pd.to_numeric(
    tracks["longitude"],
    errors="coerce"
)

tracks["max_wind_kt"] = pd.to_numeric(
    tracks["max_wind_kt"],
    errors="coerce"
)

tracks = tracks[
    tracks["latitude"].notna()
    & tracks["longitude"].notna()
].copy()


# ============================================================
# IMPORTANT:
# KEEP ONLY CYCLONIC STORM OR STRONGER SYSTEMS
# ============================================================

tracks = tracks[
    tracks["max_wind_kt"].fillna(0)
    >= MIN_CYCLONE_WIND_KT
].copy()

print(
    f"Track points from systems >= "
    f"{MIN_CYCLONE_WIND_KT:.0f} kt: "
    f"{len(tracks):,}"
)

print(
    f"Significant cyclone events: "
    f"{tracks['cyclone_event_id'].nunique()}"
)


# ============================================================
# TRACK GEODATAFRAME
# ============================================================

track_gdf = gpd.GeoDataFrame(
    tracks,
    geometry=gpd.points_from_xy(
        tracks["longitude"],
        tracks["latitude"]
    ),
    crs="EPSG:4326"
)


# ============================================================
# LOAD VILLAGES
# ============================================================

print()
print("Loading Kendrapara coastal villages...")

villages = gpd.read_file(
    VILLAGE_FILE
)

print(
    f"Coastal villages loaded: {len(villages):,}"
)


# ============================================================
# CHECK REQUIRED FIELDS
# ============================================================

required = [
    "village",
    "vlcode"
]

missing = [
    column
    for column in required
    if column not in villages.columns
]

if missing:

    raise ValueError(
        f"Missing required village fields: {missing}"
    )


# ============================================================
# CRS
# ============================================================

if villages.crs is None:

    villages = villages.set_crs(
        "EPSG:7755"
    )

villages = villages.to_crs(
    "EPSG:7755"
)

track_gdf = track_gdf.to_crs(
    "EPSG:7755"
)


# ============================================================
# REPRESENTATIVE POINTS
# ============================================================

village_points = villages.copy()

village_points["geometry"] = (
    village_points.geometry
    .representative_point()
)


# ============================================================
# VILLAGE-LEVEL CALCULATION
# ============================================================

print()
print("Calculating historical cyclone exposure...")
print()

results = []


for _, village in village_points.iterrows():

    village_name = village["village"]
    village_code = village["vlcode"]

    village_point = village.geometry

    # --------------------------------------------------------
    # Distance from village to every significant
    # cyclone track point
    # --------------------------------------------------------

    distances_km = (
        track_gdf.geometry
        .distance(village_point)
        / 1000.0
    )

    temp = track_gdf.copy()

    temp["distance_km"] = distances_km

    # --------------------------------------------------------
    # Keep only nearby cyclone tracks
    # --------------------------------------------------------

    nearby = temp[
        temp["distance_km"]
        <= MAX_INFLUENCE_DISTANCE_KM
    ].copy()

    if nearby.empty:

        results.append(
            {
                "village": village_name,
                "vlcode": village_code,
                "significant_cyclone_events": 0,
                "cyclones_within_50km": 0,
                "cyclones_within_100km": 0,
                "cyclones_within_200km": 0,
                "nearest_cyclone_distance_km": np.nan,
                "maximum_nearby_wind_kt": np.nan,
                "strongest_cyclone_event": "",
                "strongest_cyclone_name": "",
                "maximum_event_score": 0.0,
                "frequency_score": 0.0,
                "cyclone_hazard_score": 0.0
            }
        )

        continue

    # --------------------------------------------------------
    # Event-level calculations
    # --------------------------------------------------------

    event_scores = []

    for event_id, event in nearby.groupby(
        "cyclone_event_id"
    ):

        minimum_distance = (
            event["distance_km"].min()
        )

        maximum_wind = (
            event["max_wind_kt"].max()
        )

        if pd.isna(maximum_wind):

            maximum_wind = 0.0

        # ----------------------------------------------------
        # Intensity score
        # ----------------------------------------------------

        intensity_score = (
            maximum_wind
            / MAX_REFERENCE_WIND_KT
        )

        intensity_score = float(
            np.clip(
                intensity_score,
                0.0,
                1.0
            )
        )

        # ----------------------------------------------------
        # Distance decay
        # ----------------------------------------------------

        distance_factor = np.exp(
            -minimum_distance
            / DISTANCE_SCALE_KM
        )

        # ----------------------------------------------------
        # Event score
        # ----------------------------------------------------

        event_score = (
            intensity_score
            * distance_factor
        )

        # ----------------------------------------------------
        # Event name
        # ----------------------------------------------------

        event_name = ""

        if "cyclone_name" in event.columns:

            names = (
                event["cyclone_name"]
                .dropna()
                .astype(str)
                .str.strip()
            )

            names = names[
                ~names.isin(
                    [
                        "",
                        "None",
                        "nan",
                        "--"
                    ]
                )
            ]

            if len(names) > 0:

                event_name = names.iloc[0]

        event_scores.append(
            {
                "event_id": event_id,
                "event_name": event_name,
                "distance_km": minimum_distance,
                "max_wind_kt": maximum_wind,
                "event_score": event_score
            }
        )

    # --------------------------------------------------------
    # Sort strongest event first
    # --------------------------------------------------------

    event_scores = sorted(
        event_scores,
        key=lambda x: x["event_score"],
        reverse=True
    )

    # --------------------------------------------------------
    # Historical frequency
    #
    # More significant cyclones near a village
    # increase historical hazard.
    # --------------------------------------------------------

    event_count = len(
        event_scores
    )

    frequency_score = min(
        event_count / 8.0,
        1.0
    )

    # --------------------------------------------------------
    # Strongest event
    # --------------------------------------------------------

    strongest = event_scores[0]

    maximum_event_score = (
        strongest["event_score"]
    )

    # --------------------------------------------------------
    # Historical hazard score
    #
    # 70% strongest cyclone exposure
    # 30% historical frequency
    # --------------------------------------------------------

    hazard_score = (
        0.70
        * maximum_event_score
        +
        0.30
        * frequency_score
    )

    hazard_score = float(
        np.clip(
            hazard_score,
            0.0,
            1.0
        )
    )

    # --------------------------------------------------------
    # Distance counts
    # --------------------------------------------------------

    distances = np.array(
        [
            event["distance_km"]
            for event in event_scores
        ]
    )

    within_50 = int(
        np.sum(
            distances <= 50
        )
    )

    within_100 = int(
        np.sum(
            distances <= 100
        )
    )

    within_200 = int(
        np.sum(
            distances <= 200
        )
    )

    # --------------------------------------------------------
    # Maximum nearby wind
    # --------------------------------------------------------

    maximum_nearby_wind = max(
        event["max_wind_kt"]
        for event in event_scores
    )

    # --------------------------------------------------------
    # Store
    # --------------------------------------------------------

    results.append(
        {
            "village": village_name,
            "vlcode": village_code,
            "significant_cyclone_events": event_count,
            "cyclones_within_50km": within_50,
            "cyclones_within_100km": within_100,
            "cyclones_within_200km": within_200,
            "nearest_cyclone_distance_km": float(
                min(distances)
            ),
            "maximum_nearby_wind_kt": float(
                maximum_nearby_wind
            ),
            "strongest_cyclone_event": (
                strongest["event_id"]
            ),
            "strongest_cyclone_name": (
                strongest["event_name"]
            ),
            "maximum_event_score": (
                maximum_event_score
            ),
            "frequency_score": (
                frequency_score
            ),
            "cyclone_hazard_score": (
                hazard_score
            )
        }
    )


# ============================================================
# DATAFRAME
# ============================================================

results_df = pd.DataFrame(
    results
)


# ============================================================
# RELATIVE RISK CATEGORIES
#
# Use score distribution rather than forcing every village
# into the same fixed category.
# ============================================================

q25 = results_df[
    "cyclone_hazard_score"
].quantile(0.25)

q50 = results_df[
    "cyclone_hazard_score"
].quantile(0.50)

q75 = results_df[
    "cyclone_hazard_score"
].quantile(0.75)


def classify(score):

    if score <= q25:
        return "LOW"

    elif score <= q50:
        return "MODERATE"

    elif score <= q75:
        return "HIGH"

    else:
        return "VERY HIGH"


results_df[
    "cyclone_hazard_category"
] = (
    results_df[
        "cyclone_hazard_score"
    ]
    .apply(classify)
)


# ============================================================
# MERGE WITH VILLAGE GEOMETRY
# ============================================================

output_gdf = villages.merge(
    results_df,
    on=[
        "village",
        "vlcode"
    ],
    how="left"
)


# ============================================================
# SAVE GEOJSON
# ============================================================

output_gdf.to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON"
)


# ============================================================
# SAVE CSV
# ============================================================

results_df.to_csv(
    OUTPUT_CSV,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("CYCLONE HAZARD GENERATION COMPLETE")
print("=" * 70)
print()

print(
    f"Villages processed: "
    f"{len(results_df):,}"
)

print()

print(
    "Hazard score:"
)

print(
    f"Minimum: "
    f"{results_df['cyclone_hazard_score'].min():.4f}"
)

print(
    f"Mean: "
    f"{results_df['cyclone_hazard_score'].mean():.4f}"
)

print(
    f"Maximum: "
    f"{results_df['cyclone_hazard_score'].max():.4f}"
)

print()

print(
    "Category thresholds:"
)

print(
    f"LOW <= {q25:.4f}"
)

print(
    f"MODERATE <= {q50:.4f}"
)

print(
    f"HIGH <= {q75:.4f}"
)

print(
    f"VERY HIGH > {q75:.4f}"
)

print()

print(
    "Hazard distribution:"
)

print(
    results_df[
        "cyclone_hazard_category"
    ]
    .value_counts()
    .reindex(
        [
            "LOW",
            "MODERATE",
            "HIGH",
            "VERY HIGH"
        ],
        fill_value=0
    )
    .to_string()
)

print()

print(
    "Historical cyclone exposure:"
)

print(
    f"Villages with significant cyclones "
    f"within 50 km: "
    f"{(results_df['cyclones_within_50km'] > 0).sum():,}"
)

print(
    f"Villages with significant cyclones "
    f"within 100 km: "
    f"{(results_df['cyclones_within_100km'] > 0).sum():,}"
)

print(
    f"Villages with significant cyclones "
    f"within 200 km: "
    f"{(results_df['cyclones_within_200km'] > 0).sum():,}"
)

print()

print(
    "Top 10 cyclone hazard villages:"
)

top10 = (
    results_df
    .sort_values(
        "cyclone_hazard_score",
        ascending=False
    )
    .head(10)
)

print(
    top10[
        [
            "village",
            "cyclone_hazard_score",
            "cyclone_hazard_category",
            "significant_cyclone_events",
            "nearest_cyclone_distance_km",
            "maximum_nearby_wind_kt",
            "strongest_cyclone_name"
        ]
    ].to_string(
        index=False
    )
)

print()

print("Outputs:")
print(
    OUTPUT_GEOJSON
)

print(
    OUTPUT_CSV
)

print()
print("=" * 70)