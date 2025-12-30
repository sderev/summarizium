import sys
from pathlib import Path

import click
import validators
from lmterminal.cli import validate_model_name, validate_temperature
from lmterminal.lib import DEFAULT_MODEL

from . import core, web, youtube

ERROR_PREFIX = click.style("Error:", fg="red")


def _looks_like_file_path(text: str) -> bool:
    """Check if text looks like a file path."""
    return "/" in text or text.startswith("~") or text.startswith(".")


def load_source_content(source: tuple[str, ...]) -> str:
    """
    Load source content from a file path or return joined text.
    """
    if not source:
        return ""

    if len(source) == 1:
        candidate = Path(source[0]).expanduser()
        if candidate.is_file():
            try:
                return candidate.read_text(encoding="utf-8")
            except OSError as error:
                click.secho(f"{ERROR_PREFIX} {error}", err=True)
                sys.exit(1)
        elif _looks_like_file_path(source[0]) and not candidate.exists():
            click.secho(f"{ERROR_PREFIX} File not found: {source[0]}", err=True)
            sys.exit(1)

    return " ".join(source)


@click.command()
@click.argument("source", nargs=-1, required=False)
@click.option("--emoji", is_flag=True, help="Add emotions and emojis.")
@click.option(
    "-m",
    "--model",
    default=DEFAULT_MODEL,
    help="The model to use for the requests.",
    callback=validate_model_name,
)
@click.option(
    "--temperature",
    callback=validate_temperature,
    default=1,
    type=float,
    help="The temperature to use for the requests.",
    show_default=True,
)
@click.option(
    "--tokens",
    is_flag=True,
    help="Count the number of tokens in the prompt, and display the cost of the request.",
)
@click.option(
    "--no-stream",
    is_flag=True,
    default=False,
    help="Disable the streaming of the response.",
)
@click.option(
    "--raw",
    "-r",
    is_flag=True,
    default=False,
    help="Disable colors and formatting, and print the raw response.",
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Print debug information.",
)
def summarize(
    source: tuple[str, ...],
    model: str,
    emoji: bool,
    temperature: float,
    tokens: bool,
    no_stream: bool,
    raw: bool,
    debug: bool,
) -> None:
    """
    Summarize text, a file, a YouTube video, or a webpage.
    """
    template = "summarize"
    source_str = " ".join(source).strip()
    prompt_input = ""

    if source_str and youtube.is_youtube_video(source_str):
        transcript = youtube.get_transcript(source_str)
        prompt_input = youtube.format_transcript(transcript)
        template = "video_summarization"
    elif source_str and validators.url(source_str):
        prompt_input = web.fetch_page_text(source_str)
    else:
        prompt_input = load_source_content(source)

    core.process_command(
        template=template,
        model=model,
        emoji=emoji,
        prompt_input=prompt_input,
        temperature=temperature,
        tokens=tokens,
        no_stream=no_stream,
        raw=raw,
        debug=debug,
    )
