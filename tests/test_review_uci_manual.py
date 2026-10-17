"""Tests for manually reviewed UCI queue decisions and safe persistence."""

import csv
from pathlib import Path
from runpy import run_path

import pytest

module = run_path(
    str(Path(__file__).resolve().parents[1] / "scripts" / "review_uci_manual.py")
)
apply_decision = module["apply_decision"]
count_statuses = module["count_statuses"]
load_queue = module["load_queue"]
save_queue = module["save_queue"]


def fake_row(record_id="uci-test"):
    return {
        "id": record_id,
        "channel": "sms",
        "original_language": "und",
        "text": "Fictional routine lunch note with no identifying details.",
        "provisional_label": "legitimate",
        "family": "none",
        "source": "uci_sms_spam_collection",
        "privacy_flags": "",
        "review_status": "pending",
        "reviewed_label": "",
        "reviewed_language": "",
        "review_notes": "",
    }


def test_approval_requires_explicit_decision():
    row = fake_row()
    assert row["review_status"] == "pending"
    apply_decision(row, "a")
    assert row["review_status"] == "approved"
    assert row["reviewed_label"] == "legitimate"
    assert row["reviewed_language"] == "en"
    with pytest.raises(ValueError, match="Only pending"):
        apply_decision(row, "a")


def test_hold_reject_and_invalid_decisions():
    holding = fake_row("uci-hold")
    rejected = fake_row("uci-reject")
    invalid = fake_row("uci-invalid")
    apply_decision(holding, "h")
    apply_decision(rejected, "r")
    with pytest.raises(ValueError, match="Unrecognized"):
        apply_decision(invalid, "x")
    assert count_statuses([holding, rejected, invalid]) == {
        "approved": 0, "rejected": 1, "hold": 1, "pending": 1,
    }


def test_atomic_save_and_reload(tmp_path):
    path = tmp_path / "private.csv"
    row = fake_row()
    fields = list(row)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)
    loaded, existing_fields = load_queue(path)
    assert existing_fields == fields
    apply_decision(loaded[0], "b")
    save_queue(path, loaded, existing_fields)
    updated, _ = load_queue(path)
    assert updated[0]["reviewed_language"] == "es"
    assert updated[0]["review_status"] == "approved"
