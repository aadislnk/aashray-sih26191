from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "administrative"
    / "wayanad_villages.geojson"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "administrative"

OUTPUT_IMAGE = OUTPUT_DIR / "wayanad_villages_map.png"


def main():
    print("Loading processed Wayanad boundaries...")

    gdf = gpd.read_file(INPUT_FILE)

    print(f"Villages: {len(gdf)}")
    print(f"CRS: {gdf.crs}")

    fig, ax = plt.subplots(figsize=(10, 10))

    gdf.boundary.plot(ax=ax, linewidth=0.5)

    ax.set_title("AASHRAY - Wayanad Village Boundaries")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")

    plt.tight_layout()

    plt.savefig(OUTPUT_IMAGE, dpi=200)
    plt.close()

    print("\nMap saved to:")
    print(OUTPUT_IMAGE)


if __name__ == "__main__":
    main()