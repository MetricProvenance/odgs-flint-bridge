# ODGS FLINT Bridge

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![ODGS](https://img.shields.io/badge/ODGS-v5.0.0-0055AA)](https://github.com/MetricProvenance/odgs-protocol)

The **Open Data Governance Standard (ODGS) FLINT Bridge** is an open-source institutional connector designed to unify the "Rules as Code" (Regels als Code) ecosystem. It bridges the gap between semantic legal ontology and executable, cryptographically verifiable governance.

This package natively translates **TNO's FLINT** (Formal Language for the Interpretation of Normative Texts) Linked Data into **ODGS Executable Rules**.

## The 5-Plane Architecture Synergy

This bridge perfectly aligns the Dutch ecosystem's legal parsing with the ODGS protocol's enforcement mechanisms:

1. **The Legislative Plane (TNO FLINT & Choppr):** TNO's open-source tools parse the human text of the law (e.g., from *wetten.overheid.nl*) and decompose it into a structured semantic truth (JSON-LD). This tells us *what the law means*.
2. **The Physical Plane (ODGS Protocol):** The [ODGS Execution Engine](https://github.com/MetricProvenance/odgs-protocol) takes this semantic truth and mechanically enforces it against live IT systems (Databricks, Snowflake, AI Agents). 

### Administrative Recusal (The "Hard Stop")
The core philosophy of ODGS is **Administrative Recusal**. If an AI agent or a legacy system attempts to process citizen data that does not perfectly conform to the rigorous FLINT definition mapped through this bridge, the ODGS Engine physically halts the pipeline to prevent "Black Box" liability. It generates an immutable cryptographic log citing the exact Dutch law that triggered the recusal.

## Usage Overview

The bridge performs three highly specific tasks:
1. **Parses the Semantic Truth:** Ingests the `flint:Fact` JSON-LD payload.
2. **Hashes the Law:** Creates an immutable SHA-256 seal of the source legislation (`flint:sourceReference`).
3. **Compiles the Executable Rule:** Translates the FLINT parameters (`LESS_THAN_OR_EQUAL`) into the ODGS runtime schema.

```bash
pip install -e .
```

---
### 🏢 Enterprise & Public Sector: EU AI Act Compliance
This open-source package connects your physical data infrastructure to the ODGS validation engine. However, if you are operating a **High-Risk AI System** and require strict liability indemnification under the **EU AI Act (Articles 10 & 12)**, you need cryptographic provenance.

**Metric Provenance** offers the commercial Enterprise Infrastructure for ODGS:
* **Certified Sovereign Packs:** Pre-compiled, cryptographically signed Ed25519 rule bundles for DORA, EU AI Act, and Basel.
* **The S-Cert Sovereign Registry:** An air-gapped Enterprise Certificate Authority that mints immutable, JWS-sealed audit logs.

👉 **[Discover the Sovereign CA Enterprise Node & Packs](https://platform.metricprovenance.com)**
---
