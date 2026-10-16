# CareShield — Week 2 Labeling Guide

**Version:** 1.0
**Date:** October 16, 2026
**Purpose:** Consistent scam and legitimate labels for CareShield training and evaluation.

## 1. Dataset Schema

Every accepted record must have these fields:

| Field | Allowed value |
|---|---|
| id | Unique, non-patient identifier |
| channel | sms or email |
| language | en or es |
| text | Message body, maximum 10,000 characters |
| label | scam or legitimate |
| family | insurance_enrollment, medical_debt, pharmacy, phishing, impersonation, or none |
| source | Documented corpus or synthetic-data source |

A record labeled `legitimate` must have `family = none`.

A record labeled `scam` must be assigned one primary scam family.

The source identifies provenance. It does not establish that a message is trustworthy.

## 2. Core Labeling Rules

### Scam

Assign `scam` when the message contains sufficient evidence of a deceptive or fraudulent healthcare-related request.

Examples of strong evidence include:

- Requests for Medicare, Medicaid, Social Security, banking, password, or one-time authentication information through an unverified channel.
- Impersonation of a government program, insurer, clinic, or pharmacy to obtain sensitive information.
- Demands for gift cards, cryptocurrency, or suspicious transfers to settle alleged healthcare debt.
- False threats of arrest or loss of benefits used to force immediate payment or disclosure.
- Offers of prescription medicines without a required prescription.
- Deceptive login instructions directing a recipient to an unverified destination.

A message should not be classified as a scam solely because it contains urgency, a link, an unfamiliar sender, or promotional language.

### Legitimate

Assign `legitimate` when reliable context or the controlled synthetic scenario establishes that the communication is genuine or benign.

Examples include:

- Ordinary appointment reminders and cancellations.
- Pharmacy pickup or refill notifications.
- Explanation of Benefits availability notices.
- Routine insurance or billing updates.
- Instructions to contact a known clinic through an independently verified channel.

Legitimate communications may discuss bills, deadlines, links, or insurance eligibility. These features alone do not establish fraud.

### Uncertain or Conflicting Evidence

If evidence is insufficient or conflicting, place the record in a **private review queue** rather than guessing.

Do not include unresolved records in training, validation, testing, or reported accuracy calculations.

The final labeled corpus uses only `scam` and `legitimate`.

## 3. Primary Scam Family

Choose the most specific family supported by the message's central fraudulent action.

| Family | Primary focus |
|---|---|
| insurance_enrollment | Fake enrollment, coverage confirmation, or Marketplace offers |
| medical_debt | Fraudulent debt collection, payment threats, or debt-validation deception |
| pharmacy | Prescription, medication-sale, or pharmacy-delivery scams |
| phishing | Credential theft through portals, messages, or fake account notifications |
| impersonation | Medicare, Medicaid, HHS, government, or provider identity deception |

If several families are plausible, choose the family that best describes the central lure. Document secondary indicators separately when needed.

For example, a fake laboratory portal requesting a password generally belongs to `phishing`; a fake Medicare card replacement requesting an identifier generally belongs to `impersonation`.

## 4. Ambiguous Cases

### Legitimate reminder containing a shortened link

A shortened URL does not automatically prove fraud.

Check whether the sender, destination, and claimed organization can be independently verified. If the destination cannot be established safely, place the example in the review queue. Do not infer legitimacy or fraud from the short link alone.

### Real medical debt collector using rude language

An unpleasant tone is not sufficient evidence of a scam.

Consider whether the debt can be validated, whether the collector provides appropriate information, and whether the payment instructions are suspicious. Threats of arrest, gift-card demands, or refusal to verify an alleged debt are stronger indicators. If authenticity is unresolved, request review.

### Legal but pushy Medicare Advantage marketing

Aggressive marketing is not necessarily fraudulent.

A deadline, promotional offer, or persistent sales language does not by itself establish a scam. Look for false government affiliation, deceptive identity claims, unusual payments, or requests for sensitive credentials. Put uncertain examples into review instead of treating all Medicare marketing as fraud.

### Routine patient portal message

A normal notice directing patients to their established portal can be legitimate. A message demanding that the recipient reply with a password or one-time code is suspicious.

When the identity of a linked portal cannot be independently established, label the record as needing review.

### Public SMS spam and ham labels

A source label of `spam` is not equivalent to confirmed healthcare fraud. Likewise, a source label of `ham` does not automatically guarantee that a message is safe or suitable.

Review public-data records for labeling accuracy, language, source consistency, and privacy before admitting them to the final corpus.

## 5. Language and Channel

Identify the message's primary language as English (`en`) or Spanish (`es`). Keep uncertain-language records out of the finalized dataset until reviewed.

Record the actual message channel as `sms` or `email`.

For generated email examples, subject text may be included in the message body for this initial normalized schema.

Do not change the fraud label merely because a message is written in Spanish.

## 6. Privacy and Data Quality

Use fictional examples wherever possible. Never copy identifiable victim or patient messages into public files.

Before admitting public records:

1. Check for names, phone numbers, addresses, account identifiers, and other personal information.
2. Redact sensitive details or exclude the record.
3. Preserve the source attribution and license.
4. Check for exact and near-duplicate messages.
5. Review the assigned label and language.
6. Document exclusions and unresolved cases.

The reserved `.example` domain is used in CareShield's synthetic messages. Its presence alone must never determine whether the message is labeled scam or legitimate.

## 7. Training, Validation, and Test Integrity

The target split is approximately 70 percent training, 15 percent validation, and 15 percent testing.

Stratify where practical by label, family, language, and channel while preserving sufficient examples in each group.

Synthetic records generated from the same base template must remain in the same split, even when the language, channel, or variable values differ.

The Week 2 synthetic IDs encode template numbers such as `t01`. Group by family or legitimate theme and template number, ignoring language, channel, and variation.

Also group exact and near-duplicate public messages. Do not allow substantially equivalent content in both training and testing.

Freeze the final split files using SHA-256 hashes recorded in `docs/model-card.md`. Never tune detection rules using the frozen test set.

## 8. Evaluation and Review

For the rules engine:

**Recall** = detected healthcare scams / total reviewed healthcare scams.

**False-positive rate** = legitimate counterexamples flagged as scams / total reviewed legitimate counterexamples.

Week 2 targets:

- Recall at least 0.80 on the healthcare scam seed set.
- False-positive rate at most 0.10 on legitimate counterexamples.
- Positive and negative automated tests for every detection rule.

Report the number of examples, language coverage, family coverage, and known data limitations with every evaluation.

Template-generated examples are useful for initial testing but cannot independently demonstrate performance on real-world messages.

## 9. Labeling Review Checklist

Before approving a record, confirm:

- The message contains no unapproved personal information.
- The source and usage rights are documented.
- The chosen label has a defensible rationale.
- The primary family is correct.
- The language and channel are correct.
- The example is not an unreviewed duplicate.
- Related templates will not cross dataset splits.

Records that fail these checks remain excluded until reviewed.
