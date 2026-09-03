from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "multi_hazard"
    / "kendrapara_multi_hazard_risk.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "maps"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "kendrapara_multi_hazard_risk_map.png"
)


# ============================================================
# LOAD
# ============================================================

print("=" * 70)
print("KENDRAPARA MULTI-HAZARD RISK MAP")
print("=" * 70)

print("\n[1] Loading validated multi-hazard layer...")

gdf = gpd.read_file(INPUT_FILE)

print(f"Villages: {len(gdf)}")
print(f"CRS: {gdf.crs}")


# ============================================================
# VALIDATION
# ============================================================

print("\n[2] Preparing risk categories...")

category_order = [
    "LOW",
    "MODERATE",
    "HIGH",
    "VERY HIGH",
]

gdf["multi_hazard_category"] = gdf[
    "multi_hazard_category"
].astype(str)

print(
    gdf["multi_hazard_category"]
    .value_counts()
    .to_string()
)


# ============================================================
# MAP
# ============================================================

print("\n[3] Generating map...")

fig, ax = plt.subplots(
    figsize=(14, 12)
)

gdf.plot(
    ax=ax,
    column="multi_hazard_category",
    categorical=True,
    legend=True,
    linewidth=0.15,
    edgecolor="black",
)

ax.set_title(
    "AASHRAY — Kendrapara Multi-Hazard Risk Map\n"
    "Coastal + Flood + Cyclone + Rainfall",
    fontsize=16,
    pad=15,
)

ax.set_xlabel("Easting")
ax.set_ylabel("Northing")

ax.grid(
    True,
    linestyle="--",
    linewidth=0.4,
    alpha=0.4,
)

plt.tight_layout()


# ============================================================
# SAVE
# ============================================================

print("\n[4] Saving map...")

plt.savefig(
    OUTPUT_FILE,
    dpi=300,
    bbox_inches="tight",
)

plt.close()

print(f"Map saved: {OUTPUT_FILE}")


# ============================================================
# TOP VILLAGES
# ============================================================

print("\n[5] Highest-risk villages:")

top10 = (
    gdf[
        [
            "village",
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

print(
    top10.to_string(index=False)
)


print("\n" + "=" * 70)
print("✓ KENDRAPARA RISK MAP GENERATED")
print("=" * 70)