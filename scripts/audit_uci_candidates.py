"""Create a private human-review queue for staged UCI SMS candidates.

This is a conservative screening aid, not PII anonymization or label approval.
"""

import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "seed_corpus" / "staging" / "uci_ham_candidates.csv"
QUEUE = ROOT / "data" / "seed_corpus" / "staging" / "uci_review_queue.csv"
SUMMARY = ROOT / "data" / "seed_corpus" / "staging" / "uci_review_summary.json"

INPUT_FIELDS = {"id", "channel", "language", "text", "label", "family", "source"}
QUEUE_FIELDS = [
    "id", "channel", "original_language", "text", "provisional_label",
    "family", "source", "privacy_flags", "review_status",
    "reviewed_label", "reviewed_language", "review_notes",
]

# These patterns only flag candidates for manual inspection. They are incomplete.
PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", re.IGNORECASE),
    "url": re.compile(r"https?://|www\.", re.IGNORECASE),
    "long_number": re.compile(r"(?<!\d)(?:\+?\d[\s().-]*){8,}(?!\d)"),
    "location_reference": re.compile(
        r"\b(?:street|avenue|boulevard|postcode|post\s*code|zip\s*code)\b",
        re.IGNORECASE,
    ),
    "sensitive_term": re.compile(
        r"\b(?:account\s*(?:number|no\.)|social security|passport|date of birth|dob|ssn)\b",
        re.IGNORECASE,
    ),
    "named_greeting": re.compile(r"\b(?:hi|hey|hello|dear)\s+[A-Z][a-z]{2,}\b"),
}


def find_flags(text: str) -> list[str]:
    """Find obvious review indicators, not every form of personal data."""
    return [name for name, pattern in PATTERNS.items() if pattern.search(text)]


def prepare_review(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict]:
    """Build a private review queue without automatically approving any row."""
    if not rows:
        raise ValueError("Candidate input is empty.")

    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate candidate IDs found.")

    output = []
    flag_counts = Counter()
    flagged = 0

    for row in rows:
        if not row["text"].strip():
            raise ValueError(f"Empty text for record {row['id']}.")
        if row["label"] != "legitimate" or row["source"] != "uci_sms_spam_collection":
            raise ValueError("Unexpected UCI source or provisional label.")

        flags = find_flags(row["text"])
        flag_counts.update(flags)
        flagged += bool(flags)
        output.append({
            "id": row["id"],
            "channel": row["channel"],
            "original_language": row["language"],
            "text": row["text"],
            "provisional_label": row["label"],
            "family": row["family"],
            "source": row["source"],
            "privacy_flags": ";".join(flags),
            "review_status": "pending",
            "reviewed_label": "",
            "reviewed_language": "",
            "review_notes": "",
        })

    summary = {
        "total_candidates": len(rows),
        "pending_human_review": len(rows),
        "approved": 0,
        "flagged_for_privacy_review": flagged,
        "without_automatic_flags": len(rows) - flagged,
        "flag_counts": dict(sorted(flag_counts.items())),
        "source": "uci_sms_spam_collection",
        "warning": (
            "Heuristic scanning cannot establish that any message is PII-free, "
            "correctly labeled, or English. All messages require manual review."
        ),
    }
    return output, summary


def main() -> None:
    if not INPUT.is_file():
        raise FileNotFoundError("Run scripts/import_uci_sms.py first.")

    # Never overwrite an existing queue containing manual review decisions.
    if QUEUE.exists():
        print("Existing private review queue detected; leaving it unchanged.")
        print(f"Review queue: {QUEUE}")
        return

    with INPUT.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not INPUT_FIELDS <= set(reader.fieldnames):
            raise ValueError("Candidate CSV is missing required columns.")
        input_rows = list(reader)

    review_rows, summary = prepare_review(input_rows)
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_FIELDS)
        writer.writeheader()
        writer.writerows(review_rows)

    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print("UCI PRIVATE REVIEW SUMMARY")
    print(f"Candidates: {summary['total_candidates']}")
    print(f"Flagged for extra privacy review: {summary['flagged_for_privacy_review']}")
    print(f"Without automatic flags: {summary['without_automatic_flags']}")
    print(f"Pending manual review: {summary['pending_human_review']}")
    print("Approved for final dataset: 0")
    print(f"Review queue (PRIVATE): {QUEUE}")
    print(f"Summary (PRIVATE): {SUMMARY}")
    print("Do not upload the review queue, raw data, or message texts to GitHub.")


if __name__ == "__main__":
    main()
