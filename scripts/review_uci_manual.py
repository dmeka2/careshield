"""Private, one-at-a-time human review of staged UCI SMS candidates."""

import argparse
import csv
import os
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "data" / "seed_corpus" / "staging" / "uci_review_queue.csv"
REQUIRED_FIELDS = {
    "id", "channel", "original_language", "text", "provisional_label",
    "family", "source", "privacy_flags", "review_status", "reviewed_label",
    "reviewed_language", "review_notes",
}
VALID_STATUSES = {"pending", "approved", "hold", "rejected"}


def load_queue(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Read a private review queue; reject unexpected columns or status values."""
    if not path.is_file():
        raise FileNotFoundError(f"Private review queue not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        if not fields or not REQUIRED_FIELDS <= set(fields):
            raise ValueError("Review queue is missing expected columns.")
        rows = list(reader)
    if not rows or len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Review queue is empty or contains duplicate IDs.")
    for row in rows:
        if row["review_status"] not in VALID_STATUSES:
            raise ValueError("Review queue contains an unexpected status.")
        if (row["source"] != "uci_sms_spam_collection"
                or row["provisional_label"] != "legitimate"):
            raise ValueError("Review queue contains an unexpected source or label.")
    return rows, fields


def apply_decision(row: dict[str, str], choice: str) -> None:
    """Record one explicit human review decision."""
    if row["review_status"] != "pending":
        raise ValueError("Only pending messages can be reviewed.")
    decisions = {
        "a": ("approved", "legitimate", "en", "Human-reviewed as benign English; no identifying details found."),
        "b": ("approved", "legitimate", "es", "Human-reviewed as benign Spanish; no identifying details found."),
        "h": ("hold", "", "", "Held for deeper privacy, label, or language review."),
        "r": ("rejected", "", "", "Excluded after human privacy or labeling review."),
    }
    if choice not in decisions:
        raise ValueError("Unrecognized review choice.")
    status, label, language, notes = decisions[choice]
    row.update(review_status=status, reviewed_label=label,
               reviewed_language=language, review_notes=notes)


def save_queue(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    """Persist each decision atomically to the private staging directory."""
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def count_statuses(rows: list[dict[str, str]]) -> dict[str, int]:
    counts = Counter(row["review_status"] for row in rows)
    return {key: counts[key] for key in ("approved", "rejected", "hold", "pending")}


def print_summary(rows: list[dict[str, str]]) -> None:
    print("\nPRIVATE UCI REVIEW PROGRESS (COUNTS ONLY)")
    print("-----------------------------------------")
    print(f"Total: {len(rows)}")
    for status, count in count_statuses(rows).items():
        print(f"{status.capitalize()}: {count}")
    pending_flags = sum(
        bool(row["privacy_flags"]) and row["review_status"] == "pending"
        for row in rows
    )
    print(f"Pending with automatic privacy flags: {pending_flags}")
    print("Human approval is required; automated screening is not proof of safety.")


def review(batch_size: int) -> None:
    rows, fields = load_queue(QUEUE)
    pending = [row for row in rows if row["review_status"] == "pending"]
    if not pending:
        print("No pending messages.")
        print_summary(rows)
        return
    # Prioritize the two flagged examples, while keeping others in their source order.
    pending.sort(key=lambda row: not bool(row["privacy_flags"]))
    selected = pending[:batch_size]
    backup = QUEUE.with_name(
        f"uci_review_queue_backup_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S_%f')}.csv"
    )
    shutil.copy2(QUEUE, backup)
    print(f"Private queue backup created: {backup.name}")
    print("Review message text ONLY on your computer; do not share text/screenshots.")
    print("Approve only when benign, in the selected language, and free of identifying details.")
    print("A = approve English, B = approve Spanish, H = hold, R = reject, Q = quit")

    for index, row in enumerate(selected, 1):
        print(f"\n--- Private message {index}/{len(selected)} ---")
        print(f"ID: {row['id']} | Channel: {row['channel']}")
        print(f"Flags: {row['privacy_flags'] or 'none (not a safety guarantee)'}")
        print("PRIVATE MESSAGE:")
        print(row["text"])
        while True:
            try:
                choice = input("Decision [A/B/H/R/Q]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nSession stopped; completed decisions are saved.")
                print_summary(rows)
                return
            if choice in {"a", "b", "h", "r", "q"}:
                break
            print("Please type A, B, H, R, or Q.")
        if choice == "q":
            break
        if choice in {"a", "b"} and row["privacy_flags"]:
            confirmation = input(
                "Privacy flag present: type VERIFIED if fully checked, "
                "or press Enter to hold: "
            ).strip()
            if confirmation != "VERIFIED":
                choice = "h"
        apply_decision(row, choice)
        save_queue(QUEUE, rows, fields)
        print(f"Decision saved: {row['review_status']}")
    print_summary(rows)
    print("Private review files stay under data/seed_corpus/staging/ (Git-ignored).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--summary", action="store_true", help="Show counts only")
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 50:
        parser.error("Batch size must be 1 to 50")
    if args.summary:
        rows, _ = load_queue(QUEUE)
        print_summary(rows)
    else:
        review(args.batch_size)


if __name__ == "__main__":
    main()
