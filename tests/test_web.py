import httpx
import pytest

from summarizium import web


class StubResponse:
    def __init__(self, text: str, raise_for_status_error: Exception | None = None) -> None:
        self.text = text
        self.raise_for_status_error = raise_for_status_error
        self.raise_for_status_called = False

    def raise_for_status(self) -> None:
        self.raise_for_status_called = True
        if self.raise_for_status_error is not None:
            raise self.raise_for_status_error


def test_fetch_page_text_strips_html(monkeypatch):
    called = {}

    def fake_get(url, timeout, follow_redirects):
        called["url"] = url
        called["timeout"] = timeout
        called["follow_redirects"] = follow_redirects
        response = StubResponse("<p>Hello</p>")
        called["response"] = response
        return response

    monkeypatch.setattr(web.httpx, "get", fake_get)

    result = web.fetch_page_text("https://example.com", timeout=7.5)

    assert result == "Hello"
    assert called["url"] == "https://example.com"
    assert called["timeout"] == 7.5
    assert called["follow_redirects"] is True
    assert called["response"].raise_for_status_called is True


def test_fetch_page_text_http_error_exits(monkeypatch, capsys):
    def fake_get(*_args, **_kwargs):
        return StubResponse("ignored", raise_for_status_error=httpx.HTTPError("boom"))

    monkeypatch.setattr(web.httpx, "get", fake_get)

    with pytest.raises(SystemExit) as exc:
        web.fetch_page_text("https://example.com")

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert "Error:" in captured.err
    assert "boom" in captured.err
