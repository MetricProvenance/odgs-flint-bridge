import hashlib
import json
from typing import Dict, Any

class OdgsCompiler:
    """Compiles parsed FLINT semantics into executable ODGS Enforcement Rules (Physical Plane)."""

    @staticmethod
    def _create_semantic_hash(raw_payload: Dict[str, Any]) -> str:
        """Creates an immutable SHA-256 hash of the original FLINT JSON-LD."""
        # Ensure deterministic hashing by sorting keys
        payload_string = json.dumps(raw_payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(payload_string.encode('utf-8')).hexdigest()

    @staticmethod
    def compile_rule(parsed_data: Dict[str, Any], odgs_version: str = "5.0.0") -> Dict[str, Any]:
        """
        Compiles the ODGS execution payload with built-in Administrative Recusal.
        Outputs W3C JSON-LD `EnforcementRule`.
        """
        source_ref = parsed_data["source_reference"]
        semantic_hash = OdgsCompiler._create_semantic_hash(parsed_data["raw_payload"])

        # Extract full taxonomy ID from the urn (e.g., "urn:flint:duty:eudataact:art5:p1" -> "eudataact_art5_p1")
        urn = parsed_data["raw_payload"].get("flint:identifier", "")
        short_id = urn.split(":")[3:] if ":" in urn else ["custom_rule"]
        
        urn_suffix = '_'.join(short_id)
        
        # Format target_value for evaluation (wrap strings in quotes)
        target_v = parsed_data['target_value']
        formatted_value = f"'{target_v}'" if isinstance(target_v, str) else str(target_v)

        return {
            "@context": "https://metricprovenance.com/schemas/odgs/v5",
            "@type": "EnforcementRule",
            "urn": f"urn:odgs:rule:flint:{urn_suffix}",
            "name": parsed_data["raw_payload"].get("flint:name", f"FLINT Rule {urn_suffix}"),
            "domain": "Legislative Compliance",
            "target_variable": parsed_data['target_field'],
            "logic_expression": f"{parsed_data['target_field']} {parsed_data['operator']} {formatted_value}",
            "definition": f"Derived from TNO FLINT: {source_ref}",
            "severity": "HARD_STOP",
            "metadata": {
                "ontology_source": "TNO_FLINT",
                "semantic_hash": semantic_hash
            }
        }
