import geopandas as gpd
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE = Path(r"C:\Users\laxmi\Documents\SIH 2026\aashray-sih26191\AI-ML")

INPUT = Path(r"C:\Users\laxmi\Documents\SIH 2026\AASHRAY\AI-ML\data\raw\administrative\village_boundary\vb_soi_kl.GeoJSON")

OUTPUT_DIR = BASE / "data/processed/administrative"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_GEOJSON = OUTPUT_DIR / "kerala_700_selected_villages.geojson"
OUTPUT_CSV = OUTPUT_DIR / "kerala_700_selected_villages.csv"


# ============================================================
# LOAD DATA
# ============================================================

print("Loading Kerala village dataset...")

g = gpd.read_file(INPUT)

g.columns = g.columns.str.strip()

print("Total records:", len(g))


# ============================================================
# CLEAN NUMERIC DATA
# ============================================================

numeric_columns = [
    "total_households",
    "total_population_village",
    "avg_household",
    "total_geographical_area",
    "total_male_population_village",
    "total_female_population_village",
    "forest_area",
    "area_under_non_agricultural_use",
    "barren_uncultivable_land",
    "permanent_pastures_grazing",
    "land_under_miscellaneous",
    "culturable_waste_land",
    "fallows_land_other_than_current",
    "current_fallows_area",
    "net_area_sown",
    "total_unirrigated_land",
    "area_irrigated_by_source",
    "canals_area",
    "wells_tube_wells_area",
    "tanks_lakes_area",
    "waterfall_area",
    "other_source_specify_area",
    "nearest_town_distance_from_village",
]


for col in numeric_columns:
    g[col] = pd.to_numeric(g[col], errors="coerce").fillna(0)


# ============================================================
# REMOVE OBVIOUS AGGREGATE / NON-VILLAGE RECORDS
# ============================================================

# Records with zero geographical area are generally urban/
# aggregate administrative records in this dataset.

before = len(g)

g = g[g["total_geographical_area"] > 0].copy()

print("Removed zero-area records:", before - len(g))
print("Candidate village records:", len(g))


# ============================================================
# CREATE DIVERSITY FEATURES
# ============================================================

features = [
    "total_population_village",
    "total_households",
    "avg_household",
    "total_geographical_area",
    "total_male_population_village",
    "total_female_population_village",
    "forest_area",
    "area_under_non_agricultural_use",
    "barren_uncultivable_land",
    "permanent_pastures_grazing",
    "land_under_miscellaneous",
    "culturable_waste_land",
    "fallows_land_other_than_current",
    "current_fallows_area",
    "net_area_sown",
    "total_unirrigated_land",
    "area_irrigated_by_source",
    "canals_area",
    "wells_tube_wells_area",
    "tanks_lakes_area",
    "waterfall_area",
    "other_source_specify_area",
    "nearest_town_distance_from_village",
]


X = g[features].copy()


# ============================================================
# LOG TRANSFORM
# ============================================================

# Reduces the dominance of extremely large population/area
# values while preserving differences between villages.

for col in features:
    X[col] = np.log1p(X[col])


# ============================================================
# STANDARDIZE
# ============================================================

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


# ============================================================
# CLUSTER VILLAGES
# ============================================================

# Many clusters allow us to capture many different village
# profiles instead of selecting one dominant village type.

N_CLUSTERS = 140

print("Creating", N_CLUSTERS, "diversity clusters...")

kmeans = KMeans(
    n_clusters=N_CLUSTERS,
    random_state=42,
    n_init=20
)

g["cluster"] = kmeans.fit_predict(X_scaled)


# ============================================================
# SELECT REPRESENTATIVE VILLAGES
# ============================================================

selected_indices = []

# First guarantee geographic representation:
# select at least one village from every district and block.

for district in sorted(g["district"].dropna().unique()):

    district_data = g[g["district"] == district]

    for block in sorted(district_data["block"].dropna().unique()):

        block_data = district_data[district_data["block"] == block]

        if len(block_data) == 0:
            continue

        # Select the village closest to the block's feature centre.

        block_indices = block_data.index.to_numpy()

        block_vectors = X_scaled[
            g.index.get_indexer(block_indices)
        ]

        centre = block_vectors.mean(axis=0)

        distances = np.linalg.norm(
            block_vectors - centre,
            axis=1
        )

        best_position = np.argmin(distances)

        selected_indices.append(block_indices[best_position])


# Remove duplicates

selected_indices = list(dict.fromkeys(selected_indices))

print("Initial district/block representatives:", len(selected_indices))


# ============================================================
# ADD CLUSTER REPRESENTATIVES
# ============================================================

for cluster_id in sorted(g["cluster"].unique()):

    cluster_data = g[g["cluster"] == cluster_id]

    cluster_indices = cluster_data.index.to_numpy()

    cluster_vectors = X_scaled[
        g.index.get_indexer(cluster_indices)
    ]

    centre = cluster_vectors.mean(axis=0)

    distances = np.linalg.norm(
        cluster_vectors - centre,
        axis=1
    )

    order = np.argsort(distances)

    for position in order:

        idx = cluster_indices[position]

        if idx not in selected_indices:
            selected_indices.append(idx)
            break


print("After cluster representatives:", len(selected_indices))


# ============================================================
# FILL REMAINING SLOTS USING MAXIMUM DIVERSITY
# ============================================================

remaining = 700 - len(selected_indices)

if remaining > 0:

    available_indices = [
        idx for idx in g.index
        if idx not in selected_indices
    ]

    selected_vectors = X_scaled[
        g.index.get_indexer(selected_indices)
    ]

    available_vectors = X_scaled[
        g.index.get_indexer(available_indices)
    ]

    # Greedy farthest-point sampling.
    #
    # Each next village is chosen because it is far from
    # villages already selected in feature space.

    min_distances = np.full(
        len(available_indices),
        np.inf
    )

    for _ in range(remaining):

        distances = np.linalg.norm(
            available_vectors -
            selected_vectors[-1],
            axis=1
        )

        min_distances = np.minimum(
            min_distances,
            distances
        )

        best_position = np.argmax(min_distances)

        selected_idx = available_indices[best_position]

        selected_indices.append(selected_idx)

        selected_vectors = np.vstack([
            selected_vectors,
            available_vectors[best_position]
        ])

        available_indices.pop(best_position)
        available_vectors = np.delete(
            available_vectors,
            best_position,
            axis=0
        )

        min_distances = np.delete(
            min_distances,
            best_position
        )


# ============================================================
# FINAL DATASET
# ============================================================

selected = g.loc[selected_indices].copy()

selected = selected.drop(columns=["cluster"], errors="ignore")


# ============================================================
# SORT FOR READABILITY
# ============================================================

selected = selected.sort_values(
    ["district", "block", "village"]
).reset_index(drop=True)


# ============================================================
# SAVE
# ============================================================

print("Final selected villages:", len(selected))

selected.to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON"
)

selected.drop(columns="geometry").to_csv(
    OUTPUT_CSV,
    index=False
)


# ============================================================
# REPORT
# ============================================================

print("\n========================================")
print("KERALA 700 VILLAGE SELECTION COMPLETE")
print("========================================")

print("Selected villages:", len(selected))
print("Districts:", selected["district"].nunique())
print("Blocks:", selected["block"].nunique())

print("\nVillages per district:")
print(
    selected["district"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nFiles created:")
print(OUTPUT_GEOJSON)
print(OUTPUT_CSV)