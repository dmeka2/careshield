"""Week 2 rules: one positive and one negative test for every YAML rule."""

import json
from pathlib import Path

import pytest

from careshield.rules_engine import evaluate_redacted_text, load_rules

RULES = load_rules()


def test_rules_count_and_metadata():
    assert 30 <= len(RULES) <= 40
    assert len({rule.id for rule in RULES}) == len(RULES)
    assert len({rule.family for rule in RULES}) == 5
    assert all(rule.explanation_en and rule.explanation_es for rule in RULES)


@pytest.mark.parametrize("rule", RULES, ids=lambda rule: rule.id)
def test_each_rule_matches_its_positive_example(rule):
    hits = evaluate_redacted_text(rule.example_positive, RULES)
    assert rule.id in {hit["rule_id"] for hit in hits}


@pytest.mark.parametrize("rule", RULES, ids=lambda rule: rule.id)
def test_each_rule_rejects_its_negative_example(rule):
    hits = evaluate_redacted_text(rule.example_negative, RULES)
    assert rule.id not in {hit["rule_id"] for hit in hits}


def test_no_message_text_is_returned():
    message = "Your health plan is approved. Send your Social Security number now."
    hits = evaluate_redacted_text(message, RULES)
    assert hits
    assert message not in json.dumps(hits)
    assert all("text" not in hit and "match" not in hit for hit in hits)


def test_blank_and_long_input_handling():
    assert evaluate_redacted_text("", RULES) == []
    with pytest.raises(ValueError, match="10,000"):
        evaluate_redacted_text("a" * 10001, RULES)


def test_invalid_yaml_is_rejected(tmp_path: Path):
    (tmp_path / "broken.yaml").write_text("rules: [broken]", encoding="utf-8")
    with pytest.raises(TypeError):
        load_rules(tmp_path)


def test_mundane_appointment_not_flagged():
    message = "Your appointment is confirmed for Thursday at 9 AM. Call your usual clinic."
    assert evaluate_redacted_text(message, RULES) == []
