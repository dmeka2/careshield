"""Build an auditable *provisional* group-safe split of Week 2 synthetic data.

Only the 420 generated Week 2 rows are eligible. The Week 1 pilot and all
private/unreviewed UCI messages are intentionally excluded. This is NOT the
final frozen 1,000-message evaluation split.
"""

import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/seed_corpus/processed/healthcare_synthetic_week2.csv"
OUTPUT = ROOT / "data/seed_corpus/provisional_split"
FIELDS = ("id", "channel", "language", "text", "label", "family", "source")
SOURCE = "careshield_synthetic_week2"
SEED = "careshield-week2-provisional-v1"
SPLITS = ("train", "validation", "test")
SCAM_TOPICS = (
    "insurance_enrollment", "medical_debt", "pharmacy", "phishing", "impersonation",
)
LEGIT_TOPICS = ("appointment", "pharmacy", "insurance", "billing", "lab_results")
ID_PATTERN = re.compile(
    r"^syn-(?P<kind>scam|legit)-(?P<topic>[a-z_]+)-"
    r"(?P<language>en|es)-(?P<channel>sms|email)-"
    r"t(?P<template>\d{2})-v(?P<variation>\d{2})$"
)
EMAIL_SUBJECT = re.compile(r"\A(?:Subject|Asunto):[^\n]*\n\n", re.IGNORECASE)


def sha256(data: bytes) -> str:
    """Calculate a portable SHA-256 hex digest."""
    return hashlib.sha256(data).hexdigest()


def stable_order(items: list[str]) -> list[str]:
    """Order group IDs deterministically, independent of input file order."""
    return sorted(items, key=lambda key: sha256(f"{SEED}:{key}".encode()))


def group_key(row: dict[str, str]) -> str:
    """Group all variations, languages and channels of a base template."""
    match = ID_PATTERN.fullmatch(row["id"])
    if match is None:
        raise ValueError(f"Not a recognized Week 2 synthetic ID: {row['id']!r}")

    kind = match["kind"]
    topic = match["topic"]
    expected_label = "scam" if kind == "scam" else "legitimate"
    topics = SCAM_TOPICS if kind == "scam" else LEGIT_TOPICS
    expected_family = topic if kind == "scam" else "none"
    if topic not in topics:
        raise ValueError(f"Unexpected synthetic topic for {row['id']!r}")
    if row["label"] != expected_label or row["family"] != expected_family:
        raise ValueError(f"Label/family mismatch for {row['id']!r}")
    if row["language"] != match["language"] or row["channel"] != match["channel"]:
        raise ValueError(f"Language/channel mismatch for {row['id']!r}")
    if row["source"] != SOURCE:
        raise ValueError(f"Unapproved source for {row['id']!r}; UCI and pilot excluded")
    if not row["text"].strip() or len(row["text"]) > 10000:
        raise ValueError(f"Invalid text for {row['id']!r}")
    return f"{kind}:{topic}:t{match['template']}"


