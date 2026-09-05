import geopandas as gpd
import pandas as pd
from pathlib import Path

BASE = Path(r"C:\Users\laxmi\Documents\SIH 2026\aashray-sih26191\AI-ML")

GEOJSON = (
    BASE
    / "data"
    / "processed"
    / "administrative"
    / "kerala_700_selected_villages.geojson"
)

CSV = (
    BASE
    / "data"
    / "processed"
    / "administrative"
    / "kerala_700_selected_villages.csv"
)

print("Loading selected village GeoJSON...")

g = gpd.read_file(GEOJSON)

g.columns = g.columns.str.strip()

print("Villages:", len(g))

# Calculate centroid in the source CRS first.
centroids = g.geometry.centroid

# Transform centroid coordinates to WGS84.
centroid_gdf = gpd.GeoSeries(
    centroids,
    crs=g.crs
).to_crs("EPSG:4326")

g["latitude"] = centroid_gdf.y
g["longitude"] = centroid_gdf.x

# Load existing CSV.
df = pd.read_csv(CSV)

df.columns = df.columns.str.strip()

# Match using village code.
coordinates = g[
    ["vlcode", "latitude", "longitude"]
].copy()

coordinates["vlcode"] = coordinates["vlcode"].astype(str).str.strip()
df["vlcode"] = df["vlcode"].astype(str).str.strip()

df = df.drop(
    columns=["latitude", "longitude"],
    errors="ignore"
)

df = df.merge(
    coordinates,
    on="vlcode",
    how="left"
)

df.to_csv(
    CSV,
    index=False
)

print("Coordinates added.")
print("Latitude missing:", df["latitude"].isna().sum())
print("Longitude missing:", df["longitude"].isna().sum())
print("Final records:", len(df))
print("CSV updated:")
print(CSV)