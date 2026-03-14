from typing import Dict, Any, Optional

class FlintParser:
    """Parses TNO FLINT 'Fact' Linked Data (JSON-LD) into standardized ODGS input."""

    @staticmethod
    def parse_fact(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts semantic references and mathematical expressions 
        from a TNO FLINT JSON-LD Fact object.
        """
        # Ensure it's a valid FLINT fact or duty
        if payload.get("@type") not in ["flint:Fact", "flint:Duty"]:
            raise ValueError("Invalid FLINT Payload: Expected '@type': 'flint:Fact' or 'flint:Duty'")
        
        # 1. Extract Semantic Truth (Legislative Anchor)
        source_reference = payload.get("flint:sourceReference")
        if not source_reference:
            raise KeyError("Missing 'flint:sourceReference' in FLINT payload.")
        
        # 2. Extract The Mathematical Expression
        expression = payload.get("flint:expression", {})
        if not expression:
            raise KeyError("Missing 'flint:expression' in FLINT payload.")
        
        # Map FLINT vocabulary to ODGS syntax
        target_field = expression.get("flint:subject")
        flint_operator = expression.get("flint:operator")
        target_value = expression.get("flint:targetValue")
        
        operator_map = {
            "LESS_THAN_OR_EQUAL": "<=",
            "GREATER_THAN_OR_EQUAL": ">=",
            "EQUALS": "==",
            "LESS_THAN": "<",
            "GREATER_THAN": ">",
        }
        
        mapped_operator = operator_map.get(flint_operator)
        if not mapped_operator:
            if flint_operator in operator_map.values():
                mapped_operator = flint_operator
            else:
                raise ValueError(f"Unsupported FLINT operator: {flint_operator}")

        try:
            parsed_value = float(target_value) if target_value is not None else None
        except ValueError:
            parsed_value = target_value.strip('"\'') if isinstance(target_value, str) else target_value

        return {
            "source_reference": source_reference,
            "target_field": target_field,
            "operator": mapped_operator,
            "target_value": parsed_value,
            "raw_payload": payload # Passed forward for the SHA-256 seal
        }
