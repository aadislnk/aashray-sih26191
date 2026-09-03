import geopandas as gpd
import rasterio
from rasterio.mask import mask
from pathlib import Path


DEM_FILE = Path(
    "data/raw/dem/copernicus/N11_E076_Copernicus_GLO30.tif"
)

STUDY_AREA = Path(
    "data/processed/administrative/wayanad_pilot_villages.geojson"
)

OUTPUT_FILE = Path(
    "data/processed/dem/wayanad_pilot_dem.tif"
)


def main():

    print("Loading pilot village boundaries...")

    villages = gpd.read_file(STUDY_AREA)

    print(f"Pilot villages: {len(villages)}")
    print(f"Village CRS: {villages.crs}")

    print("\nLoading Copernicus DEM...")

    with rasterio.open(DEM_FILE) as src:

        print(f"DEM CRS: {src.crs}")
        print(f"DEM resolution: {src.res}")

        # Make sure both datasets use the same CRS
        villages = villages.to_crs(src.crs)

        geometries = villages.geometry.tolist()

        print("\nClipping DEM to pilot villages...")

        clipped, transform = mask(
            src,
            geometries,
            crop=True
        )

        profile = src.profile.copy()

        profile.update(
            {
                "height": clipped.shape[1],
                "width": clipped.shape[2],
                "transform": transform,
                "compress": "lzw"
            }
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with rasterio.open(
        OUTPUT_FILE,
        "w",
        **profile
    ) as dst:

        dst.write(clipped)

    print("\nDEM clipping completed successfully.")

    print(f"Saved to:")
    print(OUTPUT_FILE.resolve())


if __name__ == "__main__":
    main()