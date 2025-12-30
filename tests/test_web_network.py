import pytest

from summarizium import web


@pytest.mark.network
@pytest.mark.parametrize(
    "url",
    (
        "https://example.com",
        "https://httpbin.org/redirect-to?url=https://example.com/",
    ),
)
def test_fetch_page_text_network(url):
    text = web.fetch_page_text(url, timeout=10.0)

    assert "Example Domain" in text
