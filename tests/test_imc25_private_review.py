"""Fictional-only tests for private IMC25 queue generation and review."""

import json
from pathlib import Path

import pytest

from scripts.prepare_imc25_healthcare_queue import (
    infer_fields,
    make_queue,
    match_type,
    normalize_column,
    write_new_json,
)
from scripts.review_imc25_healthcare import (
    counts,
    decision,
    load_queue,
    print_summary,
    save_queue,
)


def row(text, language="English", category="government"):
    """Fictional stand-in, never an actual SMS dataset entry."""
    return {"text": text, "source_category": category, "source_language": language}


def empty_hashes():
    return {"uci": set(), "mendeley": set(), "synthetic": set()}


def prepare(rows, hashes=None):
    return make_queue(
        rows,
        existing_hashes=hashes or empty_hashes(),
        source_sha256="f" * 64,
    )


def test_header_recognition():
    assert normalize_column(" Scam_Type ") == "scamtype"
    assert infer_fields(["SMS Text", "Language", "Scam_Type"]) == (
        "SMS Text", "Scam_Type", "Language"
    )


def test_missing_category_column_fails_closed():
    with pytest.raises(ValueError, match="scam_type"):
        infer_fields(["Text", "Language", "unverified"])


def test_narrow_and_broad_keyword_matches():
    assert match_type("The clinic appointment is Monday") == "direct"
    assert match_type("Your NHS account has a security update") == "broader_only"
    assert match_type("Your family picnic is Monday") == ""


def test_queue_includes_nhs_broad_only_as_pending():
    payload, summary = prepare([
        row("The clinic appointment is Monday"),
        row("Your NHS account has a security update", "Spanish", "others"),
    ])
    assert summary["broad_healthcare_keyword_matches"] == 2
    assert summary["direct_keyword_matches"] == 1
    assert summary["broader_only_keyword_matches"] == 1
    assert summary["private_pending_review"] == 2
    assert set(summary["by_language"]) == {"en", "es"}
    assert all(entry["review_status"] == "pending" for entry in payload["items"])
    assert all(entry["reviewed_label"] == "" for entry in payload["items"])


def test_other_languages_excluded():
    payload, summary = prepare([
        row("The doctor visit is Monday", "Portuguese"),
        row("The pharmacy visit is Tuesday", "Unknown"),
    ])
    assert not payload["items"]
    assert summary["excluded_other_languages"] == 2


def test_exact_duplicates_within_corpus():
    payload, summary = prepare([
        row("The doctor visit is Monday"),
        row("  THE DOCTOR  VISIT IS MONDAY "),
    ])
    assert len(payload["items"]) == 1
    assert summary["duplicate_candidate_rows"] == 1


def test_external_exact_duplicate_exclusions():
    from scripts.audit_mendeley_sms import fingerprint

    rows = [
        row("The clinic visited Alice today"),
        row("The doctor visited Alice today"),
        row("The hospital visited Alice today"),
        row("The pharmacy visited Alice today"),
    ]
    hashes = {
        "uci": {fingerprint(rows[0]["text"])},
        "mendeley": {fingerprint(rows[1]["text"])},
        "synthetic": {fingerprint(rows[2]["text"])},
    }
    payload, summary = prepare(rows, hashes)
    assert summary["exact_overlap_full_uci"] == 1
    assert summary["exact_overlap_mendeley"] == 1
    assert summary["exact_overlap_synthetic"] == 1
    assert len(payload["items"]) == 1


def test_privacy_or_url_flag_is_not_autoapproval():
    payload, summary = prepare([
        row("Your Medicare portal visit is at https://login.example"),
    ])
    assert summary["with_basic_privacy_or_url_flags"] == 1
    assert "url" in payload["items"][0]["privacy_flags"]
    assert payload["items"][0]["review_status"] == "pending"


