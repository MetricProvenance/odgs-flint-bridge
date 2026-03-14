import pytest
from odgs_flint_bridge.main import FlintBridge

# TNO FLINT Dutch Administrative Example
# Income Threshold for Zorgtoeslag (Healthcare Allowance) under the Awb.
MOCK_FLINT_FACT = {
  "@context": "https://flint.tno.nl/ontology/context.jsonld",
  "@type": "flint:Fact",
  "flint:identifier": "urn:flint:fact:toetsingsinkomen:2026",
  "flint:name": "ToetsingsinkomenThreshold",
  "flint:sourceReference": "https://wetten.overheid.nl/BWBR0018472/2026-01-01/#hoofdstuk_2_artikel_2",
  "flint:validityPeriod": {
    "start": "2026-01-01T00:00:00Z",
    "end": None
  },
  "flint:expression": {
    "@type": "flint:Condition",
    "flint:subject": "citizen.annual_income",
    "flint:operator": "LESS_THAN_OR_EQUAL",
    "flint:targetValue": 37496,
    "flint:datatype": "xsd:decimal"
  }
}

def test_bridge_compilation_zorgtoeslag():
    """Validates the bridge end-to-end using the Dutch Zorgtoeslag dataset."""
    
    # Execute the Bridge
    odgs_rule = FlintBridge.process_flint_payload(MOCK_FLINT_FACT)
    
    # 1. Verify ODGS Metadata and Versioning
    assert odgs_rule["urn"] == "urn:odgs:rule:flint:toetsingsinkomen_2026"
    assert odgs_rule["name"] == "ToetsingsinkomenThreshold"
    assert odgs_rule["domain"] == "Legislative Compliance"
    
    # 2. Verify Semantic Provenance (The Legislative Plane)
    assert odgs_rule["definition"] == "Derived from TNO FLINT: https://wetten.overheid.nl/BWBR0018472/2026-01-01/#hoofdstuk_2_artikel_2"
    metadata = odgs_rule["metadata"]
    assert metadata["ontology_source"] == "TNO_FLINT"
    assert "semantic_hash" in metadata
    
    # 3. Verify Execution Logic Translation (The Physical Plane)
    assert odgs_rule["logic_expression"] == "citizen.annual_income <= 37496.0"
    assert odgs_rule["target_variable"] == "citizen.annual_income"
    assert odgs_rule["severity"] == "HARD_STOP"
    assert odgs_rule["@context"] == "https://metricprovenance.com/schemas/odgs/v5"
    assert odgs_rule["@type"] == "EnforcementRule"
    
    # 4. Verify Cryptographic Attestation (v4.1)
    attestation = odgs_rule["__attestation__"]
    assert attestation["is_signed"] is True
    assert attestation["key_id"] == "flint-sovereign-ca"
    assert "signature" in attestation
    assert "MOCK_SIGNATURE_DO_NOT_USE_IN_PROD" in attestation["signature"]
