"""
ODGS FLINT Bridge — Comprehensive Test Suite (v0.3.0)
======================================================
Tests all six FLINT types end-to-end through FlintParser → OdgsCompiler.
"""
import pytest
from odgs_flint_bridge.parser import FlintParser
from odgs_flint_bridge.compiler import OdgsCompiler


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixtures
# ─────────────────────────────────────────────────────────────────────────────

MOCK_FACT = {
    "@context": "https://flint.tno.nl/ontology/context.jsonld",
    "@type": "flint:Fact",
    "flint:identifier": "urn:flint:fact:toetsingsinkomen:2026",
    "flint:name": "ToetsingsinkomenThreshold",
    "flint:description": "Income must not exceed the threshold.",
    "flint:salvageClause": "Income exceeds threshold — reject application.",
    "flint:sourceReference": "https://wetten.overheid.nl/BWBR0018472/2026-01-01/#hoofdstuk_2_artikel_2",
    "flint:validityPeriod": {"start": "2026-01-01T00:00:00Z", "end": None},
    "flint:expression": {
        "@type": "flint:Condition",
        "flint:subject": "citizen.annual_income",
        "flint:operator": "LESS_THAN_OR_EQUAL",
        "flint:targetValue": 37496,
        "flint:datatype": "xsd:decimal",
    },
}

MOCK_DUTY = {
    "@context": "https://flint.tno.nl/ontology/context.jsonld",
    "@type": "flint:Duty",
    "flint:identifier": "urn:flint:duty:ai_act:art13:transparency",
    "flint:name": "AIActTransparencyObligation",
    "flint:description": "AI system must maintain audit logs.",
    "flint:salvageClause": "Audit log missing — halt processing.",
    "flint:sourceReference": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689#art_13",
    "flint:dutyHolder": "ai_system_operator",
    "flint:claimant": "regulatory_authority",
    "flint:period": {"flint:start": "2026-08-02", "flint:end": None},
    "flint:expression": {
        "flint:subject": "audit_log.record_count",
        "flint:operator": "GREATER_THAN",
        "flint:targetValue": 0,
    },
}

MOCK_ACT = {
    "@context": "https://flint.tno.nl/ontology/context.jsonld",
    "@type": "flint:Act",
    "flint:identifier": "urn:flint:act:dora:art9:access_control",
    "flint:name": "DORAICTAccessControlAct",
    "flint:description": "Only authorised ICT administrators may modify critical system configs.",
    "flint:salvageClause": "Unauthorised change — escalate to CISO.",
    "flint:sourceReference": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R2554#art_9",
    "flint:actor": "ict_administrator",
    "flint:object": "critical_system_configuration",
    "flint:precondition": {
        "flint:subject": "actor.authorisation_level",
        "flint:operator": "GREATER_THAN_OR_EQUAL",
        "flint:targetValue": 3,
    },
    "flint:postcondition": "change_log.entry_created == True",
}

MOCK_SOURCE = {
    "@context": "https://flint.tno.nl/ontology/context.jsonld",
    "@type": "flint:Source",
    "flint:identifier": "urn:flint:source:awb:art5:p1",
    "flint:name": "AlgemeneWetBestuursrechtArt5",
    "flint:description": "Statutory source for Zorgtoeslag income threshold.",
    "flint:sourceReference": "https://wetten.overheid.nl/BWBR0018472/2026-01-01/#hoofdstuk_2_artikel_2",
    "flint:citation": "Awb Art. 5, lid 1 — Wet zorgtoeslag",
    "flint:body": "Het recht op zorgtoeslag bestaat slechts indien...",
    "flint:jurisdiction": "NL",
    "flint:language": "nl",
}

MOCK_REFERENCE = {
    "@context": "https://flint.tno.nl/ontology/context.jsonld",
    "@type": "flint:Reference",
    "flint:identifier": "urn:flint:ref:dora:art9:ref:nis2:art21",
    "flint:name": "DORAtoNIS2CrossReference",
    "flint:description": "DORA Art. 9 supplements NIS2 Art. 21.",
    "flint:sourceReference": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R2554#art_9",
    "flint:refersTo": "urn:flint:act:nis2:art21:security_measures",
}

