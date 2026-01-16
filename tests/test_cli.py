from pathlib import Path

import pytest
from click.testing import CliRunner

from summarizium import cli


def test_summarize_youtube_uses_video_template(monkeypatch):
    called = {}

    def fake_process_command(**kwargs):
        called.update(kwargs)
        return "", 0.0, {}

    monkeypatch.setattr(cli.core, "process_command", fake_process_command)
    monkeypatch.setattr(cli.youtube, "get_transcript", lambda url, languages=None: [{"text": "hi"}])
    monkeypatch.setattr(cli.youtube, "format_transcript", lambda transcript: "formatted")

    runner = CliRunner()
    result = runner.invoke(cli.summarize, ["https://youtu.be/dQw4w9WgXcQ"])

    assert result.exit_code == 0
    assert called["template"] == "video_summarization"
    assert called["prompt_input"] == "formatted"


def test_summarize_youtube_passes_languages(monkeypatch):
    transcript_args = {}

    def fake_get_transcript(url, languages=None):
        transcript_args["languages"] = languages
        return [{"text": "bonjour"}]

    def fake_process_command(**kwargs):
        return "", 0.0, {}

    monkeypatch.setattr(cli.core, "process_command", fake_process_command)
    monkeypatch.setattr(cli.youtube, "get_transcript", fake_get_transcript)
    monkeypatch.setattr(cli.youtube, "format_transcript", lambda transcript: "text")

    runner = CliRunner()
    result = runner.invoke(cli.summarize, ["-l", "fr", "-l", "en", "https://youtu.be/dQw4w9WgXcQ"])

    assert result.exit_code == 0
    assert transcript_args["languages"] == ("fr", "en")


def test_summarize_youtube_default_languages_is_none(monkeypatch):
    transcript_args = {}

    def fake_get_transcript(url, languages=None):
        transcript_args["languages"] = languages
        return [{"text": "hello"}]

    def fake_process_command(**kwargs):
        return "", 0.0, {}

    monkeypatch.setattr(cli.core, "process_command", fake_process_command)
    monkeypatch.setattr(cli.youtube, "get_transcript", fake_get_transcript)
    monkeypatch.setattr(cli.youtube, "format_transcript", lambda transcript: "text")

    runner = CliRunner()
    result = runner.invoke(cli.summarize, ["https://youtu.be/dQw4w9WgXcQ"])

    assert result.exit_code == 0
    assert transcript_args["languages"] is None


def test_summarize_web_uses_web_fetch(monkeypatch):
    called = {}

    def fake_process_command(**kwargs):
        called.update(kwargs)
        return "", 0.0, {}

    monkeypatch.setattr(cli.core, "process_command", fake_process_command)
    monkeypatch.setattr(cli.web, "fetch_page_text", lambda _: "web content")

    runner = CliRunner()
    result = runner.invoke(cli.summarize, ["https://example.com"])

    assert result.exit_code == 0
    assert called["template"] == "summarize"
    assert called["prompt_input"] == "web content"


@pytest.mark.parametrize("domain", ("ft.com", "example.org"))
def test_summarize_domain_prepends_https(monkeypatch, domain):
    called = {}
    fetched = {}

    def fake_process_command(**kwargs):
        called.update(kwargs)
        return "", 0.0, {}

    def fake_fetch_page_text(url):
        fetched["url"] = url
        return "web content"

    monkeypatch.setattr(cli.core, "process_command", fake_process_command)
    monkeypatch.setattr(cli.web, "fetch_page_text", fake_fetch_page_text)

    runner = CliRunner()
    result = runner.invoke(cli.summarize, [domain])

    assert result.exit_code == 0
    assert fetched["url"] == f"https://{domain}"
    assert called["template"] == "summarize"
    assert called["prompt_input"] == "web content"


def test_summarize_domain_with_path_prepends_https(monkeypatch):
    called = {}
    fetched = {}

    def fake_process_command(**kwargs):
        called.update(kwargs)
        return "", 0.0, {}

    def fake_fetch_page_text(url):
        fetched["url"] = url
        return "web content"

    monkeypatch.setattr(cli.core, "process_command", fake_process_command)
    monkeypatch.setattr(cli.web, "fetch_page_text", fake_fetch_page_text)

    runner = CliRunner()
    result = runner.invoke(cli.summarize, ["example.com/path"])

    assert result.exit_code == 0
    assert fetched["url"] == "https://example.com/path"
    assert called["template"] == "summarize"
    assert called["prompt_input"] == "web content"


def test_summarize_file_uses_file_content(monkeypatch, tmp_path):
    called = {}

    def fake_process_command(**kwargs):
        called.update(kwargs)
        return "", 0.0, {}

    file_path = tmp_path / "input.txt"
    file_path.write_text("file content", encoding="utf-8")

    monkeypatch.setattr(cli.core, "process_command", fake_process_command)

    runner = CliRunner()
    result = runner.invoke(cli.summarize, [str(file_path)])

    assert result.exit_code == 0
    assert called["template"] == "summarize"
    assert called["prompt_input"] == "file content"


def test_summarize_domain_prefers_file(monkeypatch, tmp_path):
    called = {}

    def fake_process_command(**kwargs):
        called.update(kwargs)
        return "", 0.0, {}

    file_path = tmp_path / "data.com"
    file_path.write_text("file content", encoding="utf-8")

    def fail_fetch(*_args, **_kwargs):
        raise AssertionError("fetch_page_text should not be called for files")

    monkeypatch.setattr(cli.core, "process_command", fake_process_command)
    monkeypatch.setattr(cli.web, "fetch_page_text", fail_fetch)

    runner = CliRunner()
    result = runner.invoke(cli.summarize, [str(file_path)])

    assert result.exit_code == 0
    assert called["template"] == "summarize"
    assert called["prompt_input"] == "file content"


def test_summarize_path_like_missing_shows_error(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(cli.summarize, ["./notes.com"])

    assert result.exit_code == 1
    assert "File not found" in result.output


def test_summarize_plain_text_does_not_trigger_domain(monkeypatch, tmp_path):
    called = {}

    def fake_process_command(**kwargs):
        called.update(kwargs)
        return "", 0.0, {}

    def fail_fetch(*_args, **_kwargs):
        raise AssertionError("fetch_page_text should not be called for plain text")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.core, "process_command", fake_process_command)
    monkeypatch.setattr(cli.web, "fetch_page_text", fail_fetch)

    runner = CliRunner()
    result = runner.invoke(cli.summarize, ["notes.txt"])

    assert result.exit_code == 0
    assert called["template"] == "summarize"
    assert called["prompt_input"] == "notes.txt"


def test_summarize_nonexistent_file_shows_error(tmp_path):
    missing_path = tmp_path / "missing.txt"
    runner = CliRunner()
    result = runner.invoke(cli.summarize, [str(missing_path)])

    assert result.exit_code == 1
    assert "File not found" in result.output


def test_load_source_content_empty_returns_empty():
    assert cli.load_source_content(()) == ""


def test_load_source_content_joins_text():
    assert cli.load_source_content(("hello", "world")) == "hello world"


def test_load_source_content_read_error_exits(tmp_path, monkeypatch, capsys):
    file_path = tmp_path / "input.txt"
    file_path.write_text("content", encoding="utf-8")

    def fail_read(*_args, **_kwargs):
        raise OSError("read failed")

    monkeypatch.setattr(Path, "read_text", fail_read)

    with pytest.raises(SystemExit) as exc:
        cli.load_source_content((str(file_path),))

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert "read failed" in captured.err
