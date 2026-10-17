"""Audit a downloaded Mendeley SMS ZIP without publishing or approving SMS text.

The only generated artifact is a counts-only JSON report in Git-ignored staging.
Source labels (ham, spam, smishing) are not CareShield verified labels.
"""

import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "data/seed_corpus/raw/Dataset_5971.zip"
SUMMARY_PATH = ROOT / "data/seed_corpus/staging/mendeley_audit_summary.json"
UCI_CANDIDATES = ROOT / "data/seed_corpus/staging/uci_ham_candidates.csv"
SYNTHETIC_FILES = (
    ROOT / "data/seed_corpus/processed/healthcare_synthetic_week2.csv",
    ROOT / "data/seed_corpus/processed/week1_labeled_pilot.csv",
)
MAX_CSV_BYTES = 30_000_000
MAX_ZIP_MEMBERS = 100
MAX_DATA_ROWS = 100_000
EXPECTED_FIELDS = frozenset({"label", "text"})
SOURCE_LABELS = {"ham", "spam", "smishing"}

HEALTHCARE_PATTERN = re.compile(
    r"\b(?:health\s?care|health\s?plan|health\s?insurance|"
    r"medic(?:al|are|aid|ine|ation|ament(?:o|os)?)|"
    r"doctor|physician|clinic|hospital|pharmacy|pharmacist|"
    r"prescription|patient|diagnos(?:is|tic)|health\s?benefits|"
    r"laboratory|lab\s?results|insurance\s?coverage|"
    r"farmacia|receta(?:s)?|cl[ií]nica|m[eé]dico|"
    r"cobertura\s?(?:m[eé]dica|de salud)|seguro\s?(?:m[eé]dico|de salud))\b",
    re.IGNORECASE,
)
PRIVACY_PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", re.IGNORECASE),
    "url": re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE),
    "long_number": re.compile(r"(?<!\d)(?:\+?\d[\s().-]*){8,}(?!\d)"),
    "address_hint": re.compile(
        r"\b(?:street|st\.|avenue|ave\.|boulevard|blvd|postcode|"
        r"zip\s*code|apartment|apt\.|road|rd\.)\b",
        re.IGNORECASE,
    ),
    "sensitive_term": re.compile(
        r"\b(?:social\s+security|ssn|date\s+of\s+birth|"
        r"account\s*(?:number|no\.)|passport|bank\s+account|"
        r"medicare\s+(?:number|id)|patient\s+id)\b",
        re.IGNORECASE,
    ),
}


def normalize_header(value: str) -> str:
    """Canonicalize expected column titles, not message text."""
    return re.sub(r"[\s_\-]+", "", value.strip().lstrip("\ufeff").casefold())


