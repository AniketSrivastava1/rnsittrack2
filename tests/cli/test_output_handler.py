import pytest
import json
from hypothesis import given, strategies as st
from devready.cli.output_handler import OutputHandler
from io import StringIO
import sys

@given(st.recursive(
    st.one_of(st.none(), st.booleans(), st.integers(), st.text(), st.floats(allow_nan=False, allow_infinity=False)),
    lambda children: st.one_of(st.lists(children), st.dictionaries(st.text(), children)),
    max_leaves=10
))
def test_json_output_always_valid_json(data):
    # Mock stdout to capture print
    captured_output = StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured_output
    try:
        handler = OutputHandler(json_mode=True)
        handler.output(data)
        output_str = captured_output.getvalue()
        # Verify it's valid JSON and matches the data
        assert json.loads(output_str) == data
    finally:
        sys.stdout = original_stdout

def test_formatted_output_calls_formatter():
    mock_formatter = MagicMock()
    handler = OutputHandler(json_mode=False)
    data = {"test": "data"}
    handler.output(data, formatter_fn=mock_formatter)
    mock_formatter.assert_called_once_with(data)

from unittest.mock import MagicMock
