import json
import shutil
import sys
from functools import lru_cache
from pathlib import Path

import click
from lmterminal.lib import prepare_and_generate_response

from .prompts import PROMPTS_DIR

ERROR_PREFIX = click.style("Error:", fg="red")


@lru_cache(maxsize=1)
def ensure_templates_installed() -> None:
    """
    Install and refresh prompt templates in the lmterminal templates directory.
    """
    dest_path = Path.home() / ".config" / "lmt" / "templates"
    dest_path.mkdir(parents=True, exist_ok=True)

    config_file = Path.home() / ".config" / "lmt" / "config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.touch(exist_ok=True)

    try:
        with config_file.open("r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError:
        config = {}

    config.setdefault("tools", {})

    for file in PROMPTS_DIR.glob("*.yaml"):
        destination = dest_path / file.name
        template_name = file.stem
        destination_exists = destination.exists()
        needs_update = not destination_exists or destination.read_text(
            encoding="utf-8"
        ) != file.read_text(encoding="utf-8")

        if needs_update:
            shutil.copy2(file, destination)
            action = "Installed" if not destination_exists else "Updated"
            click.secho(f"{action} `{template_name}` template.", fg="green")

        config["tools"][template_name] = str(destination)

    with config_file.open("w", encoding="utf-8") as file:
        json.dump(config, file, indent=4)


def process_command(
    template: str,
    model: str,
    emoji: bool,
    prompt_input: str | list[str] | tuple[str, ...],
    temperature: float,
    tokens: bool,
    no_stream: bool,
    raw: bool,
    debug: bool,
):
    """
    Process a given command using a specific template and optional input.
    """
    ensure_templates_installed()

    if isinstance(prompt_input, (list, tuple)):
        prompt_input = "".join(prompt_input)
    elif prompt_input is None:
        prompt_input = ""

    prompt_input = str(prompt_input).strip()

    if not prompt_input:
        if not sys.stdin.isatty():
            prompt_input = sys.stdin.read()
        elif sys.stdin.isatty():
            click.secho(
                "You can paste your prompt below. Press <Enter> to skip a line.\n"
                "Once you've done, press Ctrl+D to send it.",
                fg="yellow",
            )
            click.echo("---")
            prompt_input = sys.stdin.read().strip()
            click.echo()

    if not sys.stdout.isatty():
        no_stream = True

    return prepare_and_generate_response(
        system=None,
        template=template,
        model=model,
        prompt_input=prompt_input,
        emoji=emoji,
        temperature=temperature,
        tokens=tokens,
        no_stream=no_stream,
        raw=raw,
        debug=debug,
    )
