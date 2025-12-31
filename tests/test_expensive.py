"""
Expensive tests that call paid LLM APIs.

These tests are skipped in CI (via `-m "not real and not network and not expensive"`).
Run manually with: uv run pytest --run-real tests/test_expensive.py
"""

import pytest
from click.testing import CliRunner

from summarizium import cli


@pytest.mark.real
@pytest.mark.expensive
@pytest.mark.parametrize(
    "source",
    ["Python is a programming language.", "https://example.com"],
    ids=["plain-text", "web-page"],
)
def test_summarize_end_to_end(source):
    """Actually summarize content using the LLM."""
    runner = CliRunner()
    result = runner.invoke(cli.summarize, [source])
    assert result.exit_code == 0
    assert len(result.output) > 10
