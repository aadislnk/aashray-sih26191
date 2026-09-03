from pathlib import Path
import fitz
import subprocess
import tempfile
import re

PDF = Path("data/raw/coastal/nccr_odisha_shoreline_change.pdf")

TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")

KEYWORDS = [
    "kendrapara",
    "pentha",
    "satbhaya",
    "gairmatha",
    "habalikhuti",
]

print("=" * 70)
print("AASHRAY NCCR KENDRAPARA OCR")
print("=" * 70)

if not PDF.exists():
    print("\nERROR: NCCR PDF not found:")
    print(PDF.resolve())
    raise SystemExit(1)

if not TESSERACT.exists():
    print("\nERROR: Tesseract not found:")
    print(TESSERACT)
    raise SystemExit(1)

doc = fitz.open(PDF)

print(f"\nTotal pages: {len(doc)}")
print("Starting OCR...")
print("This may take a few minutes.\n")

matches = []

with tempfile.TemporaryDirectory() as temp_dir:

    temp_dir = Path(temp_dir)

    for page_number, page in enumerate(doc, start=1):

        print(
            f"\rProcessing page {page_number}/{len(doc)}...",
            end="",
            flush=True
        )

        # Render page at good OCR resolution
        pix = page.get_pixmap(
            matrix=fitz.Matrix(2, 2),
            colorspace=fitz.csRGB
        )

        image_path = temp_dir / f"page_{page_number}.png"
        pix.save(image_path)

        # Run Tesseract
        result = subprocess.run(
            [
                str(TESSERACT),
                str(image_path),
                "stdout",
                "--psm",
                "6"
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        text = result.stdout

        text_lower = text.lower()

        found_keywords = []

        for keyword in KEYWORDS:
            if keyword in text_lower:
                found_keywords.append(keyword)

        if found_keywords:

            matches.append(
                {
                    "page": page_number,
                    "keywords": found_keywords,
                    "text": text
                }
            )

print("\n\n" + "=" * 70)
print("OCR SEARCH RESULTS")
print("=" * 70)

print(f"\nRelevant pages found: {len(matches)}")

if not matches:
    print("\nNo Kendrapara-related pages were detected.")
    print("OCR may need a different configuration.")
else:

    for item in matches:

        print("\n" + "-" * 70)
        print(f"PAGE {item['page']}")
        print(
            "Keywords:",
            ", ".join(item["keywords"])
        )
        print("-" * 70)

        # Print only useful OCR lines
        lines = item["text"].splitlines()

        for line in lines:

            clean = re.sub(
                r"\s+",
                " ",
                line
            ).strip()

            if not clean:
                continue

            if any(
                keyword in clean.lower()
                for keyword in KEYWORDS
            ):
                print(clean)

print("\n" + "=" * 70)
print("NCCR OCR COMPLETE")
print("=" * 70)