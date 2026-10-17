# CareShield: Private IMC25 Healthcare Candidate Review

**Stage:** Week 2 corpus preparation, **NOT** release approval or final evaluation.

## Provenance

**Source:** Agarwal, Sharad; Papasavva, Antonis; Suarez-Tangil, Guillermo; and Vasek, Marie (2025), *Fishing for Smishing: Understanding SMS Phishing Infrastructure and Strategies by Mining Public User Reports*, IMC '25. DOI: https://doi.org/10.1145/3730567.3764431. Research dataset: https://github.com/reportsmishing/Smishing-Dataset-IMC25. License stated by that repository: CC BY 4.0 (attribution required).

Research scam categories such as `government`, `others`, and `banking` are **not** CareShield's five healthcare scam families. A reported smishing message can be unrelated to healthcare or may contain unverified allegations. No source annotation automatically becomes a verified CareShield label.

## Preparing a private shortlist

Run `uv run python scripts/prepare_imc25_healthcare_queue.py` once. The program:

- Reads the downloaded IMC25 CSV from `data/seed_corpus/raw/` locally.
- Combines the stricter healthcare matching used in Step 6 with the additional `NHS`, `Medicare`, `Medicaid`, `Obamacare`, and `healthcare` matching used in Step 5. This reconciles the earlier different candidate counts without silently excluding matches.
- Excludes non-English/Spanish examples from this review queue, while preserving the original source file unchanged.
- Deduplicates normalized exact text within IMC25 and against the **full** UCI dataset, the Mendeley dataset, and both published CareShield synthetic corpora. This does **not** detect every near-duplicate or translated variant.
- Flags obvious personal-information and URL indicators; a lack of flags does **not** prove that a message is safe or lacks patient information.
- Writes `imc25_healthcare_review_queue.json` and a **counts-only** summary under the Git-ignored `data/seed_corpus/staging/` directory. The private queue includes potentially sensitive research message text. It is intentionally NOT part of the GitHub commit.
- Never assigns `scam`, `legitimate`, or a healthcare family automatically. Existing queues are protected from overwrite.

**Important:** These keyword matches are only candidates. The tool does not prove that the content is healthcare-specific fraud or that source labels are accurate. A source labeled `wrong number`, `spam`, or `others` may be unsuitable. Never open or click links contained in any message.

## Private terminal review

`uv run python scripts/review_imc25_healthcare.py --summary` displays only progress counts.

`uv run python scripts/review_imc25_healthcare.py --batch-size 5` displays up to five *private* texts locally for human review. Never paste this terminal output into a chat or ticket or post screenshots showing the messages.

The review choices are:

| Key | Provisional manual judgment |
|---|---|
| `1` | Healthcare insurance/enrollment scam |
| `2` | Medical-debt scam |
| `3` | Prescription/pharmacy scam |
| `4` | Healthcare portal/credential phishing |
| `5` | Medicare, Medicaid, government, or provider impersonation |
| `L` | Clearly legitimate healthcare communication, with reliable context |
| `H` | Hold because evidence, language, privacy, or relevance is uncertain |
| `R` | Reject or irrelevant to CareShield |
| `Q` | Save completed work and quit |

These decisions are **provisional**. Records with simple privacy or URL flags are automatically put on hold if approval is attempted. Unflagged records may still contain personal information and must undergo a separate privacy review. The review tool backs up the queue privately before every session and saves each decision atomically.

## Before any data leaves the private staging area

1. Have a reviewer verify healthcare relevance, category, language, and rationale; resolve ambiguous cases rather than guessing.
2. Remove identifying names, contact details, URLs when appropriate, other personal information, and any PHI; document redaction, and do not change or visit malicious links.
3. Recheck licensing, source attribution, exact **and near** duplicates, source overlap, template family grouping, and conflicts.
4. Release only records passing an independent privacy/quality gate with approved source permissions; keep raw messages and review notes local.
5. Rebuild the *final* 70/15/15 split after obtaining at least 1,000 suitably labeled records and a representative independently authored healthcare scam and legitimate counterexample pool. Current provisional test data are development-only and not an unbiased holdout.

The review queue's provisional decisions must **not** be included in public data files or accuracy calculations merely because a reviewer selected a family.
