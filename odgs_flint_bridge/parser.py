"""
ODGS FLINT Parser — v0.3.0
===========================
Parses all six TNO FLINT JSON-LD types into a standardised ODGS intermediate
representation that the compiler can turn into enforcement rules.

Supported types:
    flint:Fact       — a condition/constraint that must hold (logical expression)
    flint:Duty       — a time-bound obligation (temporal rule bounds auto-extracted)
    flint:Act        — an executable action with actor, object, pre/post-conditions
    flint:Source     — a legislative source anchor (provenance-only, no logic expr)
    flint:Reference  — a cross-reference to another FLINT element (linking rule)
    flint:Violation  — a contrary-to-duty obligation; compiles to elevated HARD_STOP

Entry point:
    FlintParser.parse(payload)          — auto-routes by @type (recommended)
    FlintParser.parse_fact(payload)     — kept for backward compat (Fact + Duty)
"""

from typing import Dict, Any, Optional, List


# ---------------------------------------------------------------------------
# Supported FLINT @type values
# ---------------------------------------------------------------------------
FLINT_TYPES = {
    "flint:Fact",
    "flint:Duty",
    "flint:Act",
    "flint:Source",
    "flint:Reference",
    "flint:Violation",
}

# Shared operator vocabulary
OPERATOR_MAP: Dict[str, str] = {
    "LESS_THAN_OR_EQUAL":    "<=",
    "GREATER_THAN_OR_EQUAL": ">=",
    "EQUALS":                "==",
    "NOT_EQUALS":            "!=",
    "LESS_THAN":             "<",
    "GREATER_THAN":          ">",
    "IN":                    "in",
    "NOT_IN":                "not in",
    "IS_NULL":               "is None",
    "IS_NOT_NULL":           "is not None",
}


def _map_operator(flint_op: Optional[str]) -> str:
    if flint_op is None:
        raise ValueError("Missing 'flint:operator' in expression.")
    mapped = OPERATOR_MAP.get(flint_op)
    if mapped is None:
        if flint_op in OPERATOR_MAP.values():
            return flint_op  # already a symbol
        raise ValueError(f"Unsupported FLINT operator: '{flint_op}'")
    return mapped


def _coerce_value(raw) -> Any:
    """Try to coerce a target value to float, fall back to cleaned string."""
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return str(raw).strip("\"'")


def _require(payload: Dict[str, Any], key: str) -> Any:
    val = payload.get(key)
    if val is None:
        raise KeyError(f"Missing required FLINT field: '{key}'")
    return val


