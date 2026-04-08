import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from devready.operator.fix_parser import FixParser, PrettyPrinter

def test_fix_parser():
    parser = FixParser()
    res = parser.parse_command("npm install lodash@4.17.21")
    assert res["package_manager"] == "npm"
    assert res["action"] == "install"
    assert res["target"] == "lodash"
    assert res["version"] == "4.17.21"

def test_round_trip():
    # Property: Round-Trip Parsing
    parser = FixParser()
    printer = PrettyPrinter()
    parsed = parser.parse_command("pip install requests==2.28")
    pretty = printer.format_fix(parsed, "low", "sandbox_only")
    assert "Install requests" in pretty
    assert "pip install requests==2.28" in pretty
