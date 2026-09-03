from pathlib import Path
import subprocess
import tempfile
import fitz

PDF = Path("data/raw/coastal/Shoreline_Change_Atlas_Vol-V.pdf")
TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")

KEYWORDS = [
    "73L/11/NE",
    "73L/14/NE",
    "73L/14/SE",
    "73L/14/SW",
    "73L/15/NW",
    "73P/2/NW",
    "73 L/11/NE",
    "73 L/14/NE",
    "73 L/14/SE",
    "73 L/14/SW",
    "73 L/15/NW",
    "73 P/2/NW",
]

print("=" * 70)
print("AASHRAY SAC/ISRO KENDRAPARA OCR SEARCH")
print("=" * 70)

if not PDF.exists():
    print("\nERROR: Atlas not found:")
    print(PDF.resolve())
    raise SystemExit(1)

if not TESSERACT.exists():
    print("\nERROR: Tesseract not found:")
    print(TESSERACT)
    raise SystemExit(1)

doc = fitz.open(PDF)

print(f"\nTotal atlas pages: {len(doc)}")
print("Searching for the six Kendrapara map sheets...")
print("This may take a few minutes.\n")

matches = []

with tempfile.TemporaryDirectory() as temp_dir:

    temp_dir = Path(temp_dir)

    for page_number, page in enumerate(doc, start=1):

        print(
            f"\rOCR page {page_number}/{len(doc)}...",
            end="",
            flush=True
        )

        pix = page.get_pixmap(
            matrix=fitz.Matrix(2, 2),
            colorspace=fitz.csRGB
        )

        image_path = temp_dir / f"page_{page_number}.png"
        pix.save(image_path)

        result = subprocess.run(
            [
                str(TESSERACT),
                str(image_path),
                "stdout",
                "--psm",
                "11"
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        text = result.stdout
        text_normalized = (
            text.lower()
            .replace(" ", "")
            .replace("\n", "")
            .replace("\r", "")
        )

        found = []

        for keyword in KEYWORDS:

            keyword_normalized = (
                keyword.lower()
                .replace(" ", "")
            )

            if keyword_normalized in text_normalized:
                found.append(keyword)

        if found:
            matches.append(
                {
                    "page": page_number,
                    "sheets": sorted(set(found))
                }
            )

print("\n\n" + "=" * 70)
print("KENDRAPARA SHEET SEARCH RESULTS")
print("=" * 70)

if not matches:

    print("\nNo exact Kendrapara sheet numbers detected.")

    print(
        "\nThe atlas may use a different sheet-number format."
    )

else:

    print(
        f"\nPages containing Kendrapara sheet references: "
        f"{len(matches)}"
    )

    for item in matches:

        print(
            f"\nPage {item['page']}: "
            f"{', '.join(item['sheets'])}"
        )

print("\n" + "=" * 70)
print("SAC/ISRO KENDRAPARA OCR SEARCH COMPLETE")
print("=" * 70)