"""Evaluate provisional YAML rules on fictional development messages only.

This report is NOT a held-out test set, nor a Week 2 gate sign-off.
"""

import csv
import json
from collections import Counter
from pathlib import Path

from careshield.rules_engine import evaluate_redacted_text, load_rules

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "seed_corpus" / "processed"
OUTPUT = ROOT / "reports" / "week2_rules_coverage_dev.json"
MATRIX = ROOT / "reports" / "week2_rules_matrix_dev.csv"


def load_synthetic_rows() -> list[dict[str, str]]:
    paths = [DATA / "healthcare_synthetic_week2.csv", DATA / "week1_labeled_pilot.csv"]
    rows = []
    for path in paths:
        if not path.is_file():
            if path.name == "week1_labeled_pilot.csv":
                continue
            raise FileNotFoundError(f"Missing expected synthetic dataset: {path}")
        with path.open(newline="", encoding="utf-8-sig") as handle:
            rows.extend(csv.DictReader(handle))
    if not rows:
        raise ValueError("No synthetic rows found")
    return rows


def evaluate() -> dict:
    rules = load_rules()
    rows = load_synthetic_rows()
    seen_ids = set()
    totals = Counter()
    by_family = {}
    by_language = {}
    coverage = Counter()
    matrix_rows = []
    for row in rows:
        if row["id"] in seen_ids:
            raise ValueError("Duplicate synthetic corpus ID")
        seen_ids.add(row["id"])
        if row["source"] not in {"careshield_synthetic_week1", "careshield_synthetic_week2"}:
            raise ValueError("Refusing to evaluate public or private raw message data")
        hits = evaluate_redacted_text(row["text"], rules)
        flagged = bool(hits)
        is_scam = row["label"] == "scam"
        if row["label"] not in {"scam", "legitimate"}:
            raise ValueError("Unexpected label")
        totals["messages"] += 1
        totals["scam_total" if is_scam else "legitimate_total"] += 1
        if flagged:
            totals["scam_detected" if is_scam else "legitimate_flagged"] += 1
        family = row["family"] if is_scam else "none"
        bucket = by_family.setdefault(family, {"total": 0, "flagged": 0})
        bucket["total"] += 1
        bucket["flagged"] += int(flagged)
        language = row["language"]
        bucket = by_language.setdefault(language, {"total": 0, "scam": 0, "scam_detected": 0})
        bucket["total"] += 1
        bucket["scam"] += int(is_scam)
        bucket["scam_detected"] += int(is_scam and flagged)
        coverage.update(hit["rule_id"] for hit in hits)
        matrix_rows.append({
            "id": row["id"],
            "label": row["label"],
            "family": row["family"],
            "language": row["language"],
            "rule_ids": ";".join(hit["rule_id"] for hit in hits),
        })

    recall = totals["scam_detected"] / totals["scam_total"]
    false_positive_rate = totals["legitimate_flagged"] / totals["legitimate_total"]
    report = {
        "evaluation_status": "development_only_not_held_out",
        "warning": (
            "Template-generated fictional messages are closely correlated and are NOT an "
            "independent or frozen test set. Metrics must not be used as the Week 2 gate result. "
            "The input is synthetic and has no real personal data; apply Presidio redaction "
            "before evaluating any real message."
        ),
        "total_messages": totals["messages"],
        "scam_total": totals["scam_total"],
        "legitimate_total": totals["legitimate_total"],
        "scam_detected": totals["scam_detected"],
        "legitimate_flagged": totals["legitimate_flagged"],
        "provisional_recall": round(recall, 4),
        "provisional_false_positive_rate": round(false_positive_rate, 4),
        "active_rules": len(rules),
        "family_counts": by_family,
        "language_counts": by_language,
        "rules_fired_counts": dict(sorted(coverage.items())),
        "rules_never_fired": sorted(rule.id for rule in rules if not coverage[rule.id]),
    }
    return report, matrix_rows


def main() -> None:
    report, matrix_rows = evaluate()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with MATRIX.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["id", "label", "family", "language", "rule_ids"]
        )
        writer.writeheader()
        writer.writerows(matrix_rows)
    print("WEEK 2 RULES DEVELOPMENT CHECK (SYNTHETIC ONLY)")
    print(f"Rules loaded: {report['active_rules']}")
    print(f"Synthetic messages: {report['total_messages']}")
    print(f"Scam patterns caught: {report['scam_detected']} / {report['scam_total']}")
    print(f"Legitimate messages flagged: {report['legitimate_flagged']} / {report['legitimate_total']}")
    print(f"Preliminary recall: {report['provisional_recall']:.1%}")
    print(f"Preliminary false-positive rate: {report['provisional_false_positive_rate']:.1%}")
    print(f"Report (aggregate counts only): {OUTPUT}")
    print(f"Synthetic ID/rule coverage matrix (no text): {MATRIX}")
    print("NOT a held-out evaluation or a completed Week 2 gate.")


if __name__ == "__main__":
    main()
