# CareShield — Provisional Week 2 Synthetic Split

**Status: DEVELOPMENT ONLY. Not the final frozen train/validation/test split.**

## Purpose

Build a reproducible 70/15/15-style demonstration of template-group-aware
splitting before admitting reviewed public messages to the 1,000-message corpus.
This stage is a **data pipeline check**, not an independent model evaluation.

## Scope and exclusions

The input is exactly `data/seed_corpus/processed/healthcare_synthetic_week2.csv`
(420 controlled fictional messages). It contains 300 synthetic scam messages and
120 synthetic legitimate messages. Its English and Spanish versions, email and
SMS formats, and variable substitutions are **not independent observations**.

The program specifically does **not** read or publish:

- the 20 Week 1 pilot messages, which might overlap templates and must be
  checked separately before inclusion;
- any UCI SMS candidates or manual-review decisions in the private
  `data/seed_corpus/staging/` directory;
- identifiable patient or victim communications.

## Leakage controls

Week 2 IDs include source template markers of the form `t01`, `t02`, etc.
For example, `syn-scam-pharmacy-en-sms-t01-v01` and
`syn-scam-pharmacy-es-email-t01-v02` must share a split. Grouping uses
`scam:pharmacy:t01` and ignores language, channel and substituted amounts.
Legitimate themes receive their own groups, e.g. `legit:appointment:t01`.

The script also rejects exact duplicate message bodies across distinct template
groups and uses a high-similarity text check to flag obvious cross-group near
duplicates. These checks do not prove semantic independence or cover all possible
leakage. The synthetic generator still shares vocabulary, subjects, and writing
style across templates.

Assignments are SHA-256-seeded and deterministic; running the script with
unchanged records produces the same files. Its outputs are protected against
silent overwrites if an existing output file was modified.

## Provisional counts

| Split | Messages | Scam | Legitimate | Base template groups | Share |
|---|---:|---:|---:|---:|---:|
| Train | 292 | 204 | 88 | 28 | 69.5% |
| Validation | 64 | 48 | 16 | 6 | 15.2% |
| Test | 64 | 48 | 16 | 6 | 15.2% |
| Total | 420 | 300 | 120 | 40 | 100% |

Each split has equal English/Spanish counts and equal SMS/email counts because
each base template group contains all four language/channel combinations.

**Important limitation:** There are only five scam base templates per family.
The group-integrity requirement means the validation split is missing the
`medical_debt` family, and the test split is missing the `phishing` family.
This is unsuitable as the final representative held-out test corpus. The final
1,000+ corpus must include additional independent examples to support adequate
coverage of every healthcare scam family and legitimate counterexamples.

## Files

Run `uv run python scripts/prepare_provisional_split.py`. It creates:

- `data/seed_corpus/provisional_split/train.csv`
- `data/seed_corpus/provisional_split/validation.csv`
- `data/seed_corpus/provisional_split/test.csv`
- `data/seed_corpus/provisional_split/manifest.json`

The CSV files contain **fictional messages only**. The manifest stores split
counts, source-record SHA-256, SHA-256 for each output CSV, and every template
group's assignment. Hashing is for **reproducibility of this provisional run**;
it does **not** constitute the final Week 2 freeze of a reviewed corpus.

The generated `test.csv` must not be used to tune or select the current rules
engine. The rules were already developed using examples from this generator;
therefore this provisional test partition is **not unseen evaluation data**.

## Before the final Week 2 split

1. Finish privacy screening, redaction and human label review for all public
   material. Only approved records should enter the final dataset.
2. Obtain additional **independent** licensed or authored examples. The current
   approved counts do not meet the 1,000-message gate.
3. Deduplicate across **all** sources, including Week 1 pilot examples and
   approved public SMS messages. Group semantic and source/template variants.
4. Re-stratify to ensure each healthcare family, English/Spanish, SMS/email and
   legitimate examples are represented appropriately in validation and test.
5. Review the split membership, then freeze the final dataset and SHA-256
   hashes in the model card. Do not tune rules on the frozen final test split.
6. Only then run and report independent healthcare recall and legitimate
   false-positive rate, with counts and limitations.
