from pathlib import Path
import re
import fitz
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PDF_PATH = Path(
    "data/raw/landslides/landslide_report.pdf"
)

OUTPUT_DIR = Path(
    "data/processed/landslides"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "wayanad_landslide_inventory_full.csv"
)


# ============================================================
# BASIC CLEANING
# ============================================================

def clean(value):
    """Clean whitespace and PDF artifacts."""

    if value is None:
        return ""

    value = str(value)

    value = value.replace("\xa0", " ")
    value = value.replace("\r", " ")
    value = value.replace("\n", " ")

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# ============================================================
# COORDINATE EXTRACTION
# ============================================================

def extract_coordinates(text):
    """
    Find Kerala/Wayanad latitude and longitude.

    Expected approximate ranges:

        Latitude  : 8 - 14
        Longitude : 74 - 78
    """

    text = clean(text)

    patterns = [

        # Example:
        # 11.46277778 76.13416667
        r"(?P<lat>1[0-4]\.\d+|[89]\.\d+)"
        r"\s+"
        r"(?P<lon>7[4-8]\.\d+)",

        # Example:
        # Latitude 11.46277778 Longitude 76.13416667
        r"Latitude\s*[:=]?\s*"
        r"(?P<lat>1[0-4]\.\d+|[89]\.\d+)"
        r".{0,100}?"
        r"Longitude\s*[:=]?\s*"
        r"(?P<lon>7[4-8]\.\d+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            try:

                lat = float(
                    match.group("lat")
                )

                lon = float(
                    match.group("lon")
                )

                if (
                    8 <= lat <= 14
                    and
                    74 <= lon <= 78
                ):
                    return lat, lon

            except (
                ValueError,
                TypeError
            ):
                pass

    return None, None


# ============================================================
# DATE EXTRACTION
# ============================================================

def extract_date(text):
    """Extract common date formats from report text."""

    text = clean(text)

    patterns = [

        # 30/07/2024
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b",

        # 30 July 2024
        r"\b\d{1,2}\s+"
        r"(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+\d{4}\b",

        # July 30, 2024
        r"\b"
        r"(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+\d{1,2}"
        r"(?:,\s*|\s+)"
        r"\d{4}\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            return clean(
                match.group(0)
            )

    return ""


# ============================================================
# LOCATION EXTRACTION
# ============================================================

def extract_location(text):
    """
    Detect known Wayanad locations appearing in a page/record.
    """

    text_lower = text.lower()

    locations = [

        "Mundakkai",
        "Mundakai",
        "Mundakkai Estate",

        "Chooralmala",
        "Churalmala",

        "Attamala",
        "Attamala Estate",

        "Meppadi",

        "Vellarimala",
        "Velarimala",

        "Thrikaipetta",
        "Thrikkaipatta",

        "Kottappadi",

        "Puthumala",

        "Kalladi",

        "Sugandhagiri",

        "Chembra",

        "Lakkidi",

        "900 Acres",
    ]

    found = []

    for location in locations:

        if location.lower() in text_lower:

            found.append(location)

    # Preserve order and remove duplicates.
    return ", ".join(
        dict.fromkeys(found)
    )


# ============================================================
# MOVEMENT TYPE
# ============================================================

def extract_movement_type(text):
    """Detect landslide movement types."""

    text_lower = text.lower()

    patterns = [

        "rock cum debris slide",
        "rock cum debris flow",

        "debris flow",
        "debris flows",

        "debris slide",
        "debris slides",

        "rock fall",
        "rockfall",

        "rock slide",
        "rockslide",

        "rock topple",

        "mud flow",
        "mudflow",

        "mud slide",
        "mudslide",

        "soil slide",
        "soil flow",

        "soil creep",

        "subsidence",

        "creep",

        "landslide",
    ]

    found = []

    for pattern in patterns:

        if pattern in text_lower:

            found.append(pattern)

    return ", ".join(
        dict.fromkeys(found)
    )


# ============================================================
# SLIDE NUMBER DETECTION
# ============================================================

SLIDE_ID_PATTERN = re.compile(
    r"""
    \b
    (?:KER|KRL|KL)
    /
    [A-Z0-9]+
    /
    [A-Z0-9]+
    /
    [A-Z0-9]+
    /
    [A-Z0-9]+
    (?:/[A-Z0-9]+)*
    \b
    """,
    flags=re.IGNORECASE | re.VERBOSE
)


# ============================================================
# ROW EXTRACTION
# ============================================================

def extract_records_from_page(
    text,
    page_number
):
    """
    Extract individual landslide records from a
    Wayanad table page.

    The PDF table may be represented as plain text
    after extraction, so this function uses slide IDs
    as row anchors.
    """

    records = []

    text = text.replace(
        "\r",
        "\n"
    )

    matches = list(
        SLIDE_ID_PATTERN.finditer(text)
    )

    if not matches:
        return records

    for index, match in enumerate(matches):

        slide_no = clean(
            match.group(0)
        )

        start = match.start()

        if index + 1 < len(matches):

            end = matches[
                index + 1
            ].start()

        else:

            end = len(text)

        block = text[
            start:end
        ]

        block = clean(block)

        # We only want Wayanad records.
        # Since the page itself is selected for Wayanad,
        # also require Kerala/Wayanad context.
        if not re.search(
            r"\bWayanad\b",
            block,
            flags=re.IGNORECASE
        ):

            # Sometimes Wayanad appears in a table header
            # rather than every individual row.
            # In that case we still allow the record.
            pass

        lat, lon = extract_coordinates(
            block
        )

        # If no coordinate was found in the row,
        # don't create a geographic event record.
        if lat is None or lon is None:
            continue

        location = extract_location(
            block
        )

        movement = extract_movement_type(
            block
        )

        date = extract_date(
            block
        )

        records.append(
            {
                "slide_no": slide_no,
                "district": "Wayanad",
                "latitude": lat,
                "longitude": lon,
                "location": location,
                "movement_type": movement,
                "history": date,
                "source_page": page_number,
                "source_text": block[:3000],
            }
        )

    return records


# ============================================================
# MAIN EXTRACTION
# ============================================================

def extract():

    if not PDF_PATH.exists():

        raise FileNotFoundError(
            f"\nPDF not found:\n{PDF_PATH.resolve()}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("=" * 70)
    print("AASHRAY LANDSLIDE INVENTORY EXTRACTION")
    print("=" * 70)

    print()
    print("Opening landslide report...")

    # Use PyMuPDF.
    # Newer versions expose it as pymupdf,
    # while fitz remains available.
    doc = fitz.open(
        PDF_PATH
    )

    print(
        f"Total pages: {len(doc)}"
    )

    all_records = []

    wayanad_pages = 0

    for page_number, page in enumerate(
        doc,
        start=1
    ):

        text = page.get_text()

        if not text:
            continue

        # Only inspect Wayanad pages.
        if not re.search(
            r"\bWayanad\b",
            text,
            flags=re.IGNORECASE
        ):
            continue

        wayanad_pages += 1

        records = extract_records_from_page(
            text,
            page_number
        )

        if records:

            all_records.extend(
                records
            )

            print(
                f"Page {page_number}: "
                f"{len(records)} records"
            )

    doc.close()

    print()
    print(
        f"Wayanad pages found: "
        f"{wayanad_pages}"
    )

    print(
        f"Raw records extracted: "
        f"{len(all_records)}"
    )

    if not all_records:

        print()
        print(
            "WARNING: No individual records "
            "were extracted."
        )

        print(
            "The PDF structure may require "
            "a different table parser."
        )

        return

    # ========================================================
    # DATAFRAME
    # ========================================================

    df = pd.DataFrame(
        all_records
    )

    # Make sure coordinates are numeric.
    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )

    # Remove invalid coordinates.
    df = df[
        df["latitude"].between(
            8,
            14
        )
        &
        df["longitude"].between(
            74,
            78
        )
    ]

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    before = len(df)

    df = df.drop_duplicates(
        subset=[
            "slide_no",
            "latitude",
            "longitude",
        ]
    )

    duplicates_removed = (
        before - len(df)
    )

    # ========================================================
    # SORT
    # ========================================================

    df = df.sort_values(
        [
            "source_page",
            "slide_no",
        ]
    ).reset_index(
        drop=True
    )

    # ========================================================
    # SAVE
    # ========================================================

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # ========================================================
    # REPORT
    # ========================================================

    print()
    print("=" * 70)
    print("EXTRACTION COMPLETED")
    print("=" * 70)

    print(
        f"Final records: {len(df)}"
    )

    print(
        f"Duplicates removed: "
        f"{duplicates_removed}"
    )

    print(
        f"Unique source pages: "
        f"{df['source_page'].nunique()}"
    )

    print()
    print(
        f"Saved to:\n"
        f"{OUTPUT_FILE.resolve()}"
    )

    print()
    print("Columns:")

    print(
        df.columns.tolist()
    )

    print()
    print("Movement types:")

    print(
        df[
            "movement_type"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    print()
    print("Sample records:")

    print(
        df[
            [
                "slide_no",
                "district",
                "location",
                "latitude",
                "longitude",
                "movement_type",
                "history",
                "source_page",
            ]
        ]
        .head(20)
        .to_string(
            index=False
        )
    )

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    extract()