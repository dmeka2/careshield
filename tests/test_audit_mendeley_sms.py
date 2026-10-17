"""Fictional-only tests for the private Mendeley SMS audit."""

import csv
import io
import json
import runpy
from pathlib import Path
from zipfile import ZipFile

import pytest

# Load the file directly, independent of how pytest configures sys.path.
SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/audit_mendeley_sms.py"
AUDIT = runpy.run_path(str(SCRIPT_PATH))
_csv_rows = AUDIT["_csv_rows"]
build_summary = AUDIT["build_summary"]
existing_fingerprints = AUDIT["existing_fingerprints"]
fingerprint = AUDIT["fingerprint"]
load_archive = AUDIT["load_archive"]
save_summary = AUDIT["save_summary"]


PRIVATE_FAKE_TEXT = "SECRET_FAKE_NAME123 health insurance appointment at my clinic"


def _make_zip(path: Path, rows: list[dict[str, str]], *, delimiter: str = ",") -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=["LABEL", "TEXT", "URL", "EMAIL", "PHONE"],
                            delimiter=delimiter, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({"LABEL": row["label"], "TEXT": row["text"],
                         "URL": "NO", "EMAIL": "NO", "PHONE": "NO"})
    with ZipFile(path, "w") as archive:
        archive.writestr("Dataset_5971.csv", stream.getvalue().encode("utf-8-sig"))
        archive.writestr("readme.txt", "Not message data")


def test_read_zip_without_extraction(tmp_path):
    path = tmp_path / "Dataset_5971.zip"
    _make_zip(path, [{"label": "Ham", "text": "Regular appointment reminder"}])
    rows, metadata = load_archive(path)
    assert rows == [{"label": "Ham", "text": "Regular appointment reminder"}]
    assert metadata["csv_filename"] == "Dataset_5971.csv"
    assert len(metadata["zip_sha256"]) == 64
    assert not (tmp_path / "Dataset_5971.csv").exists()


def test_semicolon_csv_is_supported():
    rows, encoding = _csv_rows(b"LABEL;TEXT\nHam;Appointment at regular clinic\n")
    assert rows == [{"label": "Ham", "text": "Appointment at regular clinic"}]
    assert encoding == "utf-8-sig"


def test_malformed_headers_fail_safely(tmp_path):
    path = tmp_path / "bad.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("Dataset_5971.csv", "CLASS,MESSAGE\nham,Private message\n")
    with pytest.raises(ValueError, match="LABEL and TEXT"):
        load_archive(path)


def test_multiple_csv_files_fail_instead_of_guessing(tmp_path):
    path = tmp_path / "many.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("a.csv", "LABEL,TEXT\nHam,one\n")
        archive.writestr("b.csv", "LABEL,TEXT\nHam,two\n")
    with pytest.raises(ValueError, match="multiple CSV"):
        load_archive(path)


def test_missing_zip_fails(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        load_archive(tmp_path / "missing.zip")


def test_source_labels_remain_unverified():
    rows = [
        {"label": "Ham", "text": PRIVATE_FAKE_TEXT},
        {"label": "Smishing", "text": "Your fake health insurance was cancelled"},
        {"label": "Spam", "text": "Buy our garden plants"},
    ]
    report = build_summary(rows, {"csv_filename": "test.csv"})
    assert report["nonempty_rows_by_source_label"] == {
        "ham": 1, "smishing": 1, "spam": 1,
    }
    assert report["approved_for_careshield"] == 0
    assert report["healthcare_keyword_candidates_by_source_label"] == {
        "ham": 1, "smishing": 1,
    }
    assert PRIVATE_FAKE_TEXT not in json.dumps(report)


def test_duplicate_and_source_overlap_counts():
    rows = [
        {"label": "Ham", "text": "Medical appointment today"},
        {"label": "Ham", "text": " medical   appointment   today "},
        {"label": "Smishing", "text": "Pharmacy bank account update"},
    ]
    report = build_summary(
        rows, {"csv_filename": "test.csv"},
        uci_fingerprints={fingerprint("Medical appointment today")},
        synthetic_fingerprints={fingerprint("Pharmacy bank account update")},
    )
    assert report["exact_normalized_duplicates_inside_mendeley"] == 1
    assert report["exact_overlap_with_staged_uci_candidates"] == 2
    assert report["exact_overlap_with_published_synthetic_data"] == 1
    assert report["any_basic_privacy_or_url_flag_by_source_label"] == {"smishing": 1}


def test_invalid_labels_and_empty_rows_are_not_approved():
    report = build_summary(
        [{"label": "", "text": ""},
         {"label": PRIVATE_FAKE_TEXT, "text": "Hello"}],
        {"csv_filename": "test.csv"},
    )
    assert report["malformed_or_empty_rows"] == 1
    assert report["unrecognized_source_label_count"] == 1
    assert PRIVATE_FAKE_TEXT not in json.dumps(report)
    assert report["approved_for_careshield"] == 0


def test_private_summary_does_not_write_text(tmp_path):
    report = build_summary(
        [{"label": "ham", "text": PRIVATE_FAKE_TEXT}],
        {"csv_filename": "dataset.csv"},
    )
    path = tmp_path / "mendeley_audit_summary.json"
    save_summary(report, path)
    save_summary(report, path)
    content = path.read_text(encoding="utf-8")
    assert PRIVATE_FAKE_TEXT not in content
    assert json.loads(content)["approved_for_careshield"] == 0


def test_differing_summary_never_overwrites(tmp_path):
    path = tmp_path / "mendeley_audit_summary.json"
    save_summary({"row_count": 1}, path)
    with pytest.raises(RuntimeError, match="differs"):
        save_summary({"row_count": 2}, path)
    assert json.loads(path.read_text()) == {"row_count": 1}


def test_local_overlap_sources_read_only(tmp_path):
    path = tmp_path / "uci_ham_candidates.csv"
    path.write_text("id,text\nex1,One test message\n", encoding="utf-8")
    digests, names = existing_fingerprints((path, tmp_path / "none.csv"))
    assert digests == {fingerprint("one test message")}
    assert names == ["uci_ham_candidates.csv"]


def test_missing_text_column_rejected(tmp_path):
    path = tmp_path / "uci_ham_candidates.csv"
    path.write_text("id,body\nex1,hello\n", encoding="utf-8")
    with pytest.raises(ValueError, match="text column"):
        existing_fingerprints((path,))
