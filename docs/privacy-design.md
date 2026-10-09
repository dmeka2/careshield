# CareShield — Privacy Design

**Project:** CareShield: Healthcare Scam and Access Defender  

**Sponsoring Organization:** Chicago Education Advocacy Cooperative (ChiEAC)  

**Status:** Week 1 — Initial Privacy Design

## 1. Purpose

CareShield analyzes suspicious healthcare emails and text messages while protecting users' personal and healthcare information.

The system follows a privacy-by-design approach. Raw messages are processed in memory and are not stored in application databases, logs, analytics events, or external services.

## 2. Data Flow

The CareShield processing pipeline follows this sequence:

**User Input → Input Validation → Text Normalization and URL Extraction → PII Redaction → Rules Engine and NLP Analysis → Threat Intelligence Enrichment → Risk Scoring → User Results → Optional De-identified Analytics Event**

The pipeline handles data as follows:

1. **Input validation:** Pydantic validates pasted messages, CSV/JSON uploads, and questionnaire responses. Messages exceeding 10,000 characters and uploads exceeding 500 rows or 5 MB are rejected.
2. **In-memory processing:** Original messages remain temporarily in application memory. They are used only for analysis and for displaying evidence to the submitting user.
3. **Sensitive information redaction:** Microsoft Presidio detects sensitive information. Custom recognizers identify Medicare Beneficiary Identifiers and National Provider Identifier numbers. Sensitive identifiers are removed or replaced before text is logged, cached, or emitted.
4. **Scam detection:** Detection rules and NLP classification operate on redacted content to identify suspicious patterns.
5. **Threat intelligence:** Only the necessary domain or sanitized URL is sent to services such as OpenPhish, URLhaus, PhishTank, and RDAP. Full message bodies are never sent. Threat-intelligence lookup results may be cached for 24 hours.
6. **Results:** The user receives a risk score, scam classification, explanations, and an action plan. The original message is not persisted.
7. **Analytics:** The public edition emits no analytics events unless an organization key is configured. Organization-enabled deployments send only approved de-identified events to Splunk or DuckDB.

## 3. Approved Analytics Event Schema

Only these 12 fields may leave the application for organizational analytics:

| Field | Description |
|---|---|
| `event_id` | Random UUID identifying an analysis event |
| `org_id` | Organization identifier |
| `ts_hour` | Timestamp rounded to the hour |
| `channel` | Email, SMS, or questionnaire |
| `family` | Detected scam family |
| `score_band` | Low, elevated, high, or critical |
| `rule_ids` | Identifiers of triggered detection rules |
| `enrich_flags` | Threat-intelligence indicator flags |
| `registered_domain` | Public registered domain identified during analysis |
| `impersonated_brand` | Brand or agency category, if identified |
| `sender_hash` | SHA-256 hash using a per-organization salt |
| `lang` | English or Spanish |

Raw numeric risk scores are not included in analytics events.

## 4. Prohibited Data

The following must never be stored in analytics events, application logs, or persistent databases:

- Raw message bodies, subjects, or email headers
- Names, addresses, and dates of birth
- Social Security numbers
- Medicare or Medicaid identifiers
- Account numbers and payment information
- Original sender email addresses or telephone numbers
- User IP addresses
- Raw risk scores

## 5. Privacy Controls

**Data minimization:** Only information needed for detection is processed.

**No persistent message storage:** The public application processes message content in memory without saving it.

**PII redaction:** Presidio and custom healthcare recognizers protect sensitive information before logging or event emission.

**Safe logging:** Application logs exclude raw request bodies, sensitive identifiers, and unsanitized exception data.

**Sender privacy:** Sender identifiers are hashed with a per-organization salt before organizational event emission.

**Dashboard protection:** Dashboard groups containing fewer than five events are suppressed to reduce re-identification risk.

**External services:** Threat-intelligence providers receive only information required for URL or domain verification, never full messages.

**Secrets management:** API keys, tokens, and salts are stored outside the Git repository using environment variables or secure deployment secrets.

## 6. Privacy Verification

During Week 6, CareShield will undergo a privacy audit using 50 synthetic messages containing fake names, Social Security numbers, Medicare identifiers, dates of birth, addresses, and account numbers.

The audit will inspect generated Splunk events and application logs.

**Acceptance criterion:** All 50 test cases must produce zero prohibited personal or healthcare information in emitted events and logs.

## 7. User Safety Disclaimer

CareShield is an educational tool, not medical, legal, financial, or insurance advice.

Its assessments may be incorrect. Users should verify suspicious messages by contacting the relevant organization through an independently verified official phone number or website.

## 8. Change Control

Any addition to the approved analytics event schema requires updating this privacy design and repeating the privacy audit before deployment.

This document defines the intended privacy architecture. Implementation and audit evidence will be completed and verified in later project milestones.
