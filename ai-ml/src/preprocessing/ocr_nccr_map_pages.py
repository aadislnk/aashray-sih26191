from pathlib import Path
import subprocess
import re

INPUT_DIR = Path("data/raw/coastal")

TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")

KEYWORDS = [
    "73 L",
    "73L",
    "73 P",
    "73P",
    "Kendrapara",
    "erosion",
    "accretion",
    "shoreline",
    "shore line",
    "stable",
]

print("=" * 70)
print("AASHRAY NCCR MAP PAGE OCR")
print("=" * 70)

matches = []

for page_number in range(55, 82):

    image_path = INPUT_DIR / f"nccr_scan_page_{page_number}.png"

    if not image_path.exists():
        continue

    print(
        f"\rOCR page {page_number}/81...",
        end="",
        flush=True
    )

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
    text_lower = text.lower()

    found = []

    for keyword in KEYWORDS:
        if keyword.lower() in text_lower:
            found.append(keyword)

    if found:

        # Keep useful OCR lines
        useful_lines = []

        for line in text.splitlines():

            clean = re.sub(
                r"\s+",
                " ",
                line
            ).strip()

            if not clean:
                continue

            if any(
                keyword.lower() in clean.lower()
                for keyword in KEYWORDS
            ):
                useful_lines.append(clean)

        matches.append(
            {
                "page": page_number,
                "keywords": found,
                "lines": useful_lines
            }
        )

print("\n\n" + "=" * 70)
print("MAP PAGE OCR RESULTS")
print("=" * 70)

print(f"\nPages with relevant OCR matches: {len(matches)}")

for item in matches:

    print("\n" + "-" * 70)
    print(f"PAGE {item['page']}")
    print(
        "Keywords:",
        ", ".join(item["keywords"])
    )
    print("-" * 70)

    for line in item["lines"]:
        print(line)

print("\n" + "=" * 70)
print("MAP PAGE OCR COMPLETE")
print("=" * 70)