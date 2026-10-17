"""Prepare a *private, unapproved* English/Spanish healthcare SMS review queue.

Unifies the broad and narrow search used in earlier manual CareShield audits.
No message text is printed, published, or written outside Git-ignored staging.
Original source annotations are never treated as CareShield labels.
"""

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

from scripts.audit_mendeley_sms import (
    HEALTHCARE_PATTERN,
    PRIVACY_PATTERNS,
    fingerprint,
    load_archive,
)
from scripts.import_uci_sms import extract_messages

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/seed_corpus/raw/smishing_imc25.csv"
UCI = ROOT / "data/seed_corpus/raw/uci_sms.zip"
MENDELEY = ROOT / "data/seed_corpus/raw/Dataset_5971.zip"
PILOT = ROOT / "data/seed_corpus/processed/week1_labeled_pilot.csv"
SYNTHETIC = ROOT / "data/seed_corpus/processed/healthcare_synthetic_week2.csv"
STAGING = ROOT / "data/seed_corpus/staging"
QUEUE = STAGING / "imc25_healthcare_review_queue.json"
SUMMARY = STAGING / "imc25_healthcare_review_summary.json"
SCHEMA = "careshield-imc25-private-queue-v1"

# Extra terms used in Step 5, but omitted in the stricter Step 6 audit.
# Combining them avoids silently losing NHS and similar examples.
EXTRA_HEALTHCARE = re.compile(
    r"\b(?:nhs|medicare|medicaid|obamacare|healthcare)\b", re.IGNORECASE
)
URL_HINT = re.compile(r"(?:https?://|www\.|\b[a-z0-9-]+\.(?:com|org|net|gov|uk)/)", re.IGNORECASE)
LANGUAGES = {"english": "en", "spanish": "es"}
MAX_ROWS = 100_000
MAX_TEXT_CHARS = 10_000


def normalize_column(value: str) -> str:
    """Convert known source field names to simple, unambiguous keys."""
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def infer_fields(headers: list[str]) -> tuple[str, str, str]:
    """Require real category/language columns rather than silently guessing."""
    columns = {normalize_column(name): name for name in headers}
    message = next(
        (columns[key] for key in ("textmessage", "smstext", "message", "text") if key in columns),
        None,
    )
    scam_type = columns.get("scamtype")
    language = columns.get("language")
    if not message or not scam_type or not language:
        raise ValueError("IMC25 CSV lacks text, scam_type, or language columns")
    return message, scam_type, language