def test_private_queue_creation_never_overwrites(tmp_path):
    path = tmp_path / "queue.json"
    write_new_json(path, {"test": 1})
    with pytest.raises(FileExistsError):
        write_new_json(path, {"test": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"test": 1}


def test_counts_only_summary_redacts_message(capsys):
    payload, _ = prepare([row("The clinic name is SECRET_FICTIONAL_TEXT")])
    print_summary(payload)
    out = capsys.readouterr().out
    assert "Pending: 1" in out
    assert "SECRET_FICTIONAL_TEXT" not in out


def test_reviewer_records_a_nonflagged_scam_as_provisional():
    payload, _ = prepare([row("The medical bill demands payment tonight")])
    item = payload["items"][0]
    assert "provisionally" in decision(item, "2")
    assert item["reviewed_label"] == "scam"
    assert item["reviewed_family"] == "medical_debt"
    assert item["review_status"] == "reviewed"


def test_reviewer_records_benign_as_provisional():
    payload, _ = prepare([row("Doctor appointment reminder on Monday")])
    item = payload["items"][0]
    decision(item, "l")
    assert item["reviewed_label"] == "legitimate"
    assert item["reviewed_family"] == "none"


def test_flagged_text_cannot_be_approved_without_review():
    payload, _ = prepare([row("Enter Medicare details at https://login.example")])
    item = payload["items"][0]
    result = decision(item, "4")
    assert "privacy" in result
    assert item["review_status"] == "hold"
    assert item["reviewed_label"] == ""


def test_hold_or_reject_do_not_assign_label():
    payload, _ = prepare([
        row("Your doctor called today"),
        row("Your hospital called yesterday"),
    ])
    first, second = payload["items"]
    decision(first, "h")
    decision(second, "r")
    assert counts(payload) == {"pending": 0, "reviewed": 0, "hold": 1, "rejected": 1}
    assert first["reviewed_label"] == second["reviewed_label"] == ""


def test_completed_review_cannot_be_overwritten():
    payload, _ = prepare([row("Your pharmacy called today")])
    item = payload["items"][0]
    decision(item, "r")
    with pytest.raises(ValueError, match="Only pending"):
        decision(item, "4")


def test_review_queue_atomic_save_and_read(tmp_path):
    path = tmp_path / "queue.json"
    payload, _ = prepare([row("Your doctor called today")])
    write_new_json(path, payload)
    decision(payload["items"][0], "h")
    save_queue(path, payload)
    loaded = load_queue(path)
    assert loaded["items"][0]["review_status"] == "hold"
    assert not Path(str(path) + ".tmp").exists()


def test_review_loader_rejects_corrupt_schema(tmp_path):
    path = tmp_path / "queue.json"
    path.write_text(json.dumps({"schema": "wrong", "items": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        load_queue(path)


def test_end_to_end_queue_stays_private_and_cannot_reset(tmp_path, monkeypatch, capsys):
    """Fake corpora exercise the full queue builder; no research text is included."""
    import csv
    import subprocess
    from zipfile import ZipFile

    from scripts import prepare_imc25_healthcare_queue as tool

    root = tmp_path / "repo"
    raw = root / "data/seed_corpus/raw"
    staging = root / "data/seed_corpus/staging"
    processed = root / "data/seed_corpus/processed"
    for folder in (raw, staging, processed):
        folder.mkdir(parents=True)
    (root / ".gitignore").write_text(
        "data/seed_corpus/raw/\ndata/seed_corpus/staging/\n", encoding="utf-8"
    )
    subprocess.run(["git", "init", "--quiet", str(root)], check=True)

    with ZipFile(raw / "uci_sms.zip", "w") as archive:
        archive.writestr("SMSSpamCollection", "ham\tYour hospital called about a visit\n")
    with ZipFile(raw / "Dataset_5971.zip", "w") as archive:
        archive.writestr(
            "Dataset_5971.csv", "LABEL,TEXT\nham,Your clinic contacted you today\n"
        )
    synthetic_columns = ["id", "channel", "language", "text", "label", "family", "source"]
    for filename in ("week1_labeled_pilot.csv", "healthcare_synthetic_week2.csv"):
        with (processed / filename).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=synthetic_columns)
            writer.writeheader()
            writer.writerow({
                "id": "fictional-1", "channel": "sms", "language": "en",
                "text": "Your pharmacy refill was scheduled", "label": "legitimate",
                "family": "none", "source": "fictional",
            })
    with (raw / "smishing_imc25.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["message", "language", "scam_type"])
        writer.writeheader()
        writer.writerows([
            {"message": "Your NHS SECRET_FICTIONAL notice is ready", "language": "English", "scam_type": "government"},
            {"message": "Your clinic contacted you today", "language": "English", "scam_type": "others"},
            {"message": "Your doctor visit is next week", "language": "Spanish", "scam_type": "others"},
            {"message": "Your hospital called about a visit", "language": "English", "scam_type": "others"},
            {"message": "Your pharmacy refill was scheduled", "language": "English", "scam_type": "others"},
        ])

    monkeypatch.setattr(tool, "ROOT", root)
    monkeypatch.setattr(tool, "SOURCE", raw / "smishing_imc25.csv")
    monkeypatch.setattr(tool, "UCI", raw / "uci_sms.zip")
    monkeypatch.setattr(tool, "MENDELEY", raw / "Dataset_5971.zip")
    monkeypatch.setattr(tool, "PILOT", processed / "week1_labeled_pilot.csv")
    monkeypatch.setattr(tool, "SYNTHETIC", processed / "healthcare_synthetic_week2.csv")
    monkeypatch.setattr(tool, "STAGING", staging)
    monkeypatch.setattr(tool, "QUEUE", staging / "imc25_healthcare_review_queue.json")
    monkeypatch.setattr(tool, "SUMMARY", staging / "imc25_healthcare_review_summary.json")

    summary = tool.run()
    assert summary["private_pending_review"] == 2
    assert summary["broad_healthcare_keyword_matches"] == 5
    assert summary["exact_overlap_full_uci"] == 1
    assert summary["exact_overlap_mendeley"] == 1
    assert summary["exact_overlap_synthetic"] == 1
    assert "SECRET_FICTIONAL" not in capsys.readouterr().out
    assert "SECRET_FICTIONAL" not in tool.SUMMARY.read_text(encoding="utf-8")
    payload = json.loads(tool.QUEUE.read_text(encoding="utf-8"))
    assert all(item["review_status"] == "pending" for item in payload["items"])
    with pytest.raises(FileExistsError):
        tool.run()
