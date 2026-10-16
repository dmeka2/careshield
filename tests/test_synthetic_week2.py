import csv
import json
from collections import Counter
from pathlib import Path
from runpy import run_path

build_rows = run_path(
    str(Path(__file__).resolve().parents[1] / "scripts" / "generate_week2_healthcare.py")
)["build_rows"]


def test_synthetic_counts_and_languages():
    rows = build_rows()
    assert len(rows) == 420
    assert Counter(r["label"] for r in rows) == {
        "scam": 300,
        "legitimate": 120,
    }
    assert Counter(r["language"] for r in rows) == {"en": 210, "es": 210}
    assert Counter(r["channel"] for r in rows) == {"sms": 210, "email": 210}


def test_synthetic_five_families_and_legitimate_examples():
    rows = build_rows()
    scam = [r for r in rows if r["label"] == "scam"]
    good = [r for r in rows if r["label"] == "legitimate"]
    assert set(r["family"] for r in scam) == {
        "insurance_enrollment", "medical_debt", "pharmacy",
        "phishing", "impersonation",
    }
    assert all(count == 60 for count in Counter(r["family"] for r in scam).values())
    assert all(r["family"] == "none" for r in good)


def test_synthetic_unique_and_safe():
    rows = build_rows()
    assert len({r["id"] for r in rows}) == len(rows)
    assert len({(r["channel"], r["text"]) for r in rows}) == len(rows)
    assert all(1 <= len(r["text"]) <= 10000 for r in rows)
    assert all(r["source"] == "careshield_synthetic_week2" for r in rows)
    assert all("{" not in r["text"] for r in rows)


def test_generated_csv_and_json_match():
    folder = Path(__file__).resolve().parents[1] / "data" / "seed_corpus" / "processed"
    with (folder / "healthcare_synthetic_week2.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        csv_rows = list(csv.DictReader(handle))
    json_rows = json.loads(
        (folder / "healthcare_synthetic_week2.json").read_text(encoding="utf-8")
    )
    assert csv_rows == json_rows == build_rows()
