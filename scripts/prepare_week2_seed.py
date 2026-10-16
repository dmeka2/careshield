import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "samples" / "sample.json"
OUTPUT = ROOT / "data" / "seed_corpus" / "processed" / "week1_labeled_pilot.csv"

SCAM_FAMILIES = {
    "insurance_enrollment": {"m001", "m002", "m003"},
    "medical_debt": {"m004", "m005", "m006"},
    "pharmacy": {"m007", "m008", "m009"},
    "phishing": {"m010", "m011", "m012"},
    "impersonation": {"m013", "m014", "m015"},
}

SPANISH_IDS = {"m003", "m006", "m009", "m012", "m015", "m020"}
EXPECTED_IDS = {f"m{i:03d}" for i in range(1, 21)}

COLUMNS = [
    "id", "channel", "language", "text",
    "label", "family", "source"
]


def main() -> None:
    original = json.loads(INPUT.read_text(encoding="utf-8-sig"))
    ids = [item["id"] for item in original]

    if len(ids) != 20 or set(ids) != EXPECTED_IDS:
        raise ValueError("Expected exactly the 20 Week 1 sample IDs")

    labeled = []

    for item in original:
        message_id = item["id"]

        family = next(
            (
                name
                for name, members in SCAM_FAMILIES.items()
                if message_id in members
            ),
            "none",
        )

        labeled.append({
            "id": message_id,
            "channel": item["channel"],
            "language": "es" if message_id in SPANISH_IDS else "en",
            "text": item["text"],
            "label": "legitimate" if family == "none" else "scam",
            "family": family,
            "source": "careshield_synthetic_week1",
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(labeled)

    print(f"Created: {OUTPUT}")
    print(f"Total: {len(labeled)}")
    print(f"Labels: {dict(Counter(row['label'] for row in labeled))}")
    print(f"Languages: {dict(Counter(row['language'] for row in labeled))}")


if __name__ == "__main__":
    main()