def fingerprint(text: str) -> str:
    """Hash case/whitespace-normalized text; no cleartext is returned."""
    normalized = " ".join(text.casefold().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _csv_rows(raw: bytes) -> tuple[list[dict[str, str]], str]:
    """Parse a CSV member with the two expected fields, without printouts."""
    try:
        decoded = raw.decode("utf-8-sig")
        encoding = "utf-8-sig"
    except UnicodeDecodeError:
        decoded = raw.decode("cp1252")
        encoding = "cp1252"

    csv.field_size_limit(1_000_000)
    for delimiter in (",", ";", "\t"):
        reader = csv.DictReader(io.StringIO(decoded, newline=""), delimiter=delimiter)
        fields = reader.fieldnames or []
        titles = {normalize_header(field): field for field in fields if field}
        if not EXPECTED_FIELDS <= set(titles):
            continue
        if len(fields) > 50:
            raise ValueError("Unexpectedly many CSV columns")
        records = []
        for row in reader:
            if len(records) >= MAX_DATA_ROWS:
                raise ValueError("Unusually large dataset; refusing to process")
            label = row.get(titles["label"])
            message = row.get(titles["text"])
            if not isinstance(label, str) or not isinstance(message, str):
                # An incomplete/malformed record is counted as such later.
                records.append({"label": "", "text": ""})
            else:
                records.append({"label": label, "text": message})
        return records, encoding
    raise ValueError("No LABEL and TEXT columns found in the downloaded CSV")


def load_archive(zip_path: Path) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Safely read CSV bytes from ZIP; never extract files to disk."""
    if not zip_path.is_file():
        raise FileNotFoundError(f"Downloaded ZIP not found: {zip_path}")
    try:
        with ZipFile(zip_path) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ZIP_MEMBERS:
                raise ValueError("ZIP contains unexpectedly many files")
            candidates = [
                item for item in entries
                if not item.is_dir() and item.filename.casefold().endswith(".csv")
                and not item.filename.startswith("__MACOSX/")
            ]
            if not candidates:
                raise ValueError("ZIP has no CSV file; stop and share filenames only")
            preferred = [
                item for item in candidates
                if Path(item.filename).name.casefold() == "dataset_5971.csv"
            ]
            if len(preferred) == 1:
                chosen = preferred[0]
            elif len(candidates) == 1:
                chosen = candidates[0]
            else:
                raise ValueError("ZIP has multiple CSVs; cannot choose safely")
            if chosen.file_size > MAX_CSV_BYTES:
                raise ValueError("CSV is unexpectedly large; refusing to read")
            with archive.open(chosen) as handle:
                raw = handle.read(MAX_CSV_BYTES + 1)
            if len(raw) > MAX_CSV_BYTES:
                raise ValueError("CSV exceeds size limit")
            rows, encoding = _csv_rows(raw)
            metadata = {
                "csv_filename": Path(chosen.filename).name,
                "csv_encoding": encoding,
                "zip_sha256": hashlib.sha256(zip_path.read_bytes()).hexdigest(),
            }
    except BadZipFile as error:
        raise ValueError("Download is not a valid ZIP file") from error
    return rows, metadata


def existing_fingerprints(paths: tuple[Path, ...]) -> tuple[set[str], list[str]]:
    """Read known local sources without exposing text or altering files."""
    result = set()
    present = []
    for path in paths:
        if not path.is_file():
            continue
        present.append(path.name)
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if "text" not in (reader.fieldnames or []):
                raise ValueError(f"Unexpected text column in {path.name}")
            for row in reader:
                value = row.get("text")
                if isinstance(value, str) and value.strip():
                    result.add(fingerprint(value))
    return result, present


def build_summary(
    rows: list[dict[str, str]],
    metadata: dict[str, str],
    *,
    uci_fingerprints: set[str] | None = None,
    synthetic_fingerprints: set[str] | None = None,
    available_sources: list[str] | None = None,
) -> dict:
    """Return counts only. No messages, IDs, URLs, or row-level hashes."""
    uci_fingerprints = uci_fingerprints or set()
    synthetic_fingerprints = synthetic_fingerprints or set()
    labels = Counter()
    healthcare = Counter()
    flagged = Counter()
    duplicate_within = 0
    duplicate_uci = 0
    duplicate_synthetic = 0
    malformed = 0
    unrecognized_labels = 0
    seen = set()

    for row in rows:
        label = row["label"].strip().casefold()
        message = row["text"].strip()
        if not message or not label:
            malformed += 1
            continue
        if label not in SOURCE_LABELS:
            unrecognized_labels += 1
            label = "unknown"
        labels[label] += 1
        if HEALTHCARE_PATTERN.search(message):
            healthcare[label] += 1
        if any(pattern.search(message) for pattern in PRIVACY_PATTERNS.values()):
            flagged[label] += 1
        key = fingerprint(message)
        duplicate_within += key in seen
        seen.add(key)
        duplicate_uci += key in uci_fingerprints
        duplicate_synthetic += key in synthetic_fingerprints

    return {
        "source": "mendeley_sms_phishing_5971",
        "doi": "10.17632/f45bkkt8pr.1",
        "license": "CC BY 4.0 (attribution required)",
        **metadata,
        "total_csv_rows": len(rows),
        "nonempty_rows_by_source_label": dict(sorted(labels.items())),
        "unrecognized_source_label_count": unrecognized_labels,
        "malformed_or_empty_rows": malformed,
        "healthcare_keyword_candidates_by_source_label": dict(sorted(healthcare.items())),
        "any_basic_privacy_or_url_flag_by_source_label": dict(sorted(flagged.items())),
        "exact_normalized_duplicates_inside_mendeley": duplicate_within,
        "exact_overlap_with_staged_uci_candidates": duplicate_uci,
        "exact_overlap_with_published_synthetic_data": duplicate_synthetic,
        "comparison_files_present": sorted(available_sources or []),
        "approved_for_careshield": 0,
        "reminder": (
            "Counts only. Original source labels are unverified; smishing/spam "
            "do not automatically mean healthcare fraud. Healthcare keywords "
            "do not prove relevance. Basic privacy flags miss sensitive details. "
            "Review, redact and deduplicate before accepting any message."
        ),
    }


def save_summary(summary: dict, destination: Path) -> None:
    """Never overwrite a previously generated different private report."""
    rendered = (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if destination.exists():
        if destination.read_bytes() != rendered:
            raise RuntimeError("Existing private audit differs; inspect before replacing")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(rendered)


def main() -> None:
    rows, metadata = load_archive(ZIP_PATH)
    uci, uci_sources = existing_fingerprints((UCI_CANDIDATES,))
    synthetic, synthetic_sources = existing_fingerprints(SYNTHETIC_FILES)
    summary = build_summary(
        rows,
        metadata,
        uci_fingerprints=uci,
        synthetic_fingerprints=synthetic,
        available_sources=uci_sources + synthetic_sources,
    )
    save_summary(summary, SUMMARY_PATH)
    print("MENDELEY PRIVATE AUDIT - AGGREGATE COUNTS ONLY")
    print(f"CSV rows: {summary['total_csv_rows']}")
    print(f"Source labels: {summary['nonempty_rows_by_source_label']}")
    print("Healthcare keyword candidates:",
          summary["healthcare_keyword_candidates_by_source_label"])
    print(f"Basic privacy/URL flags: {summary['any_basic_privacy_or_url_flag_by_source_label']}")
    print(f"Exact internal duplicates: {summary['exact_normalized_duplicates_inside_mendeley']}")
    print("Exact overlaps with staged UCI candidates:",
          summary["exact_overlap_with_staged_uci_candidates"])
    print("Exact overlaps with synthetic data:",
          summary["exact_overlap_with_published_synthetic_data"])
    print(f"Invalid source label count: {summary['unrecognized_source_label_count']}")
    print(f"Malformed/empty rows: {summary['malformed_or_empty_rows']}")
    print("Approved for CareShield: 0 (human review required)")
    print(f"Private counts-only report: {SUMMARY_PATH}")
    print("No raw SMS text was written, displayed or uploaded by this audit.")


if __name__ == "__main__":
    main()