MOCK_VIOLATION = {
    "@context": "https://flint.tno.nl/ontology/context.jsonld",
    "@type": "flint:Violation",
    "flint:identifier": "urn:flint:violation:ai_act:art13:transparency_breach",
    "flint:name": "AIActTransparencyViolation",
    "flint:description": "Triggered when AI system fails its Art. 13 transparency duty.",
    "flint:salvageClause": "Immediate halt. Submit incident report within 24 hours.",
    "flint:sourceReference": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689#art_73",
    "flint:relatedDuty": "urn:flint:duty:ai_act:art13:transparency",
    "flint:expression": {
        "flint:subject": "audit_log.record_count",
        "flint:operator": "EQUALS",
        "flint:targetValue": 0,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. flint:Fact — existing behaviour preserved
# ─────────────────────────────────────────────────────────────────────────────

class TestFlintFact:
    def test_parse_routes_correctly(self):
        p = FlintParser.parse(MOCK_FACT)
        assert p["flint_type"] == "flint:Fact"
        assert p["target_field"] == "citizen.annual_income"
        assert p["operator"] == "<="
        assert p["target_value"] == 37496.0

    def test_backward_compat_parse_fact(self):
        """parse_fact() still works for Fact/Duty — backward compatibility."""
        p = FlintParser.parse_fact(MOCK_FACT)
        assert p["flint_type"] == "flint:Fact"

    def test_compile_produces_hard_stop(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_FACT))
        assert rule["severity"] == "HARD_STOP"
        assert rule["logic_expression"] == "citizen.annual_income <= 37496.0"
        assert rule["urn"] == "urn:odgs:rule:flint:toetsingsinkomen_2026"

    def test_semantic_hash_present(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_FACT))
        assert "semantic_hash" in rule
        assert len(rule["semantic_hash"]) == 64  # SHA-256 hex

    def test_plain_english_description(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_FACT))
        assert rule["plain_english_description"] == "Income must not exceed the threshold."

    def test_non_conformance_message(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_FACT))
        assert rule["non_conformance_message"] == "Income exceeds threshold — reject application."

    def test_legislative_source(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_FACT))
        assert "wetten.overheid.nl" in rule["legislative_source"]


# ─────────────────────────────────────────────────────────────────────────────
# 2. flint:Duty — temporal bounds + party fields
# ─────────────────────────────────────────────────────────────────────────────

class TestFlintDuty:
    def test_parse_routes_correctly(self):
        p = FlintParser.parse(MOCK_DUTY)
        assert p["flint_type"] == "flint:Duty"
        assert p["effective_from"] == "2026-08-02"
        assert p["effective_to"] is None

    def test_duty_holder_and_claimant_parsed(self):
        p = FlintParser.parse(MOCK_DUTY)
        assert p["duty_holder"] == "ai_system_operator"
        assert p["claimant"] == "regulatory_authority"

    def test_compile_includes_temporal_bounds(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_DUTY))
        assert rule["effective_from"] == "2026-08-02"
        assert "effective_to" not in rule  # None → not emitted

    def test_compile_party_fields(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_DUTY))
        assert rule["duty_holder"] == "ai_system_operator"
        assert rule["claimant"] == "regulatory_authority"


# ─────────────────────────────────────────────────────────────────────────────
# 3. flint:Act — actor validation rule
# ─────────────────────────────────────────────────────────────────────────────

class TestFlintAct:
    def test_parse_routes_correctly(self):
        p = FlintParser.parse(MOCK_ACT)
        assert p["flint_type"] == "flint:Act"
        assert p["act_actor"] == "ict_administrator"
        assert p["act_object"] == "critical_system_configuration"

    def test_precondition_parsed(self):
        p = FlintParser.parse(MOCK_ACT)
        assert len(p["logic_conditions"]) >= 1  # actor clause + precondition

    def test_compile_severity_act_constraint(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_ACT))
        assert rule["severity"] == "ACT_CONSTRAINT"

    def test_compile_actor_fields_present(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_ACT))
        assert rule["act_actor"] == "ict_administrator"
        assert rule["act_object"] == "critical_system_configuration"

    def test_compile_logic_expression_includes_actor(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_ACT))
        assert "ict_administrator" in rule["logic_expression"]


# ─────────────────────────────────────────────────────────────────────────────
# 4. flint:Source — provenance-only, no logic expression
# ─────────────────────────────────────────────────────────────────────────────

