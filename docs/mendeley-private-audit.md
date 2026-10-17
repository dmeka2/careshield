# CareShield — Mendeley SMS Private Audit (Week 2)

**Status: Inspection only. No messages are approved or publicly released.**

## Source and license

Mishra, Sandhya, and Soni, Devpriya (2022), *SMS PHISHING DATASET FOR MACHINE LEARNING AND PATTERN RECOGNITION*, Mendeley Data, Version 1, DOI: [10.17632/f45bkkt8pr.1](https://doi.org/10.17632/f45bkkt8pr.1), **CC BY 4.0**. The authors report 5,971 messages in three **source** categories: ham, spam, and smishing.

Source labels **do not establish** whether an SMS is a healthcare scam, a trustworthy message, or suitable for publication. Some source examples may originate from earlier SMS corpora, including UCI. Do not count them as independent simply because they have another source name.

## What this script does

Run `uv run python scripts/audit_mendeley_sms.py` after downloading `Dataset_5971.zip` into `data/seed_corpus/raw/`.

- Reads a CSV **inside the ZIP without extracting** any message text to another file.
- Counts source labels, malformed rows, and simple healthcare-keyword candidates.
- Counts messages with simple privacy/URL warning patterns. Absence of a flag is **not proof of privacy**.
- Counts normalized exact duplicates **within** Mendeley and exact matches against the local staged UCI candidate CSV (if present) and both published synthetic source CSVs (if present).
- Saves only an aggregate JSON summary in the **Git-ignored private** `data/seed_corpus/staging/` directory.
- Never prints, copies to published folders, labels as CareShield scams, or commits raw SMS text.
- Refuses to overwrite a different previous audit summary without a deliberate review.

The exact-overlap check uses normalized whitespace and case. It **does not** find all near duplicates, translations, or templated variants. The UCI comparison covers only the *locally staged 600 candidates*; it is not a comparison against all 5,574 UCI messages.

## Limitations and human review

Simple healthcare-keyword matches are prioritization hints, not verified healthcare relevance. URLs, phone-like numbers, and address words are review flags, not complete PII identification. Source ham/spam/smishing classes **must not** be directly converted to CareShield `legitimate`/`scam` labels. Non-healthcare smishing should not be misrepresented as healthcare fraud.

Next, develop a privacy-safe review queue for candidates with useful healthcare context, independently verify or redact messages, document attribution, deduplicate across full sources, and keep unresolved records out of final splits and accuracy reports. Never treat the provisional synthetic test split as final unbiased evaluation data.
