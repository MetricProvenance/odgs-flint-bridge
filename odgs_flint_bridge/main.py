import json
import base64
from typing import Dict, Any
from odgs_flint_bridge.parser import FlintParser
from odgs_flint_bridge.compiler import OdgsCompiler

class FlintBridge:
    """Main orchestration class for the ODGS Institutional Bridge."""

    @staticmethod
    def process_flint_payload(flint_json_ld: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes raw TNO FLINT Linked Data and compiles it into an ODGS Enforcement Rule.
        """
        # 1. Parse Semantic Truth
        parsed_data = FlintParser.parse_fact(flint_json_ld)
        
        # 2. Compile Physical Enforcement
        odgs_rule = OdgsCompiler.compile_rule(parsed_data)
        
        # 3. Mint Cryptographic Seal (Mocked for bridge demonstration)
        # In production, this pings the S-Cert Sovereign Registry
        odgs_rule["__attestation__"] = {
            "is_signed": True,
            "key_id": "flint-sovereign-ca",
            "signature": FlintBridge._mock_seal(odgs_rule)
        }
        
        return odgs_rule
        
    @staticmethod
    def _mock_seal(payload: Dict[str, Any]) -> str:
        """Generates a mock JWS B64 string for the demonstration payload."""
        header = base64.b64encode(b'{"alg":"RS256","typ":"JWT"}').decode('utf-8')
        body = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')
        return f"{header}.{body}.MOCK_SIGNATURE_DO_NOT_USE_IN_PROD"

if __name__ == "__main__":
    # Example usage for CLI testing
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_flint_json_ld>")
        sys.exit(1)
        
    with open(sys.argv[1], 'r') as f:
        payload = json.load(f)
        
    result = FlintBridge.process_flint_payload(payload)
    print(json.dumps(result, indent=2))