class TestFlintSource:
    def test_parse_routes_correctly(self):
        p = FlintParser.parse(MOCK_SOURCE)
        assert p["flint_type"] == "flint:Source"
        assert p["jurisdiction"] == "NL"
        assert p["verbatim_text"] is not None

    def test_compile_severity_metadata_only(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_SOURCE))
        assert rule["severity"] == "METADATA_ONLY"

    def test_compile_no_logic_expression(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_SOURCE))
        assert "logic_expression" not in rule

    def test_compile_verbatim_text_present(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_SOURCE))
        assert "verbatim_source_text" in rule

    def test_compile_silent_pass(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_SOURCE))
        assert rule["verdict_on_pass"] == "SILENT_PASS"


# ─────────────────────────────────────────────────────────────────────────────
# 5. flint:Reference — cross-reference linking rule
# ─────────────────────────────────────────────────────────────────────────────

class TestFlintReference:
    def test_parse_routes_correctly(self):
        p = FlintParser.parse(MOCK_REFERENCE)
        assert p["flint_type"] == "flint:Reference"
        assert p["refers_to_urn"] == "urn:flint:act:nis2:art21:security_measures"

    def test_compile_severity_log_only(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_REFERENCE))
        assert rule["severity"] == "LOG_ONLY"

    def test_compile_refers_to_urn_present(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_REFERENCE))
        assert rule["refers_to_urn"] == "urn:flint:act:nis2:art21:security_measures"

    def test_compile_logic_expression_links_urn(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_REFERENCE))
        assert "nis2" in rule["logic_expression"]


# ─────────────────────────────────────────────────────────────────────────────
# 6. flint:Violation — elevated HARD_STOP with related duty
# ─────────────────────────────────────────────────────────────────────────────

class TestFlintViolation:
    def test_parse_routes_correctly(self):
        p = FlintParser.parse(MOCK_VIOLATION)
        assert p["flint_type"] == "flint:Violation"
        assert p["related_duty"] == "urn:flint:duty:ai_act:art13:transparency"

    def test_compile_severity_hard_stop(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_VIOLATION))
        assert rule["severity"] == "HARD_STOP"

    def test_compile_related_duty_urn_present(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_VIOLATION))
        assert rule["related_duty_urn"] == "urn:flint:duty:ai_act:art13:transparency"

    def test_compile_non_conformance_message_from_salvage(self):
        rule = OdgsCompiler.compile_rule(FlintParser.parse(MOCK_VIOLATION))
        assert "24 hours" in rule["non_conformance_message"]


# ─────────────────────────────────────────────────────────────────────────────
# 7. Parser error handling
# ─────────────────────────────────────────────────────────────────────────────

class TestParserErrors:
    def test_unsupported_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported FLINT @type"):
            FlintParser.parse({"@type": "flint:Unknown"})

    def test_parse_fact_rejects_act_type(self):
        with pytest.raises(ValueError, match="parse_fact\\(\\) only accepts"):
            FlintParser.parse_fact(MOCK_ACT)

    def test_fact_missing_source_reference_raises(self):
        bad = {**MOCK_FACT}
        del bad["flint:sourceReference"]
        with pytest.raises(KeyError):
            FlintParser.parse(bad)

    def test_fact_unsupported_operator_raises(self):
        bad = {
            **MOCK_FACT,
            "flint:expression": {
                "flint:subject": "x",
                "flint:operator": "UNSUPPORTED_OP",
                "flint:targetValue": 1,
            }
        }
        with pytest.raises(ValueError, match="Unsupported FLINT operator"):
            FlintParser.parse(bad)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Common S-Cert fields across all types
# ─────────────────────────────────────────────────────────────────────────────

ALL_MOCKS = [MOCK_FACT, MOCK_DUTY, MOCK_ACT, MOCK_SOURCE, MOCK_REFERENCE, MOCK_VIOLATION]

@pytest.mark.parametrize("mock", ALL_MOCKS)
def test_all_types_have_s_cert_fields(mock):
    rule = OdgsCompiler.compile_rule(FlintParser.parse(mock))
    assert "urn" in rule
    assert "semantic_hash" in rule and len(rule["semantic_hash"]) == 64
    assert "legislative_source" in rule
    assert rule["@type"] == "EnforcementRule"
    assert rule["metadata"]["odgs_version"] == "5.1.0"
    assert rule["metadata"]["flint_type"] in {
        "flint:Fact", "flint:Duty", "flint:Act",
        "flint:Source", "flint:Reference", "flint:Violation"
    }
