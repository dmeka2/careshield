"""Private terminal-only review of IMC25 healthcare-keyword candidates.

Never copy message text/screenshots into chat, tickets, reports, or GitHub.
Approval here is a provisional human judgment, NOT publication authorization.
"""

import argparse
import json
import os
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "data/seed_corpus/staging/imc25_healthcare_review_queue.json"
EXPECTED_SCHEMA = "careshield-imc25-private-queue-v1"
FAMILY_CHOICES = {
    "1": "insurance_enrollment",
    "2": "medical_debt",
    "3": "pharmacy",
    "4": "phishing",
    "5": "impersonation",
}


def load_queue(path: Path) -> dict:
    """Reject invalid/corrupted queue files before any changes."""
    if not path.is_file():
        raise FileNotFoundError(f"Private IMC25 queue missing: {path.name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("IMC25 queue must be a mapping")
    if payload.get("schema") != EXPECTED_SCHEMA:
        raise ValueError("Unexpected IMC25 queue schema")
    items = payload.get("items")
    if not isinstance(items, list):
        raise TypeError("IMC25 queue items must be a list")
    if not items:
        raise ValueError("IMC25 queue is empty")
    if len({item["id"] for item in items}) != len(items):
        raise ValueError("Duplicate IDs in IMC25 review queue")
    if any(item.get("review_status") not in {"pending", "reviewed", "hold", "rejected"}
           for item in items):
        raise ValueError("Unknown review status in IMC25 review queue")
    return payload


def decision(item: dict, choice: str) -> str:
    """Apply a manual decision in memory; never publish unredacted records."""
    if item["review_status"] != "pending":
        raise ValueError("Only pending entries may be reviewed")
    choice = choice.strip().lower()
    if choice in FAMILY_CHOICES or choice == "l":
        if item["privacy_flags"]:
            item["review_status"] = "hold"
            item["review_note"] = "Privacy or URL review required before labeling."
            return "held for privacy/URL check"
        item["review_status"] = "reviewed"
        item["reviewed_label"] = "scam" if choice in FAMILY_CHOICES else "legitimate"
        item["reviewed_family"] = FAMILY_CHOICES.get(choice, "none")
        item["review_note"] = (
            "Human provisional classification; independent evidence, privacy verification, "
            "and deduplication still required before release."
        )
        return "provisionally reviewed (not published or final-approved)"
    if choice == "h":
        item["review_status"] = "hold"
        item["review_note"] = "Needs deeper language/privacy/fraud review."
        return "held"
    if choice == "r":
        item["review_status"] = "rejected"
        item["review_note"] = "Excluded by manual reviewer."
        return "rejected"
    raise ValueError("Decision must be 1-5, L, H, or R")


def counts(payload: dict) -> dict[str, int]:
    """Produce aggregate status counts only."""
    counter = Counter(item["review_status"] for item in payload["items"])
    return {key: counter[key] for key in ("pending", "reviewed", "hold", "rejected")}


def print_summary(payload: dict) -> None:
    print("IMC25 PRIVATE REVIEW PROGRESS - COUNTS ONLY")
    print("-------------------------------------------")
    for label, count in counts(payload).items():
        print(f"{label.title()}: {count}")
    print("Approved for public dataset: 0 (separate privacy/release gate required)")
    print("Human review decisions remain local and are not Git-committed.")


def save_queue(path: Path, payload: dict) -> None:
    """Atomically save the private queue with a small same-folder temporary file."""
    tmp = path.with_name(path.name + ".tmp")
    try:
        with tmp.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def review(batch_size: int) -> None:
    payload = load_queue(QUEUE)
    pending = [item for item in payload["items"] if item["review_status"] == "pending"]
    if not pending:
        print_summary(payload)
        return
    selection = pending[:batch_size]
    backup = QUEUE.with_name(
        f"imc25_review_backup_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S_%f')}.json"
    )
    shutil.copy2(QUEUE, backup)
    print("A private backup was created. Review text on your computer only.")
    print("1=enrollment scam, 2=medical debt, 3=pharmacy, 4=phishing, 5=impersonation")
    print("L=verified benign healthcare, H=hold, R=reject/not healthcare, Q=save and quit")
    print("Source categories are UNVERIFIED. Do not click URLs, share SMS text, or guess labels.")
    print("Any privacy/URL flag automatically sends an approval attempt to HOLD.")
    for index, item in enumerate(selection, 1):
        print(f"\n--- Private candidate {index}/{len(selection)} ---")
        print(f"Source language: {item['language']} | Source category (unverified): "
              f"{item['source_scam_type']} | Match: {item['match_type']}")
        print("Basic privacy/URL flags:", ", ".join(item["privacy_flags"]) or "none (not safe by default)")
        print("PRIVATE SMS TEXT - DO NOT COPY TO CHAT:")
        print(item["text"])
        while True:
            try:
                choice = input("Review decision [1/2/3/4/5/L/H/R/Q]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nReview interrupted; previously saved decisions are preserved.")
                print_summary(payload)
                return
            if choice in {*FAMILY_CHOICES, "l", "h", "r", "q"}:
                break
            print("Choose 1, 2, 3, 4, 5, L, H, R, or Q.")
        if choice == "q":
            break
        result = decision(item, choice)
        save_queue(QUEUE, payload)
        print("Decision saved:", result)
    print()
    print_summary(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true", help="Only print private queue counts")
    parser.add_argument("--batch-size", type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 20:
        parser.error("Batch size must be between 1 and 20")
    if args.summary:
        print_summary(load_queue(QUEUE))
    else:
        review(args.batch_size)


if __name__ == "__main__":
    main()
