"""Week 2, text-only, deterministic CareShield rules.

Privacy contract: callers must redact sensitive identifiers BEFORE calling
``evaluate_redacted_text``. The return value contains only rule metadata,
not the analyzed message, snippets, or matched spans.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_RULES_DIR = Path(__file__).resolve().parents[1] / "rules"
FAMILIES = {
    "insurance_enrollment", "medical_debt", "pharmacy", "phishing", "impersonation"
}
WEIGHT_POINTS = {"low": 1, "medium": 2, "high": 3}
PREFIX_FAMILY = {
    "ENR": "insurance_enrollment",
    "DEBT": "medical_debt",
    "RX": "pharmacy",
    "PHISH": "phishing",
    "IMP": "impersonation",
}


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    family: str
    weight: str
    pattern: re.Pattern[str]
    explanation_en: str
    explanation_es: str
    example_positive: str
    example_negative: str


def _required_string(value: Any, field: str, source: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid {field} in {source.name}")
    return value.strip()


def load_rules(directory: Path | None = None) -> list[Rule]:
    """Validate and compile the local, version-controlled YAML rules."""
    root = Path(directory) if directory is not None else DEFAULT_RULES_DIR
    paths = sorted(root.glob("*.yaml"))
    if not paths:
        raise ValueError(f"No YAML rules found under {root}")

    loaded: list[Rule] = []
    seen_ids: set[str] = set()

    for path in paths:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict) or not isinstance(data.get("rules"), list):
            raise TypeError(f"Invalid YAML rule collection in {path.name}")
        for item in data["rules"]:
            if not isinstance(item, dict):
                raise TypeError(f"Rule must be a mapping in {path.name}")
            rule_id = _required_string(item.get("id"), "id", path)
            prefix = rule_id.split("-", maxsplit=1)[0]
            if not re.fullmatch(r"(?:ENR|DEBT|RX|PHISH|IMP)-\d{2}", rule_id):
                raise ValueError(f"Invalid rule ID {rule_id}")
            if rule_id in seen_ids:
                raise ValueError(f"Duplicate rule ID {rule_id}")
            family = _required_string(item.get("family"), "family", path)
            if family not in FAMILIES or PREFIX_FAMILY[prefix] != family:
                raise ValueError(f"Unknown or mismatched family for {rule_id}")
            weight = _required_string(item.get("weight"), "weight", path)
            if weight not in WEIGHT_POINTS:
                raise ValueError(f"Unexpected weight for {rule_id}: {weight}")
            pattern_text = _required_string(item.get("pattern"), "pattern", path)
            if len(pattern_text) > 1000:
                raise ValueError(f"Pattern too long in {rule_id}")
            try:
                pattern = re.compile(pattern_text, re.IGNORECASE | re.DOTALL)
            except re.error as error:
                raise ValueError(f"Invalid regex in {rule_id}") from error

            explanation = item.get("explanations")
            examples = item.get("test_cases")
            if not isinstance(explanation, dict) or not isinstance(examples, dict):
                raise TypeError(f"Missing explanation or examples for {rule_id}")
            loaded.append(Rule(
                id=rule_id,
                name=_required_string(item.get("name"), "name", path),
                family=family,
                weight=weight,
                pattern=pattern,
                explanation_en=_required_string(explanation.get("en"), "English", path),
                explanation_es=_required_string(explanation.get("es"), "Spanish", path),
                example_positive=_required_string(examples.get("positive"), "positive", path),
                example_negative=_required_string(examples.get("negative"), "negative", path),
            ))
            seen_ids.add(rule_id)

    return sorted(loaded, key=lambda rule: rule.id)


def evaluate_redacted_text(
    redacted_text: str,
    rules: list[Rule] | None = None,
) -> list[dict[str, str | int]]:
    """Return matching rule metadata only; never return original input text.

    Caller MUST redact identifiers first. This function does not perform PII
    detection, domain verification, risk scoring, or external API requests.
    """
    if not isinstance(redacted_text, str):
        raise TypeError("redacted_text must be a string")
    if len(redacted_text) > 10000:
        raise ValueError("Message length exceeds 10,000 characters")
    if not redacted_text.strip():
        return []
    active_rules = rules if rules is not None else load_rules()
    results = []
    for rule in active_rules:
        if rule.pattern.search(redacted_text):
            results.append({
                "rule_id": rule.id,
                "family": rule.family,
                "weight": rule.weight,
                "weight_points": WEIGHT_POINTS[rule.weight],
                "explanation_en": rule.explanation_en,
                "explanation_es": rule.explanation_es,
            })
    return sorted(results, key=lambda hit: (-hit["weight_points"], hit["rule_id"]))
