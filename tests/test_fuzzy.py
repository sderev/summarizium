import string

import pytest
import validators
from hypothesis import given, settings
from hypothesis import strategies as st

from summarizium import cli

TEXT_STRATEGY = st.text(min_size=0, max_size=500)
DOMAIN_LABEL = st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=20)
DOMAIN_SUFFIXES = ("", "/path", "?query=1", "#frag")
DOMAIN_TEXT_STRATEGY = st.builds(
    lambda label, tld, suffix: f"{label}{tld}{suffix}",
    DOMAIN_LABEL,
    st.sampled_from(cli.COMMON_TLDS),
    st.sampled_from(DOMAIN_SUFFIXES),
)
NON_PATH_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=0,
    max_size=200,
)
PATH_PREFIXES = ("/", "~", ".")
PATH_BODY = st.text(
    alphabet=string.ascii_letters + string.digits + "._-",
    min_size=1,
    max_size=50,
)
EDGE_CASES = [
    "",
    " ",
    "\t",
    "\n",
    "\x00",
    "test.commando",
    ".com",
    "a.com",
    "example.com ",
    " example.com",
    "example.com/path",
    "example.com?query=1",
    "example.com#frag",
    "exa mple.com",
    "~/notes.txt",
    "./notes.txt",
    "\u2603",
    "a" * 500,
]
DOMAIN_EXPECTATIONS = [
    ("example.com", True),
    ("example.org", True),
    ("example.com/path", True),
    ("example.com?query=1", True),
    ("example.com#frag", True),
    ("exa mple.com", False),
    ("test.commando", False),
    (".com", False),
    ("", False),
    (" ", False),
]
FILE_PATH_EXPECTATIONS = [
    ("./notes.txt", True),
    ("~/notes.txt", True),
    ("/tmp/notes.txt", True),
    ("notes/child", True),
    ("notes.txt", False),
    ("example.com", False),
    ("", False),
]
NORMALIZE_DOMAIN_CASES = [
    ("example.com", "https://example.com"),
    ("example.com/path", "https://example.com/path"),
    ("example.com?query=1", "https://example.com?query=1"),
    ("example.com#frag", "https://example.com#frag"),
]
NORMALIZE_DOMAIN_REJECTS = [
    "",
    " ",
    "exa mple.com",
    ".com",
    "notes.txt",
    "./notes.txt",
    "~/notes.txt",
]


@pytest.mark.parametrize("func", [cli._looks_like_domain, cli._looks_like_file_path])
@settings(derandomize=True)
@given(text=TEXT_STRATEGY)
def test_predicates_handle_arbitrary_input(func, text):
    """Should never crash on any input."""
    result = func(text)
    assert isinstance(result, bool)


@settings(derandomize=True)
@given(text=DOMAIN_TEXT_STRATEGY)
def test_looks_like_domain_accepts_common_tlds(text):
    """Recognizes domains built from known TLDs."""
    assert cli._looks_like_domain(text) is True


@settings(derandomize=True)
@given(prefix=st.sampled_from(PATH_PREFIXES), rest=PATH_BODY)
def test_looks_like_file_path_accepts_markers(prefix, rest):
    """Recognizes path markers like '/', '~', or '.' prefixes."""
    assert cli._looks_like_file_path(f"{prefix}{rest}") is True


@settings(derandomize=True)
@given(text=NON_PATH_TEXT)
def test_looks_like_file_path_rejects_non_paths(text):
    """Rejects strings without path markers."""
    assert cli._looks_like_file_path(text) is False


@pytest.mark.parametrize("text, expected", DOMAIN_EXPECTATIONS)
def test_looks_like_domain_expected_values(text, expected):
    """Keeps explicit domain expectations stable."""
    assert cli._looks_like_domain(text) is expected


@pytest.mark.parametrize("text, expected", FILE_PATH_EXPECTATIONS)
def test_looks_like_file_path_expected_values(text, expected):
    """Keeps explicit path expectations stable."""
    assert cli._looks_like_file_path(text) is expected


@pytest.mark.parametrize("func", [cli._looks_like_domain, cli._looks_like_file_path])
@pytest.mark.parametrize("text", EDGE_CASES)
def test_predicates_handle_edge_cases(func, text):
    """Should never crash on common edge cases."""
    result = func(text)
    assert isinstance(result, bool)


@settings(derandomize=True)
@given(text=TEXT_STRATEGY)
def test_normalize_domain_url_handles_arbitrary_input(text):
    """Should return None or valid URL, never crash."""
    result = cli._normalize_domain_url(text)
    assert result is None or validators.url(result) is True


@settings(derandomize=True)
@given(text=DOMAIN_TEXT_STRATEGY)
def test_normalize_domain_url_accepts_valid_domains(text):
    """Normalizes domains that already look valid."""
    assert cli._normalize_domain_url(text) == f"https://{text}"


@pytest.mark.parametrize("text, expected", NORMALIZE_DOMAIN_CASES)
def test_normalize_domain_url_expected_values(text, expected):
    """Preserves domain paths, queries, and fragments."""
    assert cli._normalize_domain_url(text) == expected


@pytest.mark.parametrize("text", NORMALIZE_DOMAIN_REJECTS)
def test_normalize_domain_url_rejects_invalid(text):
    """Rejects text that should not normalize into a URL."""
    assert cli._normalize_domain_url(text) is None


@pytest.mark.parametrize("text", EDGE_CASES)
def test_normalize_domain_url_handles_edge_cases(text):
    """Should return None or valid URL for common edge cases."""
    result = cli._normalize_domain_url(text)
    assert result is None or validators.url(result) is True
