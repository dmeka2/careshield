# CareShield Week 2 — Deterministic Rules Engine

**Status:** Provisional, text-only prototype. Do not use for real clinical or fraud decisions.

The `rules/` folder contains **33 active YAML pattern rules** from the Week 1 taxonomy, across all five healthcare scam families. Every active rule has a severity weight, an English explanation, a Spanish explanation, and explicit positive/negative test cases. The engine returns **only rule metadata**: never the submitted message or matching text spans.

## Text processing and privacy

For **real** messages, callers must validate inputs and redact personal and health identifiers **before** calling `evaluate_redacted_text()`. This function does not perform redaction itself. The Week 2 development evaluation deliberately uses only CareShield's fictional synthetic examples. No public UCI review-queue data or victim messages are read by the report script.

```python
from careshield.rules_engine import evaluate_redacted_text

# Only pass text after the caller has performed PII/PHI redaction.
rule_hits = evaluate_redacted_text(redacted_message)
```

The engine makes no external network calls. A matched pattern is only a warning sign, **not proof of fraud**. Weight points (low = 1, medium = 2, high = 3) are provisional identifiers for sorting evidence, **not** a risk score.

## Deferred until verification/enrichment

Seven indicators require trustworthy external context and are not active text-only rules:

- `ENR-03`: Government URL mismatch / lookalike analysis
- `ENR-08`: Authenticity of government-style branding
- `DEBT-05`: Provider contact information mismatch
- `RX-03`: Licensed pharmacy verification
- `PHISH-01`: Unrelated or lookalike patient portal domain
- `PHISH-03`: Sender/display-name domain mismatch
- `IMP-07`: Provider or insurer contact-information mismatch

They are still defined in `docs/taxonomy.md`. A future enrichment stage will implement them using verified domains, sender metadata, and other evidence. We deliberately avoid guessing that a domain or organization is fake from message text alone.

## Test and development evaluation

Run:

```powershell
uv run ruff check .
uv run pytest
uv run python scripts/evaluate_week2_rules.py
```

All 33 rules have parameterized positive and negative pytest cases (66 per-rule assertions, plus API/invariant tests). `reports/week2_rules_coverage_dev.json` contains **aggregate counts only** with breakdowns by family, language, and rule. `reports/week2_rules_matrix_dev.csv` maps **fictional message IDs** to fired rule IDs without message text. No original messages or snippets are written to either report.

The 420 Week 2 generated examples (and optional 20 Week 1 pilot examples) have shared templates. These development metrics **cannot** establish production recall, false-positive performance, or the Week 2 benchmark. Before final assessment, finish the reviewed corpus, perform a template-grouped, stratified 70/15/15 split, freeze it with SHA-256 hashes, and evaluate with an untouched test set. Never tune rules using the held-out test set.
