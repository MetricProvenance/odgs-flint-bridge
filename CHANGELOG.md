# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
adhering to [Semantic Versioning](https://semver.org/).

## [0.3.0] - 2026-03-19

### ✨ Added — Full FLINT Type Coverage

The bridge now supports all six core TNO FLINT ontology types, not just `flint:Fact` and `flint:Duty`:

| FLINT Type | ODGS Rule Shape | Severity |
|---|---|---|
| `flint:Fact` | Logical constraint | `HARD_STOP` |
| `flint:Duty` | Temporal obligation | `HARD_STOP` + `effective_from`/`effective_to` |
| `flint:Act` | Actor-validation rule | `ACT_CONSTRAINT` |
| `flint:Source` | Provenance anchor | `METADATA_ONLY` |
| `flint:Reference` | Cross-reference link | `LOG_ONLY` |
| `flint:Violation` | Contrary-to-duty breach | `HARD_STOP` + `non_conformance_message` |

- **`FlintParser.parse()`** — new dispatcher entry point; auto-routes by `@type`. `parse_fact()` kept for backward compatibility.

- **Expanded operator vocabulary:** `NOT_EQUALS`, `IN`, `NOT_IN`, `IS_NULL`, `IS_NOT_NULL` all supported in addition to the existing five.

- **`plain_english_description`** field — compiled from `flint:description` in the source payload. Enables human-readable audit reporting.

- **`non_conformance_message`** field — compiled from `flint:salvageClause` in the source payload (or auto-generated for `flint:Violation` if no salvage clause is declared). Surfaces directly in S-Cert audit logs.

- **`flint_type` in `metadata`** — every compiled rule now records the source FLINT type, enabling downstream consumers to route by ontology layer.

- **`examples/` folder** — working FLINT JSON-LD files for all six types, plus `run_all.py` end-to-end demo covering the full Fact → Duty → Act → Source → Reference → Violation stack.

- **`flint:Duty` party fields:** `duty_holder` and `claimant` extracted and forwarded to the compiled rule.

- **`flint:Act` fields:** `act_actor`, `act_object`, `act_precondition`, `act_postcondition` forwarded to the compiled rule.

- **`flint:Reference` linking:** `refers_to_urn` in compiled rule enables chained enforcement across rule bundles.

- **`flint:Violation` chaining:** `related_duty_urn` links the violation back to the violated duty; `non_conformance_message` from salvage clause is escalated.

- **Legacy `flint:validityPeriod` shape** supported in `flint:Duty` parsing (emitted by some TNO tooling as `{start, end}` not `{flint:start, flint:end}`).

### 🔧 Changed

- `odgs` dependency bumped to `>=5.1.0` (required for `LOG_ONLY` verdict, temporal bounds, and complete S-Cert fields).

### ⚠️ Migration Notes

All changes are **additive and backward-compatible**:

- `FlintParser.parse_fact()` still works for `flint:Fact` and `flint:Duty` payloads. For new code, prefer `FlintParser.parse()`.
- Compiled rules from v0.2.x are structurally identical — new fields (`plain_english_description`, `non_conformance_message`, `flint_type` in metadata) are only emitted when source data is available.
- Requires `odgs>=5.1.0` — upgrade the engine at the same time.

---

## [0.2.0] - 2026-03-19

### ✨ Added

- **`odgs-flint` CLI:** Installed as a command-line tool after `pip install odgs-flint-bridge`.
  ```bash
  odgs-flint sample_flint.json              # compile and print
  odgs-flint sample_flint.json -o rule.json # compile and save
  odgs-flint sample_flint.json --compact    # compact JSON
  ```

- **`semantic_hash` promoted to top-level S-Cert field:** SHA-256 of the verbatim FLINT JSON-LD source is now a top-level field in the compiled rule.

- **Duty temporal bounds extraction:** `effective_from` and `effective_to` extracted from `flint:period`.

- **`legislative_source` and `verdict_on_pass`** added as top-level fields.

### 🔧 Changed

- Default `odgs_version` in compiled rules updated to `5.1.0`.

### ⚠️ Migration Notes

All changes are **additive** — existing integrations continue to work.

---

## [0.1.0] - 2026-03-14

### 🚀 Initial Release
- TNO FLINT (Regels als Code) → ODGS Executable Rules transformation engine.
- Parser (`parser.py`): Deserializes FLINT JSON-LD acts, facts, duties, and violations.
- Compiler (`compiler.py`): Compiles FLINT semantic acts into ODGS enforcement rule schemas.
- Sample input: `sample_flint.json` (Zorgtoeslag eligibility check).
- Requires `odgs>=5.0.0` — exclusively targets the v5 polymorphic execution engine.
- Apache 2.0 — open-source institutional connector.
