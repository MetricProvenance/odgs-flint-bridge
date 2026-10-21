"""
ODGS FLINT Bridge
=================

Translates TNO FLINT (Formal Language for the Interpretation of Normative
Texts) Linked Data into ODGS Executable Enforcement Rules.

Usage:
    from odgs_flint_bridge import FlintParser, OdgsCompiler

    parsed = FlintParser.parse(flint_payload)
    rule = OdgsCompiler.compile_rule(parsed)
"""

__version__ = "0.4.2"

from odgs_flint_bridge.parser import FlintParser
from odgs_flint_bridge.compiler import OdgsCompiler

__all__ = ["FlintParser", "OdgsCompiler"]
