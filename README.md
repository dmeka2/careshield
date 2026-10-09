# CareShield
### Healthcare Scam and Access Defender

**A privacy-focused healthcare scam detection project**

CareShield is a cybersecurity project developed as part of a fellowship with the Chicago Education Advocacy Cooperative (ChiEAC).

The goal is to help people identify suspicious healthcare-related emails and text messages, understand potential scam indicators, and receive clear guidance on what to do next.

The project focuses on explainable threat detection, security automation, privacy protection, and accessible English and Spanish guidance.

---

## Project Overview

CareShield is designed to identify five major categories of healthcare scams:

1. Fake Insurance Enrollment and Marketplace Impersonation
2. Medical Debt Collection Scams
3. Prescription and Pharmacy Scams
4. Phishing and Credential Harvesting
5. Medicare, Medicaid, HHS-OIG, and Healthcare Provider Impersonation

The planned application will analyze submitted messages, identify suspicious patterns, calculate a risk score, and generate understandable explanations and recommended actions.

---

## Current Development Status

**Milestone 1: Foundations — October 5–9, 2026**

The initial project foundation includes:

- A healthcare scam taxonomy with 40 detection indicators
- English and Spanish explanations for all indicators
- Low, Medium, and High indicator weights
- Privacy-by-design architecture documentation
- Pydantic input validation for messages, uploads, and questionnaires
- 20 synthetic healthcare messages in CSV and JSON formats
- Automated testing using pytest
- Code quality checks using Ruff
- GitHub Actions continuous integration
- Python 3.12 development environment

**Current testing results:**

- 8 automated tests passing
- Ruff linting checks passing
- GitHub Actions CI passing

The detection engine, machine-learning models, web application, and analytics dashboards will be developed in later milestones.

---

## Planned Technology Stack

### Programming and Data Processing

- Python 3.12
- pandas
- Pydantic
- spaCy
- scikit-learn

### Security and Threat Intelligence

- Microsoft Presidio
- OpenPhish
- URLhaus
- PhishTank
- RDAP Domain Intelligence
- CMS NPI Registry
- Splunk Enterprise

### Application and Analytics

- FastAPI
- Streamlit
- DuckDB
- Plotly

### Development and Deployment

- Git and GitHub
- GitHub Actions
- pytest
- Ruff
- uv
- Docker

---

## Project Documentation

The following project documents are available:

- [Healthcare Scam Taxonomy](docs/taxonomy.md) — Detection categories, 40 indicators, bilingual explanations, and severity weights.
- [Privacy Design](docs/privacy-design.md) — Data flow, sensitive-information handling, and privacy safeguards.
- [Input Validation Module](careshield/ingest.py) — Pydantic schemas for supported input methods.
- [Validation Tests](tests/test_ingest.py) — Automated input validation tests.
- [Synthetic Sample CSV](data/samples/sample.csv) — 20 fictional healthcare messages.
- [Synthetic Sample JSON](data/samples/sample.json) — JSON version of the sample dataset.

---

## Getting Started

### Prerequisites

- Python 3.12
- uv
- Git

### Install Dependencies

Run `uv sync` from the project directory.

### Run Automated Tests

Run `uv run pytest` to execute the test suite.

### Run Code Quality Checks

Run `uv run ruff check .` to check Python code quality.

---

## Privacy and Security

CareShield follows a privacy-by-design approach.

The planned application is designed to:

- Process message contents in memory.
- Avoid storing sensitive healthcare or personal information.
- Redact personally identifiable information using Microsoft Presidio.
- Send only approved de-identified events to organizational analytics systems.
- Protect sensitive information through data minimization.
- Avoid exposing API keys or credentials in the public repository.

Privacy protections will be implemented and validated during later milestones.

---

## Project Roadmap

| Week | Development Focus |
|---|---|
| Week 1 | Project foundation, taxonomy, privacy design, and input validation |
| Week 2 | Synthetic datasets and detection rules engine |
| Week 3 | Threat-intelligence enrichment and domain analysis |
| Week 4 | NLP classification, risk scoring, and explanations |
| Week 5 | Streamlit web application, FastAPI, and bilingual action plans |
| Week 6 | Splunk dashboards, alerts, and privacy auditing |
| Week 7 | Deployment, documentation, and final presentation |

---

## Sponsoring Organization

This project is being developed as part of a fellowship with the **Chicago Education Advocacy Cooperative (ChiEAC)**.

**Project:** CareShield — Healthcare Scam and Access Defender

**Sponsoring Organization:** Chicago Education Advocacy Cooperative

---

## License

This project is released under the [MIT License](LICENSE).

---

## Disclaimer

CareShield is an educational cybersecurity project.

Its future detection results are not a substitute for professional medical, financial, legal, or insurance advice. Users should independently verify suspicious communications through official organizational contact channels.
