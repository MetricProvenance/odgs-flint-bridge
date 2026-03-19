"""
odgs-flint CLI
==============
Command-line interface for the ODGS FLINT Bridge.

Usage:
    odgs-flint <path_to_flint_json_ld>                    # compile and print
    odgs-flint <path_to_flint_json_ld> --output rule.json # compile and save
    odgs-flint <path_to_flint_json_ld> --pretty           # pretty-print output
"""
import argparse
import json
import sys

from odgs_flint_bridge.parser import FlintParser
from odgs_flint_bridge.compiler import OdgsCompiler


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="odgs-flint",
        description="Compile a TNO FLINT JSON-LD payload into an ODGS Enforcement Rule.",
    )
    parser.add_argument(
        "input",
        help="Path to the FLINT JSON-LD file (flint:Fact or flint:Duty)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Write compiled rule to this file instead of stdout",
    )
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        default=True,
        help="Pretty-print JSON output (default: True)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        default=False,
        help="Compact JSON output (overrides --pretty)",
    )
    args = parser.parse_args()

    # Load input
    try:
        with open(args.input, "r") as f:
            flint_payload = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.input}: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse and compile
    try:
        parsed = FlintParser.parse_fact(flint_payload)
        rule = OdgsCompiler.compile_rule(parsed)
    except (KeyError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Render output
    indent = None if args.compact else 2
    output_str = json.dumps(rule, indent=indent)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output_str)
        print(f"Rule written to {args.output}")
        print(f"  semantic_hash: {rule.get('semantic_hash', 'n/a')}")
        print(f"  urn:           {rule.get('urn', 'n/a')}")
        if "effective_from" in rule:
            print(f"  effective_from: {rule['effective_from']}")
        if "effective_to" in rule:
            print(f"  effective_to:   {rule['effective_to']}")
    else:
        print(output_str)


if __name__ == "__main__":
    main()
