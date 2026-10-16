# Week 2 Healthcare Synthetic Corpus — Provenance and Review

## Scope and format

The files `data/seed_corpus/processed/healthcare_synthetic_week2.csv` and
`healthcare_synthetic_week2.json` contain **420 original fictional messages**:

- **300 scam examples:** 60 for each of the five scam families.
- **120 legitimate examples:** appointments, pharmacies, insurance, billing, and lab results.
- **210 English and 210 Spanish** messages (50% Spanish).
- **210 SMS and 210 email** messages.
- Columns: `id`, `channel`, `language`, `text`, `label`, `family`, and `source`.

These are **draft synthetic examples**, not collected victim messages, and are
separate from the Week 1 pilot dataset. No real patient details or live scam
URLs are included. Any domains appearing in the examples use the reserved
`.example` domain, not functioning external destinations.

## Scam patterns used as inspiration

The text was written for CareShield, not copied from victim reports or the
sources below. The scenarios adapt publicly described *patterns*:

- Fake insurance enrollment and government-site impersonation:
  [FTC, September 28, 2026](https://consumer.ftc.gov/consumer-alerts/2026/09/what-know-ahead-open-enrollment-avoid-health-insurance-scams).
- Medical debt collection threats and lack of debt validation:
  [FTC, February 2026](https://consumer.ftc.gov/consumer-alerts/2026/02/debt-collection-know-your-rights-avoid-scams).
- Prescription drugs without a valid prescription and unsafe pharmacy sales:
  [FDA, Considering an Online Pharmacy](https://www.fda.gov/drugs/besaferx-your-source-online-pharmacy-information/considering-online-pharmacy).
- Requests for Medicare information and fake card renewals:
  [FTC, September 2025](https://consumer.ftc.gov/consumer-alerts/2025/09/medicare-open-enrollment-season-learn-how-protect-yourself-scams).
- Fraudulent offers for free medical equipment and testing:
  [HHS-OIG, Urinary Catheter Scams](https://www.oig.hhs.gov/fraud/consumer-alerts/consumer-alert-catheter-scam/).

Source links checked on **October 16, 2026**.

## Quality limitations — important

1. **Template-derived examples are correlated.** Different variations do not
   count as independent evidence that a classifier generalizes. A strong final
   evaluation requires diverse independently authored examples and an external
   or carefully isolated healthcare test set.
2. Before any train/validation/test split, group rows with the same **family or
   legitimate theme and template number**, regardless of language, channel, or
   variation. The template identifier is encoded in each synthetic row's `id`.
   Avoid putting variants of the same base template into different splits.
3. Have humans review the English/Spanish wording, scam/legitimate distinctions,
   and confusing borderline cases before accepting final labels.
4. Reserved `.example` links are used in both scam and legitimate examples so
   domain appearance alone should not determine a scam label.
5. The existing 600 UCI SMS records are still **unreviewed local candidates**
   and are not included in these 420 rows or claimed as cleared dataset records.

## License and reproducibility

- Original text: CareShield-created, project MIT License.
- Generator: `scripts/generate_week2_healthcare.py`.
- Automated checks: `tests/test_synthetic_week2.py`.
- Re-run the generator to obtain deterministic CSV and JSON outputs.
- Do not import, publish, or log real patient, victim, or private contact data.
