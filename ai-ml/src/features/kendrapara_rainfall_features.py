from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAIN_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "rainfall"
    / "imd"
    / "imd_rainfall_2024.nc"
)

VILLAGE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "administrative"
    / "kendrapara_coastal_villages.geojson"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "rainfall"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = OUTPUT_DIR / "kendrapara_rainfall_features.csv"
OUTPUT_GEOJSON = OUTPUT_DIR / "kendrapara_rainfall_features.geojson"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("KENDRAPARA RAINFALL FEATURE GENERATION")
print("=" * 70)

print("\n[1] Loading IMD rainfall data...")

ds = xr.open_dataset(RAIN_FILE)
rain = ds["RAINFALL"]

print(f"Rainfall dimensions: {dict(ds.sizes)}")
print(
    f"Date range: "
    f"{pd.Timestamp(ds.TIME.values[0]).date()} "
    f"to "
    f"{pd.Timestamp(ds.TIME.values[-1]).date()}"
)

print("\n[2] Loading Kendrapara coastal villages...")

villages = gpd.read_file(VILLAGE_FILE)

print(f"Villages loaded: {len(villages)}")
print(f"CRS: {villages.crs}")


# ============================================================
# CREATE REPRESENTATIVE POINTS
# ============================================================

print("\n[3] Calculating village representative points...")

# Use a temporary GeoDataFrame so we do not add
# a second geometry column to the final GeoDataFrame.

points = villages[
    ["village", "vlcode", "block", "district", "geometry"]
].copy()

points = points.to_crs("EPSG:4326")

points["geometry"] = points.geometry.representative_point()

points["latitude"] = points.geometry.y
points["longitude"] = points.geometry.x


# ============================================================
# EXTRACT RAINFALL
# ============================================================

print("\n[4] Extracting rainfall for each village...")

results = []

time_index = pd.to_datetime(ds.TIME.values)

for _, row in points.iterrows():

    village = row["village"]
    vlcode = row["vlcode"]
    block = row["block"]
    district = row["district"]

    lat = float(row["latitude"])
    lon = float(row["longitude"])

    try:

        # Find nearest IMD grid cell.
        village_rain = rain.sel(
            LATITUDE=lat,
            LONGITUDE=lon,
            method="nearest"
        )

        values = np.asarray(village_rain.values, dtype=float)

        values[~np.isfinite(values)] = np.nan

        if np.all(np.isnan(values)):
            raise ValueError("No valid rainfall values")

        series = pd.Series(
            values,
            index=time_index
        )

        # ----------------------------------------------------
        # Annual statistics
        # ----------------------------------------------------

        annual_total = float(series.sum(skipna=True))

        annual_mean_daily = float(series.mean(skipna=True))

        max_daily = float(series.max(skipna=True))

        rainy_days = int(
            (series >= 2.5).sum()
        )

        heavy_rain_days = int(
            (series >= 64.5).sum()
        )

        very_heavy_rain_days = int(
            (series >= 115.6).sum()
        )

        extremely_heavy_rain_days = int(
            (series >= 204.5).sum()
        )

        # ----------------------------------------------------
        # Rolling rainfall
        # ----------------------------------------------------

        rainfall_3day = series.rolling(
            3,
            min_periods=1
        ).sum()

        rainfall_7day = series.rolling(
            7,
            min_periods=1
        ).sum()

        rainfall_30day = series.rolling(
            30,
            min_periods=1
        ).sum()

        max_3day = float(
            rainfall_3day.max(skipna=True)
        )

        max_7day = float(
            rainfall_7day.max(skipna=True)
        )

        max_30day = float(
            rainfall_30day.max(skipna=True)
        )

        # ----------------------------------------------------
        # Rainfall hazard score
        # ----------------------------------------------------

        annual_score = min(
            annual_total / 2500.0,
            1.0
        )

        daily_score = min(
            max_daily / 200.0,
            1.0
        )

        three_day_score = min(
            max_3day / 400.0,
            1.0
        )

        rainfall_hazard_score = (
            0.30 * annual_score
            + 0.35 * daily_score
            + 0.35 * three_day_score
        )

        # ----------------------------------------------------
        # Category
        # ----------------------------------------------------

        if rainfall_hazard_score < 0.25:
            category = "LOW"

        elif rainfall_hazard_score < 0.50:
            category = "MODERATE"

        elif rainfall_hazard_score < 0.75:
            category = "HIGH"

        else:
            category = "VERY HIGH"

        results.append(
            {
                "village": village,
                "vlcode": vlcode,
                "block": block,
                "district": district,
                "latitude": lat,
                "longitude": lon,

                "annual_rainfall_mm": annual_total,
                "mean_daily_rainfall_mm": annual_mean_daily,
                "max_daily_rainfall_mm": max_daily,

                "rainy_days": rainy_days,
                "heavy_rain_days": heavy_rain_days,
                "very_heavy_rain_days": very_heavy_rain_days,
                "extremely_heavy_rain_days": extremely_heavy_rain_days,

                "max_3day_rainfall_mm": max_3day,
                "max_7day_rainfall_mm": max_7day,
                "max_30day_rainfall_mm": max_30day,

                "rainfall_hazard_score": rainfall_hazard_score,
                "rainfall_hazard_category": category,

                "rainfall_data_source":
                    "IMD 0.25 degree gridded daily rainfall 2024",

                "rainfall_resolution":
                    "0.25 x 0.25 degree",
            }
        )

    except Exception as e:

        results.append(
            {
                "village": village,
                "vlcode": vlcode,
                "block": block,
                "district": district,
                "latitude": lat,
                "longitude": lon,

                "annual_rainfall_mm": np.nan,
                "mean_daily_rainfall_mm": np.nan,
                "max_daily_rainfall_mm": np.nan,

                "rainy_days": np.nan,
                "heavy_rain_days": np.nan,
                "very_heavy_rain_days": np.nan,
                "extremely_heavy_rain_days": np.nan,

                "max_3day_rainfall_mm": np.nan,
                "max_7day_rainfall_mm": np.nan,
                "max_30day_rainfall_mm": np.nan,

                "rainfall_hazard_score": np.nan,
                "rainfall_hazard_category": "NO_DATA",

                "rainfall_data_source":
                    "IMD 0.25 degree gridded daily rainfall 2024",

                "rainfall_resolution":
                    "0.25 x 0.25 degree",
            }
        )


