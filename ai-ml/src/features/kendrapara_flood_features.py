import re
from pathlib import Path

import pandas as pd
import geopandas as gpd
import pymupdf


# ============================================================
# PATHS
# ============================================================

PDF_PATH = Path("data/raw/flood/odisha_flood_hazard_atlas.pdf")

VILLAGE_GEOJSON = Path(
    "data/processed/administrative/kendrapara_coastal_villages.geojson"
)

OUTPUT_CSV = Path(
    "data/processed/features/kendrapara_flood_hazard_features.csv"
)

OUTPUT_GEOJSON = Path(
    "data/processed/flood/kendrapara_flood_hazard.geojson"
)


# ============================================================
# KENDRAPARA FLOOD ATLAS PAGES
# PDF pages 158-163
# Python uses zero-based page numbers -> 157-162
# ============================================================

START_PAGE = 157
END_PAGE = 163


# ============================================================
# FLOOD HAZARD SCORES
# ============================================================

CATEGORY_SCORE = {
    "VERY LOW": 0.10,
    "LOW": 0.30,
    "MODERATE": 0.55,
    "HIGH": 0.80,
    "VERY HIGH": 1.00,
}


CATEGORY_OCCURRENCE = {
    "VERY LOW": "1 time",
    "LOW": "2-4 times",
    "MODERATE": "5-6 times",
    "HIGH": "7-9 times",
    "VERY HIGH": "10-14 times",
}


# ============================================================
# CLEAN NAME
# ============================================================

def clean_name(name):

    if name is None:
        return ""

    name = str(name)

    name = name.replace("\n", " ")
    name = re.sub(r"\s+", " ", name)

    return name.strip().lower()


# ============================================================
# DETECT FLOOD CATEGORY
# ============================================================

def detect_category(line):

    line = line.upper()

    if "VERY HIGH" in line and "10-14" in line:
        return "VERY HIGH"

    if re.search(r"\bHIGH\s*\(7-9\)", line):
        return "HIGH"

    if "MODERATE" in line and "5-6" in line:
        return "MODERATE"

    if re.search(r"\bLOW\s*\(2-4\)", line):
        return "LOW"

    if "VERY LOW" in line and "1 TIME" in line:
        return "VERY LOW"

    return None


# ============================================================
# EXTRACT TABLE TEXT
# ============================================================

def extract_text():

    print("Opening Flood Hazard Atlas...")

    pdf = pymupdf.open(PDF_PATH)

    all_text = []

    for page_number in range(START_PAGE, END_PAGE):

        page = pdf[page_number]

        text = page.get_text()

        print(
            f"Reading PDF page {page_number + 1}: "
            f"{len(text)} characters"
        )

        all_text.append(text)

    pdf.close()

    return "\n".join(all_text)


# ============================================================
# PARSE TABLE
# ============================================================

def parse_table(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    records = []

    current_category = None

    # The PDF table contains three columns.
    # Text extraction places:
    #
    # village
    # tehsil
    # village
    # tehsil
    # village
    # tehsil
    #
    # We therefore identify villages by matching
    # against our actual Kendrapara village list.
    #
    # This avoids treating tehsil names as villages.

    villages = gpd.read_file(VILLAGE_GEOJSON)

    official_names = {}

    for name in villages["village"].dropna():

        cleaned = clean_name(name)

        if cleaned:
            official_names[cleaned] = str(name)

    print(
        f"Official Kendrapara village names available: "
        f"{len(official_names)}"
    )

    for line in lines:

        category = detect_category(line)

        if category:

            current_category = category
            continue

        if current_category is None:
            continue

        cleaned = clean_name(line)

        # Only accept names that actually exist
        # in our Kendrapara village boundary dataset.
        if cleaned in official_names:

            records.append(
                {
                    "village": official_names[cleaned],
                    "flood_hazard_category": current_category,
                    "flood_hazard_score": CATEGORY_SCORE[
                        current_category
                    ],
                    "flood_occurrence_range": CATEGORY_OCCURRENCE[
                        current_category
                    ],
                }
            )

    # Remove duplicate village/category combinations
    df = pd.DataFrame(records)

    if len(df) == 0:
        return df

    df = df.drop_duplicates(
        subset=["village", "flood_hazard_category"]
    )

    return df


# ============================================================
# CREATE FINAL VILLAGE FLOOD LAYER
# ============================================================

def create_layer(records):

    villages = gpd.read_file(VILLAGE_GEOJSON)

    print(
        f"\nCoastal Kendrapara villages: {len(villages)}"
    )

    # Start with NO DATA
    villages["flood_hazard_category"] = "NO_DATA"
    villages["flood_hazard_score"] = 0.0
    villages["flood_occurrence_range"] = "NO_DATA"

    villages["flood_data_source"] = (
        "OSDMA/NRSC Flood Hazard Atlas 2001-2018"
    )

    if len(records) == 0:

        print("WARNING: No village matches found.")

        return villages

    # --------------------------------------------------------
    # Build lookup
    # --------------------------------------------------------

    hazard_lookup = {}

    for _, row in records.iterrows():

        village = clean_name(row["village"])

        score = float(row["flood_hazard_score"])

        # If duplicate village records exist,
        # retain the highest hazard category.
        if (
            village not in hazard_lookup
            or score > hazard_lookup[village]["score"]
        ):

            hazard_lookup[village] = {
                "category": row["flood_hazard_category"],
                "score": score,
                "occurrence": row["flood_occurrence_range"],
            }

    # --------------------------------------------------------
    # Match villages
    # --------------------------------------------------------

    matched = 0

    for index, row in villages.iterrows():

        village_name = clean_name(row["village"])

        if village_name in hazard_lookup:

            hazard = hazard_lookup[village_name]

            villages.loc[
                index,
                "flood_hazard_category"
            ] = hazard["category"]

            villages.loc[
                index,
                "flood_hazard_score"
            ] = hazard["score"]

            villages.loc[
                index,
                "flood_occurrence_range"
            ] = hazard["occurrence"]

            matched += 1

    print(f"Matched villages: {matched}")

    # --------------------------------------------------------
    # Save GeoJSON
    # --------------------------------------------------------

    OUTPUT_GEOJSON.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    villages.to_file(
        OUTPUT_GEOJSON,
        driver="GeoJSON"
    )

    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    columns = [
        "village",
        "vlcode",
        "block",
        "district",
        "flood_hazard_category",
        "flood_hazard_score",
        "flood_occurrence_range",
        "flood_data_source",
    ]

    columns = [
        column
        for column in columns
        if column in villages.columns
    ]

    villages[columns].to_csv(
        OUTPUT_CSV,
        index=False
    )

    return villages


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("KENDRAPARA FLOOD HAZARD EXTRACTION")
    print("=" * 60)

    text = extract_text()

    print("\nParsing Kendrapara flood table...")

    records = parse_table(text)

    print(
        f"Matched table records before deduplication: "
        f"{len(records)}"
    )

    villages = create_layer(records)

    print("\n" + "=" * 60)
    print("FLOOD HAZARD DISTRIBUTION")
    print("=" * 60)

    print(
        villages[
            "flood_hazard_category"
        ].value_counts()
    )

    print("\nOutputs:")

    print(
        f"CSV:     {OUTPUT_CSV}"
    )

    print(
        f"GeoJSON: {OUTPUT_GEOJSON}"
    )

    print("\nDONE.")


if __name__ == "__main__":
    main()