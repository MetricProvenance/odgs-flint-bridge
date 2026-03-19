# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
adhering to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-03-14

### 🚀 Initial Release
- TNO FLINT (Regels als Code) → ODGS Executable Rules transformation engine.
- Parser (`parser.py`): Deserializes FLINT JSON-LD acts, facts, duties, and violations.
- Compiler (`compiler.py`): Compiles FLINT semantic acts into ODGS enforcement rule schemas.
- Sample input: `sample_flint.json` (Zorgtoeslag eligibility check).
- Requires `odgs>=5.0.0` — exclusively targets the v5 polymorphic execution engine.
- Apache 2.0 — open-source companion to the commercial FLINT bridge.