# ============================================================
# DATAFRAME
# ============================================================

print("\n[5] Creating rainfall feature table...")

df = pd.DataFrame(results)

df.to_csv(
    OUTPUT_CSV,
    index=False
)

print(f"CSV saved: {OUTPUT_CSV}")


# ============================================================
# CREATE GEOJSON
# ============================================================

print("\n[6] Creating spatial rainfall layer...")

# IMPORTANT:
# Keep ONLY the original village geometry.
# The rainfall table contains attributes only.

rainfall_gdf = villages.merge(
    df,
    on=[
        "village",
        "vlcode",
        "block",
        "district"
    ],
    how="left"
)

rainfall_gdf = gpd.GeoDataFrame(
    rainfall_gdf,
    geometry="geometry",
    crs=villages.crs
)

rainfall_gdf.to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON"
)

print(f"GeoJSON saved: {OUTPUT_GEOJSON}")


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("RAINFALL FEATURE SUMMARY")
print("=" * 70)

print(f"Total villages: {len(df)}")

print(
    f"Valid rainfall records: "
    f"{df['rainfall_hazard_score'].notna().sum()}"
)

print(
    f"Missing rainfall records: "
    f"{df['rainfall_hazard_score'].isna().sum()}"
)

print("\nRainfall hazard distribution:")

print(
    df["rainfall_hazard_category"]
    .value_counts()
    .to_string()
)

valid = df[
    df["rainfall_hazard_score"].notna()
]

if len(valid) > 0:

    print("\nRainfall statistics:")

    print(
        valid[
            [
                "annual_rainfall_mm",
                "max_daily_rainfall_mm",
                "max_3day_rainfall_mm",
                "rainfall_hazard_score",
            ]
        ]
        .describe()
        .round(3)
    )

print("\n" + "=" * 70)
print("✓ KENDRAPARA RAINFALL FEATURES GENERATED")
print("=" * 70)