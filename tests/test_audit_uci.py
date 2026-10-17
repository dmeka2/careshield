from pathlib import Path
from runpy import run_path

module = run_path(
    str(Path(__file__).resolve().parents[1] / "scripts" / "audit_uci_candidates.py")
)
find_flags = module["find_flags"]
prepare_review = module["prepare_review"]


def fake_row(record_id, text):
    return {
        "id": record_id,
        "channel": "sms",
        "language": "und",
        "text": text,
        "label": "legitimate",
        "family": "none",
        "source": "uci_sms_spam_collection",
    }


def test_privacy_patterns_flag_private_information():
    assert "email" in find_flags("Write to person@example.com")
    assert "long_number" in find_flags("Call 312-555-0123 please")
    assert "sensitive_term" in find_flags("Your account number is needed")


def test_review_does_not_approve_any_message():
    review, summary = prepare_review([
        fake_row("001", "A routine message about lunch plans with classmates."),
        fake_row("002", "Hi Alice, please call 312-555-0123 when convenient."),
    ])
    assert len(review) == 2
    assert summary["pending_human_review"] == 2
    assert summary["approved"] == 0
    assert all(row["review_status"] == "pending" for row in review)
    assert all(row["reviewed_language"] == "" for row in review)
    assert all(row["reviewed_label"] == "" for row in review)
    assert summary["flagged_for_privacy_review"] == 1


def test_reject_duplicate_ids():
    import pytest
    with pytest.raises(ValueError, match="Duplicate"):
        prepare_review([fake_row("001", "Message one"), fake_row("001", "Message two")])
