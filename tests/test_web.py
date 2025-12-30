import httpx
import pytest

from summarizium import web


class StubResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


def test_fetch_page_text_strips_html(monkeypatch):
    called = {}

    def fake_get(url, timeout):
        called["url"] = url
        called["timeout"] = timeout
        return StubResponse("<p>Hello</p>")

    monkeypatch.setattr(web.httpx, "get", fake_get)

    result = web.fetch_page_text("https://example.com", timeout=7.5)

    assert result == "Hello"
    assert called == {"url": "https://example.com", "timeout": 7.5}


def test_fetch_page_text_http_error_exits(monkeypatch, capsys):
    def fake_get(*_args, **_kwargs):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr(web.httpx, "get", fake_get)

    with pytest.raises(SystemExit) as exc:
        web.fetch_page_text("https://example.com")

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert "Error:" in captured.err
    assert "boom" in captured.err
