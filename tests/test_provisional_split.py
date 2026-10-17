"""Verification for the provisional template-group-aware synthetic split."""

import csv
import hashlib
import json
import runpy
from collections import Counter
from pathlib import Path

import pytest

# Load the sibling script without relying on pytest/import-path settings.
SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/prepare_provisional_split.py"
SPLIT = runpy.run_path(str(SCRIPT_PATH))
FIELDS = SPLIT["FIELDS"]
INPUT = SPLIT["INPUT"]
SPLITS = SPLIT["SPLITS"]
SOURCE = SPLIT["SOURCE"]
allocate_groups = SPLIT["allocate_groups"]
group_key = SPLIT["group_key"]
load_rows = SPLIT["load_rows"]
prepare = SPLIT["prepare"]
write_outputs = SPLIT["write_outputs"]


@pytest.fixture(scope="module")
def synthetic_rows():
    """Use the committed fictional Week 2 CSV, not any private review data."""
    return load_rows(INPUT)


def test_only_420_published_week2_synthetic_rows(synthetic_rows):
    assert len(synthetic_rows) == 420
    assert {row["source"] for row in synthetic_rows} == {SOURCE}
    assert Counter(row["label"] for row in synthetic_rows) == {
        "scam": 300, "legitimate": 120,
    }


def test_groups_combine_languages_channels_and_variations(synthetic_rows):
    sample = next(row for row in synthetic_rows if row["id"].endswith("-en-sms-t01-v01"))
    parts = sample["id"].split("-en-sms-")
    other = dict(sample)
    other["id"] = f"{parts[0]}-es-email-t01-v02"
    other["language"] = "es"
    other["channel"] = "email"
    assert group_key(sample) == group_key(other)


def test_every_base_template_stays_in_one_split(synthetic_rows):
    assignments = allocate_groups(synthetic_rows)
    assert len(assignments) == 40
    for row in synthetic_rows:
        assert assignments[group_key(row)] in SPLITS
    assert len([key for key in assignments if key.startswith("scam:")]) == 25
    assert len([key for key in assignments if key.startswith("legit:")]) == 15


def test_split_counts_labels_and_languages(synthetic_rows):
    _, manifest = prepare(synthetic_rows)
    summary = manifest["split_summary"]
    assert {name: summary[name]["total"] for name in SPLITS} == {
        "train": 292, "validation": 64, "test": 64,
    }
    assert {name: summary[name]["by_label"] for name in SPLITS} == {
        "train": {"scam": 204, "legitimate": 88},
        "validation": {"scam": 48, "legitimate": 16},
        "test": {"scam": 48, "legitimate": 16},
    }
    for name in SPLITS:
        assert set(summary[name]["by_language"]) == {"en", "es"}
        assert set(summary[name]["by_channel"]) == {"sms", "email"}


def test_reproducible_when_input_order_changes(synthetic_rows):
    first_files, first_manifest = prepare(synthetic_rows)
    second_files, second_manifest = prepare(list(reversed(synthetic_rows)))
    assert first_files == second_files
    assert first_manifest == second_manifest


def test_each_output_sha256_matches_manifest(synthetic_rows):
    files, manifest = prepare(synthetic_rows)
    for name in ("train.csv", "validation.csv", "test.csv"):
        assert hashlib.sha256(files[name]).hexdigest() == manifest["file_sha256"][name]
        assert files[name].decode("utf-8").startswith(",".join(FIELDS) + "\n")
    assert json.loads(files["manifest.json"]) == manifest


def test_invalid_source_cannot_be_admitted(synthetic_rows):
    row = dict(synthetic_rows[0], source="uci_sms")
    with pytest.raises(ValueError, match="Unapproved source"):
        group_key(row)


def test_invalid_label_and_id_are_rejected(synthetic_rows):
    incorrect_label = (
        "scam" if synthetic_rows[0]["label"] == "legitimate" else "legitimate"
    )
    with pytest.raises(ValueError, match="Label/family mismatch"):
        group_key(dict(synthetic_rows[0], label=incorrect_label))
    with pytest.raises(ValueError, match="Not a recognized"):
        group_key(dict(synthetic_rows[0], id="uci-private-message"))


def test_rejects_identical_body_in_different_template_groups(synthetic_rows, tmp_path):
    rows = [dict(row) for row in synthetic_rows]
    first = rows[0]
    second = next(
        row for row in rows
        if group_key(row) != group_key(first) and row["language"] == first["language"]
        and row["channel"] == first["channel"]
    )
    second["text"] = first["text"]
    altered = tmp_path / "altered.csv"
    with altered.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="Duplicate text crosses template groups"):
        load_rows(altered)


def test_changed_output_will_not_be_overwritten(synthetic_rows, tmp_path):
    files, _ = prepare(synthetic_rows)
    write_outputs(files, tmp_path)
    write_outputs(files, tmp_path)
    modified = tmp_path / "test.csv"
    modified.write_bytes(b"do not overwrite")
    with pytest.raises(RuntimeError, match="Existing split differs"):
        write_outputs(files, tmp_path)
    assert modified.read_bytes() == b"do not overwrite"


def test_output_files_only_use_synthetic_source(synthetic_rows):
    files, _ = prepare(synthetic_rows)
    for name in ("train.csv", "validation.csv", "test.csv"):
        records = list(csv.DictReader(files[name].decode("utf-8").splitlines(keepends=True)))
        assert all(record["source"] == SOURCE for record in records)


def test_provisional_manifest_is_explicit_about_limits(synthetic_rows):
    _, manifest = prepare(synthetic_rows)
    assert "NOT FINAL" in manifest["status"]
    assert "UCI" in " ".join(manifest["excluded"])
    assert "pilot" in " ".join(manifest["excluded"])
