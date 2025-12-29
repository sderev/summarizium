import sys

import click
import httpx
from strip_tags.lib import strip_tags

ERROR_PREFIX = click.style("Error:", fg="red")


def fetch_page_text(url: str, timeout: float = 5.0) -> str:
    """
    Fetches a webpage and strips HTML tags from it.
    """
    try:
        response = httpx.get(url, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPError as error:
        click.secho(f"{ERROR_PREFIX} {error}", err=True)
        sys.exit(1)

    return strip_tags(input=response.text, minify=True)
