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
    monkeypatch.setattr(cli.youtube, "get_transcript", lambda url: [{"text": "hi"}])
    monkeypatch.setattr(cli.youtube, "format_transcript", lambda transcript: "formatted")

    runner = CliRunner()
    result = runner.invoke(cli.summarize, ["https://youtu.be/dQw4w9WgXcQ"])

    assert result.exit_code == 0
    assert called["template"] == "video_summarization"
    assert called["prompt_input"] == "formatted"


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


def test_summarize_nonexistent_file_shows_error():
    runner = CliRunner()
    result = runner.invoke(cli.summarize, ["/nonexistent/path/file.txt"])

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