class FlintParser:
    """Parses TNO FLINT JSON-LD payloads into a standardised ODGS intermediate dict."""

    # ------------------------------------------------------------------
    # Public dispatcher — recommended entry point
    # ------------------------------------------------------------------
    @staticmethod
    def parse(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Auto-routes to the correct sub-parser based on the payload's @type.
        Returns a standardised intermediate dict consumed by OdgsCompiler.
        """
        flint_type = payload.get("@type")
        if flint_type not in FLINT_TYPES:
            supported = ", ".join(sorted(FLINT_TYPES))
            raise ValueError(
                f"Unsupported FLINT @type: '{flint_type}'. Supported: {supported}"
            )

        dispatch = {
            "flint:Fact":      FlintParser._parse_fact_inner,
            "flint:Duty":      FlintParser._parse_duty,
            "flint:Act":       FlintParser._parse_act,
            "flint:Source":    FlintParser._parse_source,
            "flint:Reference": FlintParser._parse_reference,
            "flint:Violation": FlintParser._parse_violation,
        }
        return dispatch[flint_type](payload)

    # ------------------------------------------------------------------
    # Backward-compatible entry point (Fact + Duty only)
    # ------------------------------------------------------------------
    @staticmethod
    def parse_fact(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy entry point — kept for 0.1.x / 0.2.x backward compatibility.
        Accepts flint:Fact and flint:Duty payloads. For full type support use parse().
        """
        flint_type = payload.get("@type")
        if flint_type not in ("flint:Fact", "flint:Duty"):
            raise ValueError(
                f"parse_fact() only accepts flint:Fact / flint:Duty. Got '{flint_type}'. "
                "Use FlintParser.parse() for all types."
            )
        return FlintParser.parse(payload)

    # ------------------------------------------------------------------
    # flint:Fact — condition/constraint that must hold
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_fact_inner(payload: Dict[str, Any]) -> Dict[str, Any]:
        source_ref = _require(payload, "flint:sourceReference")
        expression = _require(payload, "flint:expression")

        target_field  = _require(expression, "flint:subject")
        flint_operator = expression.get("flint:operator")
        target_value  = expression.get("flint:targetValue")

        return {
            "flint_type":       "flint:Fact",
            "source_reference": source_ref,
            "target_field":     target_field,
            "operator":         _map_operator(flint_operator),
            "target_value":     _coerce_value(target_value),
            "description":      payload.get("flint:description"),
            "salvage_clause":   payload.get("flint:salvageClause"),
            "raw_payload":      payload,
        }

    # ------------------------------------------------------------------
    # flint:Duty — time-bound obligation
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_duty(payload: Dict[str, Any]) -> Dict[str, Any]:
        source_ref = _require(payload, "flint:sourceReference")
        expression = payload.get("flint:expression", {})

        target_field   = expression.get("flint:subject")
        flint_operator = expression.get("flint:operator")
        target_value   = expression.get("flint:targetValue")

        period = payload.get("flint:period", {})
        effective_from = period.get("flint:start")
        effective_to   = period.get("flint:end")

        # Also check legacy flint:validityPeriod shape (used in some TNO tooling)
        if not effective_from:
            validity = payload.get("flint:validityPeriod", {})
            effective_from = validity.get("start")
            effective_to   = validity.get("end") or effective_to

        return {
            "flint_type":       "flint:Duty",
            "source_reference": source_ref,
            "target_field":     target_field,
            "operator":         _map_operator(flint_operator) if flint_operator else None,
            "target_value":     _coerce_value(target_value),
            "effective_from":   str(effective_from)[:10] if effective_from else None,
            "effective_to":     str(effective_to)[:10]   if effective_to   else None,
            "duty_holder":      payload.get("flint:dutyHolder"),
            "claimant":         payload.get("flint:claimant"),
            "description":      payload.get("flint:description"),
            "salvage_clause":   payload.get("flint:salvageClause"),
            "raw_payload":      payload,
        }

    # ------------------------------------------------------------------
    # flint:Act — executable action with actor, object, pre/post-conditions
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_act(payload: Dict[str, Any]) -> Dict[str, Any]:
        source_ref = _require(payload, "flint:sourceReference")

        actor        = payload.get("flint:actor")
        act_object   = payload.get("flint:object")
        precondition = payload.get("flint:precondition")
        postcondition = payload.get("flint:postcondition")

        # Build a synthetic logic expression: actor IS_AUTHORIZED + precondition holds
        conditions: List[str] = []
        if actor:
            conditions.append(f"actor == '{actor}'")
        if precondition:
            if isinstance(precondition, str):
                conditions.append(precondition)
            elif isinstance(precondition, dict):
                subj = precondition.get("flint:subject", "precondition")
                op   = precondition.get("flint:operator", "IS_NOT_NULL")
                val  = precondition.get("flint:targetValue")
                cond_op = _map_operator(op) if op else "is not None"
                cond = f"{subj} {cond_op} {val}" if val is not None else f"{subj} {cond_op}"
                conditions.append(cond)

        return {
            "flint_type":       "flint:Act",
            "source_reference": source_ref,
            "target_field":     act_object or actor or "act_subject",
            "operator":         "==",
            "target_value":     None,
            "act_actor":        actor,
            "act_object":       act_object,
            "act_precondition": precondition,
            "act_postcondition": postcondition,
            "logic_conditions": conditions,
            "description":      payload.get("flint:description"),
            "salvage_clause":   payload.get("flint:salvageClause"),
            "raw_payload":      payload,
        }

    # ------------------------------------------------------------------
    # flint:Source — legislative source anchor (provenance-only)
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_source(payload: Dict[str, Any]) -> Dict[str, Any]:
        source_ref = _require(payload, "flint:sourceReference")

        return {
            "flint_type":         "flint:Source",
            "source_reference":   source_ref,
            "target_field":       "source_anchor",
            "operator":           None,
            "target_value":       None,
            "citation":           payload.get("flint:citation", source_ref),
            "verbatim_text":      payload.get("flint:body") or payload.get("flint:verbatimText"),
            "jurisdiction":       payload.get("flint:jurisdiction"),
            "language":           payload.get("flint:language", "nl"),
            "description":        payload.get("flint:description"),
            "salted_clause":      None,
            "raw_payload":        payload,
        }

    # ------------------------------------------------------------------
    # flint:Reference — cross-reference to another FLINT element
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_reference(payload: Dict[str, Any]) -> Dict[str, Any]:
        source_ref  = _require(payload, "flint:sourceReference")
        refers_to   = payload.get("flint:refersTo") or payload.get("flint:references")
        ref_urn     = payload.get("flint:identifier", "")

        return {
            "flint_type":       "flint:Reference",
            "source_reference": source_ref,
            "target_field":     "referenced_rule",
            "operator":         None,
            "target_value":     None,
            "refers_to_urn":    refers_to,
            "ref_urn":          ref_urn,
            "description":      payload.get("flint:description"),
            "salvage_clause":   None,
            "raw_payload":      payload,
        }

    # ------------------------------------------------------------------
    # flint:Violation — contrary-to-duty, triggered on breach
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_violation(payload: Dict[str, Any]) -> Dict[str, Any]:
        source_ref = _require(payload, "flint:sourceReference")
        expression = payload.get("flint:expression", {})

        target_field   = expression.get("flint:subject")
        flint_operator = expression.get("flint:operator")
        target_value   = expression.get("flint:targetValue")

        # flint:relatedDuty — the duty that was violated (provides chaining)
        related_duty = payload.get("flint:relatedDuty") or payload.get("flint:violatedDuty")

        return {
            "flint_type":       "flint:Violation",
            "source_reference": source_ref,
            "target_field":     target_field or "violation_subject",
            "operator":         _map_operator(flint_operator) if flint_operator else "!=",
            "target_value":     _coerce_value(target_value),
            "related_duty":     related_duty,
            "description":      payload.get("flint:description"),
            "salvage_clause":   payload.get("flint:salvageClause"),
            "raw_payload":      payload,
        }
