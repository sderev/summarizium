import re
import sys
from collections.abc import Sequence
from xml.etree.ElementTree import ParseError

import click

try:
    from youtube_transcript_api import (
        NoTranscriptFound,
        TranscriptsDisabled,
        YouTubeRequestFailed,
        YouTubeTranscriptApi,
    )
except ImportError:  # pragma: no cover - v1.x may not re-export errors
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        NoTranscriptFound,
        TranscriptsDisabled,
        YouTubeRequestFailed,
    )

try:
    from youtube_transcript_api import IpBlocked
except ImportError:  # pragma: no cover - v0.x compatibility
    try:
        from youtube_transcript_api._errors import IpBlocked
    except ImportError:  # pragma: no cover - defensive fallback

        class IpBlocked(Exception):
            """Fallback error for youtube-transcript-api v0.x."""


def _error(message: str) -> None:
    click.secho(f"Error: {message}", fg="red", err=True)


def _warn_line(message: str) -> None:
    click.secho(message, fg="yellow", err=True)


YOUTUBE_URL_PATTERN = re.compile(
    r"(http(s)?:\/\/)?"  # Optional protocol
    r"(www\.)?"  # Optional www subdomain
    r"youtu(be\.com|\.be)"  # Domain variations
    r"(\/watch\?v=|\/|\/embed\/|\/shorts\/|\/live\/)"  # Path variations
    r"(?P<video_id>[a-zA-Z0-9_-]{11})"  # Video ID capture group
)


def is_youtube_video(url: str) -> bool:
    if url is None:
        raise AttributeError("No URL provided.")
    return YOUTUBE_URL_PATTERN.match(url.strip()) is not None


def extract_video_id(youtube_url: str) -> str | None:
    if youtube_url is None:
        return None
    match = YOUTUBE_URL_PATTERN.match(youtube_url.strip())
    if not match:
        return None
    return match.group("video_id")


def _normalize_languages(languages: Sequence[str] | None) -> list[str]:
    if languages is None:
        return ["en"]
    normalized = [language.strip() for language in languages if language and language.strip()]
    return normalized or ["en"]


def _list_transcripts(video_id: str):
    try:
        api = YouTubeTranscriptApi()
    except TypeError:
        api = None

    if api is not None and hasattr(api, "list"):
        return api.list(video_id)
    if hasattr(YouTubeTranscriptApi, "list_transcripts"):
        return YouTubeTranscriptApi.list_transcripts(video_id)
    if api is not None and hasattr(api, "list_transcripts"):
        return api.list_transcripts(video_id)
    raise RuntimeError("Unsupported youtube-transcript-api version.")


def _first_transcript(transcript_list):
    for transcript in transcript_list:
        return transcript
    return None


def _select_transcript(transcript_list, languages: Sequence[str]):
    try:
        return transcript_list.find_transcript(languages)
    except NoTranscriptFound:
        if languages and hasattr(transcript_list, "find_generated_transcript"):
            try:
                return transcript_list.find_generated_transcript(languages)
            except NoTranscriptFound:
                pass
        transcript = _first_transcript(transcript_list)
        if transcript is not None:
            _warn_line("Warning: No transcript for requested languages; using fallback.")
            return transcript
        raise


def get_transcript(
    youtube_url: str,
    languages: Sequence[str] | None = None,
) -> list[dict] | None:
    video_id = extract_video_id(youtube_url)
    if not video_id:
        _error("Invalid YouTube URL.")
        sys.exit(1)

    languages = _normalize_languages(languages)

    try:
        transcript_list = _list_transcripts(video_id)
        transcript = _select_transcript(transcript_list, languages)
        return transcript.fetch()
    except TranscriptsDisabled:
        _error("No transcripts available for this video.")
        click.echo("", err=True)
        _warn_line("Possible reasons:")
        _warn_line("- The video owner has disabled transcripts.")
        _warn_line(
            "- The video is too recent and automatic captions aren't ready yet (can take several hours)."
        )
        _warn_line("- The video language isn't supported for automatic captions.")
        click.echo("", err=True)
        sys.exit(1)
    except IpBlocked:
        _error("YouTube blocked transcript access from this IP.")
        _warn_line("Warning: Try again later or use a different network.")
        sys.exit(1)
    except YouTubeRequestFailed as e:
        _error(f"YouTube request failed: {e}")
        _warn_line("Warning: YouTube may be rate limiting. Try again later.")
        sys.exit(1)
    except NoTranscriptFound:
        _error("No transcript found for the requested languages.")
        _warn_line("Warning: Try different languages or another video.")
        sys.exit(1)
    except ParseError:
        _error("Failed to parse transcript data. Please try again.")
        sys.exit(1)


def format_transcript(transcript: list[dict], timecode: bool = False) -> str:
    return " ".join(
        f"|{line['start']}| {line['text']}" if timecode else line["text"] for line in transcript
    )