def read_source(path: Path) -> list[dict[str, str]]:
    """Read downloaded research CSV without logging any text."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing source file: {path.name}")
    raw = path.read_bytes()
    if len(raw) > 100_000_000:
        raise ValueError("Research CSV is unexpectedly large")
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = raw.decode("cp1252")
    csv.field_size_limit(2_000_000)
    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    message_field, category_field, language_field = infer_fields(reader.fieldnames or [])
    rows = []
    for row in reader:
        if len(rows) >= MAX_ROWS:
            raise ValueError("Unusually many rows in research CSV")
        rows.append({
            "text": row.get(message_field) or "",
            "source_category": row.get(category_field) or "",
            "source_language": row.get(language_field) or "",
        })
    return rows


def uci_fingerprints(raw: bytes) -> set[str]:
    """Compare against the full UCI archive, not just 600 staged candidates."""
    source = extract_messages(raw)
    try:
        content = source.decode("utf-8")
    except UnicodeDecodeError:
        content = source.decode("latin-1")
    result = set()
    for line in content.splitlines():
        label, separator, message = line.partition("\t")
        if separator and label in {"ham", "spam"} and message.strip():
            result.add(fingerprint(message))
    return result


def synthetic_fingerprints(paths: tuple[Path, ...]) -> set[str]:
    """Use only already-published fictional records for exact comparison."""
    result = set()
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"Missing published synthetic source: {path.name}")
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if "text" not in (reader.fieldnames or []):
                raise ValueError(f"Missing text field in {path.name}")
            for row in reader:
                text = row.get("text", "")
                if text.strip():
                    result.add(fingerprint(text))
    return result


def privacy_flags(message: str) -> list[str]:
    """Provide only basic warning signals; not proof of complete redaction."""
    flags = [name for name, pattern in PRIVACY_PATTERNS.items() if pattern.search(message)]
    if URL_HINT.search(message) and "url" not in flags:
        flags.append("url")
    return sorted(flags)


def match_type(message: str) -> str:
    """Distinguish the narrow Step 6 keyword matches from Step 5-only ones."""
    if HEALTHCARE_PATTERN.search(message):
        return "direct"
    if EXTRA_HEALTHCARE.search(message):
        return "broader_only"
    return ""


def make_queue(
    rows: list[dict[str, str]],
    *,
    existing_hashes: dict[str, set[str]],
    source_sha256: str,
) -> tuple[dict, dict]:
    """Select nonduplicated English/Spanish candidates, never preapprove them."""
    seen = set()
    queue = []
    stats = Counter()
    by_language = Counter()
    by_category = Counter()
    by_match_type = Counter()

    for row in rows:
        stats["total_csv_rows"] += 1
        message = row["text"].strip()
        if not message or len(message) > MAX_TEXT_CHARS:
            stats["empty_or_too_long"] += 1
            continue
        kind = match_type(message)
        if not kind:
            continue
        stats["broad_healthcare_matches"] += 1
        stats["direct_matches" if kind == "direct" else "broader_only_matches"] += 1

        digest = fingerprint(message)
        if digest in seen:
            stats["duplicate_candidate_rows"] += 1
            continue
        seen.add(digest)

        if digest in existing_hashes["uci"]:
            stats["overlap_uci"] += 1
            continue
        if digest in existing_hashes["mendeley"]:
            stats["overlap_mendeley"] += 1
            continue
        if digest in existing_hashes["synthetic"]:
            stats["overlap_synthetic"] += 1
            continue

        lang = LANGUAGES.get(row["source_language"].strip().casefold())
        if lang is None:
            stats["excluded_non_english_spanish"] += 1
            continue
        flags = privacy_flags(message)
        if flags:
            stats["queued_with_basic_flags"] += 1
        by_language[lang] += 1
        by_category[row["source_category"].strip().casefold() or "unclassified"] += 1
        by_match_type[kind] += 1
        queue.append({
            "id": "imc25-" + digest[:20],
            "text": message,
            "language": lang,
            "source_scam_type": row["source_category"].strip().casefold() or "unclassified",
            "match_type": kind,
            "privacy_flags": flags,
            "review_status": "pending",
            "reviewed_label": "",
            "reviewed_family": "",
            "review_note": "",
        })

    # Review direct matches and unflagged texts first; flagged examples remain private.
    queue.sort(key=lambda item: (
        item["match_type"] != "direct",
        bool(item["privacy_flags"]),
        item["language"] != "en",
        item["id"],
    ))
    if len({item["id"] for item in queue}) != len(queue):
        raise ValueError("Private IDs are not unique")
    payload = {"schema": SCHEMA, "source_sha256": source_sha256, "items": queue}
    summary = {
        "source": "IMC25 Fishing for Smishing (Agarwal et al., 2025), CC BY 4.0",
        "total_csv_rows": stats["total_csv_rows"],
        "broad_healthcare_keyword_matches": stats["broad_healthcare_matches"],
        "direct_keyword_matches": stats["direct_matches"],
        "broader_only_keyword_matches": stats["broader_only_matches"],
        "duplicate_candidate_rows": stats["duplicate_candidate_rows"],
        "exact_overlap_full_uci": stats["overlap_uci"],
        "exact_overlap_mendeley": stats["overlap_mendeley"],
        "exact_overlap_synthetic": stats["overlap_synthetic"],
        "excluded_other_languages": stats["excluded_non_english_spanish"],
        "private_pending_review": len(queue),
        "with_basic_privacy_or_url_flags": stats["queued_with_basic_flags"],
        "by_language": dict(sorted(by_language.items())),
        "by_source_scam_type_unverified": dict(sorted(by_category.items())),
        "by_match_type": dict(sorted(by_match_type.items())),
        "approved_for_publication": 0,
        "important": (
            "No records have been approved. Source scam types are not healthcare labels. "
            "Privacy flags are incomplete. Exact matching misses paraphrases and related templates. "
            "Human privacy and label review plus cross-source near-deduplication are required."
        ),
    }
    return payload, summary


def write_new_json(path: Path, payload: dict) -> None:
    """Create but never overwrite a file containing potentially reviewed records."""
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def ensure_private_paths() -> None:
    """Fail closed if the target isn't the project's expected private directory."""
    if not STAGING.is_dir():
        raise FileNotFoundError("Private staging directory does not exist")
    if STAGING.is_symlink():
        raise ValueError("Private staging folder must not be a symlink")
    for path in (SOURCE, UCI, MENDELEY, QUEUE, SUMMARY):
        check = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", str(path)],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        if check.returncode != 0:
            raise RuntimeError("Private dataset or review queue is not Git-ignored")
    if not SOURCE.is_file() or not UCI.is_file() or not MENDELEY.is_file():
        raise FileNotFoundError("Required local research source is missing")
    if QUEUE.exists() or SUMMARY.exists():
        raise FileExistsError(
            "IMC25 review queue or summary already exists. No files changed. "
            "Use the review script --summary; do not reset previous decisions."
        )


def run() -> dict:
    """Create both private artifacts after all input checks pass."""
    ensure_private_paths()
    source_bytes = SOURCE.read_bytes()
    rows = read_source(SOURCE)
    uci = uci_fingerprints(UCI.read_bytes())
    mendeley_rows, _ = load_archive(MENDELEY)
    mendeley = {fingerprint(row["text"]) for row in mendeley_rows if row["text"].strip()}
    synthetic = synthetic_fingerprints((PILOT, SYNTHETIC))
    queue, summary = make_queue(
        rows,
        existing_hashes={"uci": uci, "mendeley": mendeley, "synthetic": synthetic},
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
    )
    if not queue["items"]:
        raise ValueError("No candidates found; nothing written")
    write_new_json(QUEUE, queue)
    try:
        write_new_json(SUMMARY, summary)
    except OSError:
        # Never leave a confusing half-setup if the second creation fails.
        QUEUE.unlink()
        raise
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    summary = run()
    print("IMC25 PRIVATE HEALTHCARE REVIEW QUEUE - COUNTS ONLY")
    print("---------------------------------------------------")
    print("Broad healthcare keyword matches:", summary["broad_healthcare_keyword_matches"])
    print("  Direct matches:", summary["direct_keyword_matches"])
    print("  Broader-only matches:", summary["broader_only_keyword_matches"])
    print("Repeated candidate rows:", summary["duplicate_candidate_rows"])
    print("Exact overlap with UCI:", summary["exact_overlap_full_uci"])
    print("Exact overlap with Mendeley:", summary["exact_overlap_mendeley"])
    print("Exact overlap with synthetic data:", summary["exact_overlap_synthetic"])
    print("Excluded other/unknown languages:", summary["excluded_other_languages"])
    print("Private candidates queued:", summary["private_pending_review"])
    print("Queue languages:", summary["by_language"])
    print("Queue source categories (unverified):", summary["by_source_scam_type_unverified"])
    print("Queue messages with basic privacy/URL flags:",
          summary["with_basic_privacy_or_url_flags"])
    print("Approved for publication: 0")
    print("Raw messages and queue never leave Git-ignored local staging.")
    print("STEP 7 PREPARED (NO HUMAN REVIEWS PERFORMED)")


if __name__ == "__main__":
    main()
