from click.testing import CliRunner

from summarizium import cli


def test_summarize_youtube_uses_video_template(monkeypatch):
    called = {}

    def fake_process_command(**kwargs):
        called.update(kwargs)
        return "", 0.0, {}

    monkeypatch.setattr(cli.core, "process_command", fake_process_command)
    monkeypatch.setattr(cli.youtube, "get_transcript", lambda _: [{"text": "hi"}])
    monkeypatch.setattr(cli.youtube, "format_transcript", lambda _: "formatted")

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
