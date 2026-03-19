#!/usr/bin/env python3
"""
examples/run_all.py — ODGS FLINT Bridge v0.3.0 end-to-end demo
================================================================
Demonstrates all six supported FLINT types being compiled into ODGS rules.

Usage:
    python examples/run_all.py
    # or from repo root:
    python -m examples.run_all
"""
import json
import sys
from pathlib import Path

# Allow running from repo root without installing
sys.path.insert(0, str(Path(__file__).parent.parent))

from odgs_flint_bridge.parser import FlintParser
from odgs_flint_bridge.compiler import OdgsCompiler

EXAMPLES_DIR = Path(__file__).parent

EXAMPLES = [
    ("flint:Fact",      "fact_zorgtoeslag.json",          "Income threshold constraint (Zorgtoeslag / Awb)"),
    ("flint:Duty",      "duty_ai_act_transparency.json",  "Transparency obligation (EU AI Act Art. 13)"),
    ("flint:Act",       "act_dora_access_control.json",   "ICT access control act (DORA Art. 9)"),
    ("flint:Source",    "source_awb_art5.json",           "Legislative source anchor (Awb Art. 5)"),
    ("flint:Reference", "reference_dora_to_nis2.json",    "Cross-reference DORA → NIS2"),
    ("flint:Violation", "violation_ai_act_transparency.json", "Transparency breach violation (EU AI Act Art. 73)"),
]

SEPARATOR = "─" * 70


def main():
    print(f"\n{'═' * 70}")
    print("  ODGS FLINT Bridge v0.3.0 — Full Type Coverage Demo")
    print(f"{'═' * 70}\n")

    results = []
    errors  = []

    for flint_type, filename, description in EXAMPLES:
        filepath = EXAMPLES_DIR / filename
        print(f"{SEPARATOR}")
        print(f"  {flint_type}")
        print(f"  {description}")
        print(f"  File: {filename}")
        print(SEPARATOR)

        try:
            with open(filepath) as f:
                payload = json.load(f)

            parsed = FlintParser.parse(payload)
            rule   = OdgsCompiler.compile_rule(parsed)

            # Summary output
            print(f"  ✅  urn:             {rule.get('urn', 'n/a')}")
            print(f"      severity:        {rule.get('severity', 'n/a')}")
            print(f"      semantic_hash:   {rule.get('semantic_hash', 'n/a')[:16]}...")
            if rule.get("logic_expression"):
                print(f"      logic_expr:      {rule['logic_expression']}")
            if rule.get("effective_from"):
                print(f"      effective_from:  {rule['effective_from']}")
            if rule.get("effective_to"):
                print(f"      effective_to:    {rule['effective_to']}")
            if rule.get("refers_to_urn"):
                print(f"      refers_to:       {rule['refers_to_urn']}")
            if rule.get("related_duty_urn"):
                print(f"      related_duty:    {rule['related_duty_urn']}")
            if rule.get("plain_english_description"):
                desc = rule["plain_english_description"]
                print(f"      description:     {desc[:60]}{'...' if len(desc) > 60 else ''}")
            if rule.get("non_conformance_message"):
                msg = rule["non_conformance_message"]
                print(f"      non_conformance: {msg[:60]}{'...' if len(msg) > 60 else ''}")

            results.append((flint_type, rule))

        except Exception as exc:
            print(f"  ❌ ERROR: {exc}")
            errors.append((flint_type, str(exc)))

        print()

    # Final summary
    print(f"{'═' * 70}")
    print(f"  Summary: {len(results)} compiled, {len(errors)} failed")
    if errors:
        for t, e in errors:
            print(f"    ✗ {t}: {e}")
    print(f"{'═' * 70}\n")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