def load_rows(path: Path = INPUT) -> list[dict[str, str]]:
    """Read and strictly validate the known synthetic dataset."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError("Unexpected CSV columns; refusing to split")
        rows = list(reader)
    # Git/Windows may change line endings inside quoted email messages.
    # Canonicalize these before hashing so checkout settings cannot change
    # the logical split or its record-level fingerprint.
    for row in rows:
        if not isinstance(row.get("text"), str):
            raise TypeError("Each record must contain a text string")
        row["text"] = row["text"].replace("\r\n", "\n").replace("\r", "\n")
    if len(rows) != 420:
        raise ValueError(f"Expected 420 generated Week 2 messages, got {len(rows)}")
    if any(set(row) != set(FIELDS) for row in rows):
        raise ValueError("CSV row has missing or extra columns")

    ids = [row["id"] for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate message IDs in input")
    if Counter(row["label"] for row in rows) != {"scam": 300, "legitimate": 120}:
        raise ValueError("Unexpected synthetic label distribution")

    groups = defaultdict(list)
    bodies = {}
    for row in rows:
        key = group_key(row)
        groups[key].append(row)
        # Email subject lines are not independent new messages.
        body = EMAIL_SUBJECT.sub("", row["text"].strip()).casefold()
        body = " ".join(body.split())
        previous = bodies.setdefault((row["language"], body), key)
        if previous != key:
            raise ValueError(f"Duplicate text crosses template groups: {previous}, {key}")

    if len(groups) != 40:
        raise ValueError(f"Expected 40 independent base templates, got {len(groups)}")
    for key, members in groups.items():
        kind = key.split(":", maxsplit=1)[0]
        count_per_lang_chan = 3 if kind == "scam" else 2
        if len(members) != count_per_lang_chan * 4:
            raise ValueError(f"Wrong number of template variants for {key}")
        combos = Counter((row["language"], row["channel"]) for row in members)
        expected = {(lang, channel): count_per_lang_chan
                    for lang in ("en", "es") for channel in ("sms", "email")}
        if combos != expected:
            raise ValueError(f"Missing language/channel variants for {key}")

    # Check obvious near duplicates between *different* base templates, within
    # the same language. This is an extra guard, not a semantic leak guarantee.
    for language in ("en", "es"):
        examples = [
            (key, EMAIL_SUBJECT.sub("", row["text"]).casefold().strip())
            for key, members in groups.items()
            for row in members
            if row["language"] == language and row["channel"] == "sms"
        ]
        for i, (first_key, first_body) in enumerate(examples):
            for second_key, second_body in examples[i + 1:]:
                if first_key == second_key:
                    continue
                if SequenceMatcher(None, first_body, second_body).ratio() >= 0.92:
                    raise ValueError(
                        f"Near-duplicate templates need review: {first_key}, {second_key}"
                    )

    return sorted(rows, key=lambda row: row["id"])


def allocate_groups(rows: list[dict[str, str]]) -> dict[str, str]:
    """Assign base templates to approximately 70/15/15 splits.

    Quotas are chosen to keep both labels represented in each split and to
    spread examples across five scam families and five benign themes.
    """
    group_assignment = {}
    scam_topics = stable_order(list(SCAM_TOPICS))
    legit_topics = stable_order(list(LEGIT_TOPICS))

    for kind, topics in (("scam", scam_topics), ("legit", legit_topics)):
        for topic_index, topic in enumerate(topics):
            keys = stable_order(sorted({
                group_key(row) for row in rows
                if row["id"].startswith(f"syn-{kind}-{topic}-")
            }))
            if kind == "scam":
                # 25 groups => 17 train, 4 validation, 4 test.
                quotas = ((3, 1, 1) if topic_index < 3 else
                          (4, 1, 0) if topic_index == 3 else (4, 0, 1))
            else:
                # 15 groups => 11 train, 2 validation, 2 test.
                quotas = ((2, 1, 0) if topic_index < 2 else
                          (2, 0, 1) if topic_index < 4 else (3, 0, 0))
            if len(keys) != sum(quotas):
                raise ValueError(f"Unexpected template-group count for {kind}:{topic}")
            start = 0
            for split, quantity in zip(SPLITS, quotas, strict=True):
                for key in keys[start:start + quantity]:
                    group_assignment[key] = split
                start += quantity
    if len(group_assignment) != 40:
        raise ValueError("Some base templates were not allocated")
    return group_assignment


def prepare(rows: list[dict[str, str]]) -> tuple[dict[str, bytes], dict]:
    """Render portable CSV bytes and a manifest without touching the disk."""
    rows = sorted(rows, key=lambda row: row["id"])
    assignments = allocate_groups(rows)
    partitioned = {split: [] for split in SPLITS}
    for row in rows:
        partitioned[assignments[group_key(row)]].append(row)

    expected_counts = {"train": 292, "validation": 64, "test": 64}
    if {name: len(records) for name, records in partitioned.items()} != expected_counts:
        raise ValueError("Incorrect split sizes")

    files = {}
    file_hashes = {}
    summary = {}
    for split in SPLITS:
        records = sorted(partitioned[split], key=lambda row: row["id"])
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
        raw = stream.getvalue().encode("utf-8")
        name = f"{split}.csv"
        files[name] = raw
        file_hashes[name] = sha256(raw)
        summary[split] = {
            "total": len(records),
            "by_label": dict(sorted(Counter(row["label"] for row in records).items())),
            "by_language": dict(sorted(Counter(row["language"] for row in records).items())),
            "by_channel": dict(sorted(Counter(row["channel"] for row in records).items())),
            "by_family": dict(sorted(Counter(row["family"] for row in records).items())),
            "base_template_groups": len({group_key(row) for row in records}),
        }

    # Hash normalized logical records, independent of Windows CSV line endings.
    logical_rows = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    manifest = {
        "version": "provisional-v1",
        "status": "EXPERIMENTAL - NOT FINAL/FROZEN TEST DATA",
        "eligible_source": SOURCE,
        "excluded": ["Week 1 synthetic pilot (possible template overlap)",
                     "private/unreviewed UCI SMS candidates"],
        "seed": SEED,
        "source_records_sha256": sha256(logical_rows.encode("utf-8")),
        "file_sha256": file_hashes,
        "split_summary": summary,
        "template_group_assignment": dict(sorted(assignments.items())),
        "warning": "No final Week 2 benchmark claim; same-generation synthetic data only.",
    }
    files["manifest.json"] = (
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    return files, manifest


def write_outputs(files: dict[str, bytes], output_dir: Path) -> None:
    """Avoid silently overwriting a modified provisional dataset."""
    for name, content in files.items():
        path = output_dir / name
        if path.exists() and path.read_bytes() != content:
            raise RuntimeError(f"Existing split differs: {path}; review before replacing")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        path = output_dir / name
        if not path.exists():
            path.write_bytes(content)


def main() -> None:
    rows = load_rows(INPUT)
    files, manifest = prepare(rows)
    write_outputs(files, OUTPUT)
    print("CARE SHIELD: PROVISIONAL SYNTHETIC SPLIT ONLY")
    for split in SPLITS:
        stats = manifest["split_summary"][split]
        print(f"  {split}: {stats['total']} messages, {stats['base_template_groups']} groups")
    print("Total: 420 generated messages (20 Week 1 pilot and all UCI excluded)")
    print("Template variants stay together across languages, channels and amounts.")
    print(f"Manifest with SHA-256 hashes: {OUTPUT / 'manifest.json'}")
    print("NOT a final frozen holdout or Week 2 accuracy benchmark.")


if __name__ == "__main__":
    main()
