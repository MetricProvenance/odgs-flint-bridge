"""
ODGS FLINT Compiler — v0.3.0
=============================
Compiles the ODGS intermediate dict (output of FlintParser) into an ODGS
Enforcement Rule (W3C JSON-LD EnforcementRule schema).

Each FLINT type produces a differently-shaped rule:

  flint:Fact      → standard HARD_STOP constraint rule
  flint:Duty      → temporal HARD_STOP rule with effective_from / effective_to
  flint:Act       → actor-validation rule (ACT_CONSTRAINT severity)
  flint:Source    → provenance-only METADATA_ONLY rule (no logic_expression)
  flint:Reference → linking rule (REFERENCE_RULE, LOG_ONLY by default)
  flint:Violation → elevated HARD_STOP with non_conformance_message from salvage clause
"""

import hashlib
import json
from typing import Any, Dict, List, Optional


class OdgsCompiler:
    """Compiles parsed FLINT semantics into executable ODGS Enforcement Rules."""

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _semantic_hash(raw_payload: Dict[str, Any]) -> str:
        """SHA-256 of the canonical (sort-keyed) FLINT JSON-LD source payload."""
        canonical = json.dumps(raw_payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _urn_suffix(payload: Dict[str, Any]) -> str:
        urn = payload.get("flint:identifier", "")
        parts = urn.split(":")[3:] if ":" in urn else []
        return "_".join(parts) if parts else "custom_rule"

    @staticmethod
    def _base_rule(
        parsed: Dict[str, Any],
        odgs_version: str,
        severity: str,
        logic_expression: Optional[str],
        urn_suffix: str,
    ) -> Dict[str, Any]:
        raw        = parsed["raw_payload"]
        source_ref = parsed["source_reference"]
        sem_hash   = OdgsCompiler._semantic_hash(raw)
        name       = raw.get("flint:name", f"FLINT {parsed['flint_type']} {urn_suffix}")

        rule: Dict[str, Any] = {
            "@context":             "https://metricprovenance.com/schemas/odgs/v5",
            "@type":                "EnforcementRule",
            "urn":                  f"urn:odgs:rule:flint:{urn_suffix}",
            "name":                 name,
            "domain":               "Legislative Compliance",
            "severity":             severity,
            "semantic_hash":        sem_hash,
            "legislative_source":   source_ref,
            "verdict_on_pass":      "PASS",
            "metadata": {
                "ontology_source":  "TNO_FLINT",
                "flint_type":       parsed["flint_type"],
                "odgs_version":     odgs_version,
                "semantic_hash":    sem_hash,   # backward compat alias
            },
        }

        if logic_expression:
            rule["logic_expression"] = logic_expression
            rule["target_variable"]  = parsed.get("target_field", "")
            rule["definition"]       = f"Derived from TNO FLINT: {source_ref}"

        # Optional human-readable fields (plain_english_description, non_conformance_message)
        description   = parsed.get("description")
        salvage_clause = parsed.get("salvage_clause")
        if description:
            rule["plain_english_description"] = description
        if salvage_clause:
            rule["non_conformance_message"] = salvage_clause

        return rule

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    @staticmethod
    def compile_rule(parsed: Dict[str, Any], odgs_version: str = "5.1.0") -> Dict[str, Any]:
        """
        Compiles a parsed FLINT intermediate dict into an ODGS EnforcementRule.
        Dispatches by flint_type.
        """
        flint_type = parsed.get("flint_type", "flint:Fact")

        dispatch = {
            "flint:Fact":      OdgsCompiler._compile_fact,
            "flint:Duty":      OdgsCompiler._compile_duty,
            "flint:Act":       OdgsCompiler._compile_act,
            "flint:Source":    OdgsCompiler._compile_source,
            "flint:Reference": OdgsCompiler._compile_reference,
            "flint:Violation": OdgsCompiler._compile_violation,
        }
        fn = dispatch.get(flint_type, OdgsCompiler._compile_fact)
        return fn(parsed, odgs_version)

    # ------------------------------------------------------------------
    # flint:Fact — standard HARD_STOP constraint
    # ------------------------------------------------------------------
    @staticmethod
    def _compile_fact(parsed: Dict[str, Any], odgs_version: str) -> Dict[str, Any]:
        raw    = parsed["raw_payload"]
        suffix = OdgsCompiler._urn_suffix(raw)
        tv     = parsed["target_value"]
        fmt_v  = f"'{tv}'" if isinstance(tv, str) else str(tv)
        expr   = f"{parsed['target_field']} {parsed['operator']} {fmt_v}"

        rule = OdgsCompiler._base_rule(parsed, odgs_version, "HARD_STOP", expr, suffix)
        return rule

    # ------------------------------------------------------------------
    # flint:Duty — temporal HARD_STOP with effective_from / effective_to
    # ------------------------------------------------------------------
    @staticmethod
    def _compile_duty(parsed: Dict[str, Any], odgs_version: str) -> Dict[str, Any]:
        raw    = parsed["raw_payload"]
        suffix = OdgsCompiler._urn_suffix(raw)

        # Logic expression only if we have a subject and operator
        expr: Optional[str] = None
        if parsed.get("target_field") and parsed.get("operator"):
            tv    = parsed["target_value"]
            fmt_v = f"'{tv}'" if isinstance(tv, str) else str(tv)
            expr  = f"{parsed['target_field']} {parsed['operator']} {fmt_v}"

        rule = OdgsCompiler._base_rule(parsed, odgs_version, "HARD_STOP", expr, suffix)

        # Temporal bounds
        if parsed.get("effective_from"):
            rule["effective_from"] = parsed["effective_from"]
        if parsed.get("effective_to"):
            rule["effective_to"] = parsed["effective_to"]

        # Optional party fields
        if parsed.get("duty_holder"):
            rule["duty_holder"] = parsed["duty_holder"]
        if parsed.get("claimant"):
            rule["claimant"] = parsed["claimant"]

        return rule

    # ------------------------------------------------------------------
    # flint:Act — actor-validation rule
    # ------------------------------------------------------------------
    @staticmethod
    def _compile_act(parsed: Dict[str, Any], odgs_version: str) -> Dict[str, Any]:
        raw    = parsed["raw_payload"]
        suffix = OdgsCompiler._urn_suffix(raw)

        conditions: List[str] = parsed.get("logic_conditions", [])
        expr = " AND ".join(conditions) if conditions else "act_authorized == True"

        rule = OdgsCompiler._base_rule(parsed, odgs_version, "ACT_CONSTRAINT", expr, suffix)

        # Act-specific metadata
        if parsed.get("act_actor"):
            rule["act_actor"] = parsed["act_actor"]
        if parsed.get("act_object"):
            rule["act_object"] = parsed["act_object"]
        if parsed.get("act_precondition"):
            rule["act_precondition"] = parsed["act_precondition"]
        if parsed.get("act_postcondition"):
            rule["act_postcondition"] = parsed["act_postcondition"]

        # Acts default to LOG_ONLY until explicitly elevated — safe for initial rollout
        rule["verdict_on_pass"] = "PASS"

        return rule

    # ------------------------------------------------------------------
    # flint:Source — provenance-only, no enforcement logic
    # ------------------------------------------------------------------
    @staticmethod
    def _compile_source(parsed: Dict[str, Any], odgs_version: str) -> Dict[str, Any]:
        raw    = parsed["raw_payload"]
        suffix = OdgsCompiler._urn_suffix(raw)

        rule = OdgsCompiler._base_rule(
            parsed, odgs_version, "METADATA_ONLY", None, suffix
        )

        # Rich provenance fields
        if parsed.get("citation"):
            rule["citation"] = parsed["citation"]
        if parsed.get("verbatim_text"):
            rule["verbatim_source_text"] = parsed["verbatim_text"]
        if parsed.get("jurisdiction"):
            rule["jurisdiction"] = parsed["jurisdiction"]
        if parsed.get("language"):
            rule["language"] = parsed["language"]

        # Source rules never block — they annotate
        rule["verdict_on_pass"] = "SILENT_PASS"
        rule["severity"]        = "METADATA_ONLY"

        return rule

    # ------------------------------------------------------------------
    # flint:Reference — linking / cross-reference rule
    # ------------------------------------------------------------------
    @staticmethod
    def _compile_reference(parsed: Dict[str, Any], odgs_version: str) -> Dict[str, Any]:
        raw    = parsed["raw_payload"]
        suffix = OdgsCompiler._urn_suffix(raw)

        refers_to = parsed.get("refers_to_urn", "")
        expr = f"referenced_rule == '{refers_to}'" if refers_to else "referenced_rule is not None"

        rule = OdgsCompiler._base_rule(
            parsed, odgs_version, "LOG_ONLY", expr, suffix
        )

        rule["refers_to_urn"] = refers_to
        rule["verdict_on_pass"] = "SILENT_PASS"

        return rule

    # ------------------------------------------------------------------
    # flint:Violation — elevated HARD_STOP (contrary-to-duty)
    # ------------------------------------------------------------------
    @staticmethod
    def _compile_violation(parsed: Dict[str, Any], odgs_version: str) -> Dict[str, Any]:
        raw    = parsed["raw_payload"]
        suffix = OdgsCompiler._urn_suffix(raw)

        tf  = parsed.get("target_field", "violation_subject")
        op  = parsed.get("operator", "!=")
        tv  = parsed.get("target_value")
        fmt_v = f"'{tv}'" if isinstance(tv, str) else str(tv) if tv is not None else "None"
        expr  = f"{tf} {op} {fmt_v}"

        rule = OdgsCompiler._base_rule(parsed, odgs_version, "HARD_STOP", expr, suffix)

        # Violation rules always block — this is a breach-response rule
        rule["severity"] = "HARD_STOP"

        # Link back to the violated duty
        if parsed.get("related_duty"):
            rule["related_duty_urn"] = parsed["related_duty"]

        # Salvage clause becomes non_conformance_message if not already set by base_rule
        if "non_conformance_message" not in rule:
            salvage = parsed.get("salvage_clause")
            if salvage:
                rule["non_conformance_message"] = salvage
            else:
                rule["non_conformance_message"] = (
                    f"Violation of duty derived from: {parsed['source_reference']}. "
                    "Remediation required before processing can continue."
                )

        return rule
