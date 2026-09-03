from pathlib import Path
import geopandas as gpd

print("=" * 70)
print("AASHRAY KENDRAPARA COASTAL VILLAGE EXTRACTION")
print("=" * 70)

INPUT = Path("data/processed/administrative/kendrapara_villages.geojson")
OUTPUT = Path("data/processed/administrative/kendrapara_coastal_villages.geojson")

print("\nLoading Kendrapara villages...")
gdf = gpd.read_file(INPUT)

print(f"Total Kendrapara villages: {len(gdf)}")

# Blocks that directly represent the coastal belt / coastal-facing areas
coastal_blocks = [
    "Mahakalapada",
    "Marsaghai",
    "Rajnagar",
    "Rajkanika",
]

gdf["block_clean"] = (
    gdf["block"]
    .astype(str)
    .str.strip()
    .str.lower()
)

coastal = gdf[
    gdf["block_clean"].isin(
        [b.lower() for b in coastal_blocks]
    )
].copy()

# Remove helper column before saving
coastal = coastal.drop(columns=["block_clean"])

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

coastal.to_file(
    OUTPUT,
    driver="GeoJSON"
)

print(f"\nCoastal-belt villages: {len(coastal)}")
print(f"\nSaved: {OUTPUT.resolve()}")

print("\nCoastal blocks represented:")

for block in coastal_blocks:
    count = len(
        coastal[
            coastal["block"]
            .astype(str)
            .str.strip()
            .str.lower()
            == block.lower()
        ]
    )
    print(f"  {block}: {count} villages")

print("\n" + "=" * 70)
print("COASTAL VILLAGE EXTRACTION COMPLETE")
print("=" * 70)