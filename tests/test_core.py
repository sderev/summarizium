import io
import json
import sys

from summarizium import core


class TTYStdin(io.StringIO):
    def isatty(self) -> bool:
        return True


class TTYStdout(io.StringIO):
    def isatty(self) -> bool:
        return True


class NonTTYStdout(io.StringIO):
    def isatty(self) -> bool:
        return False


def test_ensure_templates_installed_writes_config_and_templates(tmp_path, monkeypatch):
    monkeypatch.setattr(core.Path, "home", lambda: tmp_path)
    config_file = tmp_path / ".config" / "lmt" / "config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text("{", encoding="utf-8")

    core.ensure_templates_installed.cache_clear()
    core.ensure_templates_installed()

    config = json.loads(config_file.read_text(encoding="utf-8"))
    assert "tools" in config

    for template in core.PROMPTS_DIR.glob("*.yaml"):
        destination = tmp_path / ".config" / "lmt" / "templates" / template.name
        assert destination.exists()
        assert config["tools"][template.stem] == str(destination)


def test_ensure_templates_installed_updates_existing(tmp_path, monkeypatch):
    monkeypatch.setattr(core.Path, "home", lambda: tmp_path)
    dest_dir = tmp_path / ".config" / "lmt" / "templates"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for template in core.PROMPTS_DIR.glob("*.yaml"):
        (dest_dir / template.name).write_text("present", encoding="utf-8")

    config_file = tmp_path / ".config" / "lmt" / "config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps({"tools": {"keep": "value"}}), encoding="utf-8")

    core.ensure_templates_installed.cache_clear()
    core.ensure_templates_installed()

    config = json.loads(config_file.read_text(encoding="utf-8"))
    assert config["tools"]["keep"] == "value"
    for template in core.PROMPTS_DIR.glob("*.yaml"):
        destination = dest_dir / template.name
        assert destination.read_text(encoding="utf-8") == template.read_text(encoding="utf-8")
        assert config["tools"][template.stem] == str(destination)


def test_process_command_normalizes_prompt_and_forces_no_stream(monkeypatch):
    called = {}

    def fake_prepare_and_generate_response(**kwargs):
        called.update(kwargs)
        return "ok"

    def fake_ensure_templates_installed():
        called["templates"] = called.get("templates", 0) + 1

    monkeypatch.setattr(core, "prepare_and_generate_response", fake_prepare_and_generate_response)
    monkeypatch.setattr(core, "ensure_templates_installed", fake_ensure_templates_installed)
    monkeypatch.setattr(sys, "stdout", NonTTYStdout())

    result = core.process_command(
        template="summarize",
        model="test-model",
        emoji=True,
        prompt_input=(" Hello ", "world"),
        temperature=0.3,
        tokens=True,
        no_stream=False,
        raw=True,
        debug=False,
    )

    assert result == "ok"
    assert called["templates"] == 1
    assert called["prompt_input"] == "Hello world"
    assert called["no_stream"] is True
    assert called["template"] == "summarize"
    assert called["model"] == "test-model"
    assert called["emoji"] is True
    assert called["temperature"] == 0.3
    assert called["tokens"] is True
    assert called["raw"] is True
    assert called["debug"] is False


def test_process_command_reads_from_stdin_when_piped(monkeypatch):
    called = {}

    def fake_prepare_and_generate_response(**kwargs):
        called.update(kwargs)
        return "ok"

    monkeypatch.setattr(core, "prepare_and_generate_response", fake_prepare_and_generate_response)
    monkeypatch.setattr(core, "ensure_templates_installed", lambda: None)
    monkeypatch.setattr(sys, "stdin", io.StringIO("piped content"))
    monkeypatch.setattr(sys, "stdout", TTYStdout())

    core.process_command(
        template="summarize",
        model="test-model",
        emoji=False,
        prompt_input=None,
        temperature=0.2,
        tokens=False,
        no_stream=False,
        raw=False,
        debug=False,
    )

    assert called["prompt_input"] == "piped content"
    assert called["no_stream"] is False


def test_process_command_reads_from_tty_prompt(monkeypatch):
    called = {}

    def fake_prepare_and_generate_response(**kwargs):
        called.update(kwargs)
        return "ok"

    monkeypatch.setattr(core, "prepare_and_generate_response", fake_prepare_and_generate_response)
    monkeypatch.setattr(core, "ensure_templates_installed", lambda: None)
    monkeypatch.setattr(sys, "stdin", TTYStdin("typed input\n"))
    monkeypatch.setattr(sys, "stdout", TTYStdout())

    core.process_command(
        template="summarize",
        model="test-model",
        emoji=False,
        prompt_input="",
        temperature=0.2,
        tokens=False,
        no_stream=True,
        raw=False,
        debug=True,
    )

    assert called["prompt_input"] == "typed input"
    assert called["no_stream"] is True
