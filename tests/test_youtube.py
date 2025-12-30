from xml.etree.ElementTree import ParseError

import pytest

from summarizium import youtube


class StubTranscript:
    def __init__(self, data, *, raise_parse: bool = False):
        self._data = data
        self._raise_parse = raise_parse

    def fetch(self):
        if self._raise_parse:
            raise ParseError("bad xml")
        return self._data


class StubTranscriptList:
    def __init__(self, transcript, *, generated=None, items=None):
        self._transcript = transcript
        self._generated = generated
        self._items = items or []

    def find_transcript(self, languages):
        if self._transcript is None:
            raise youtube.NoTranscriptFound()
        return self._transcript

    def find_generated_transcript(self, languages):
        if self._generated is None:
            raise youtube.NoTranscriptFound()
        return self._generated

    def __iter__(self):
        if self._items:
            return iter(self._items)
        return iter([t for t in [self._transcript, self._generated] if t is not None])


def test_extract_video_id_handles_url_variants():
    video_id = "dQw4w9WgXcQ"
    assert youtube.extract_video_id(f"https://www.youtube.com/watch?v={video_id}") == video_id
    assert youtube.extract_video_id(f"https://youtu.be/{video_id}") == video_id
    assert youtube.extract_video_id(f"https://www.youtube.com/shorts/{video_id}") == video_id


def test_get_transcript_v1_list_path(monkeypatch):
    calls = {"list": 0}
    transcript_data = [{"text": "hello", "start": 0.0, "duration": 1.0}]

    class Api:
        def list(self, video_id):
            calls["list"] += 1
            return StubTranscriptList(StubTranscript(transcript_data))

    monkeypatch.setattr(youtube, "YouTubeTranscriptApi", Api)

    result = youtube.get_transcript("https://youtu.be/dQw4w9WgXcQ", ["en"])

    assert result == transcript_data
    assert calls["list"] == 1


def test_get_transcript_v0_list_transcripts_path(monkeypatch):
    calls = {"list_transcripts": 0}
    transcript_data = [{"text": "hello", "start": 0.0, "duration": 1.0}]

    class Api:
        @staticmethod
        def list_transcripts(video_id):
            calls["list_transcripts"] += 1
            return StubTranscriptList(StubTranscript(transcript_data))

    monkeypatch.setattr(youtube, "YouTubeTranscriptApi", Api)

    result = youtube.get_transcript("https://youtu.be/dQw4w9WgXcQ", ["en"])

    assert result == transcript_data
    assert calls["list_transcripts"] == 1


def test_get_transcript_language_fallback_generated(monkeypatch):
    class StubNoTranscriptFound(Exception):
        pass

    monkeypatch.setattr(youtube, "NoTranscriptFound", StubNoTranscriptFound)

    transcript_data = [{"text": "generated", "start": 0.0, "duration": 1.0}]
    transcript_list = StubTranscriptList(
        None,
        generated=StubTranscript(transcript_data),
    )

    monkeypatch.setattr(youtube, "_list_transcripts", lambda _: transcript_list)

    result = youtube.get_transcript("https://youtu.be/dQw4w9WgXcQ", ["fr"])

    assert result == transcript_data


def test_get_transcript_language_fallback_first(monkeypatch, capsys):
    class StubNoTranscriptFound(Exception):
        pass

    monkeypatch.setattr(youtube, "NoTranscriptFound", StubNoTranscriptFound)

    transcript_data = [{"text": "fallback", "start": 0.0, "duration": 1.0}]
    fallback_transcript = StubTranscript(transcript_data)
    transcript_list = StubTranscriptList(None, items=[fallback_transcript])

    monkeypatch.setattr(youtube, "_list_transcripts", lambda _: transcript_list)

    result = youtube.get_transcript("https://youtu.be/dQw4w9WgXcQ", ["fr"])

    captured = capsys.readouterr()
    assert result == transcript_data
    assert "fallback" in captured.err


def test_get_transcript_parse_error_exits(monkeypatch, capsys):
    transcript_list = StubTranscriptList(StubTranscript([], raise_parse=True))
    monkeypatch.setattr(youtube, "_list_transcripts", lambda _: transcript_list)

    with pytest.raises(SystemExit) as exc:
        youtube.get_transcript("https://youtu.be/dQw4w9WgXcQ", ["en"])

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert "Failed to parse transcript data" in captured.err


def test_get_transcript_transcripts_disabled_exits(monkeypatch, capsys):
    class StubTranscriptsDisabled(Exception):
        pass

    monkeypatch.setattr(youtube, "TranscriptsDisabled", StubTranscriptsDisabled)
    monkeypatch.setattr(
        youtube,
        "_list_transcripts",
        lambda _: (_ for _ in ()).throw(StubTranscriptsDisabled()),
    )

    with pytest.raises(SystemExit) as exc:
        youtube.get_transcript("https://youtu.be/dQw4w9WgXcQ", ["en"])

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert "No transcripts available" in captured.err


def test_get_transcript_ip_blocked_exits(monkeypatch, capsys):
    class StubIpBlocked(Exception):
        pass

    monkeypatch.setattr(youtube, "IpBlocked", StubIpBlocked)
    monkeypatch.setattr(
        youtube,
        "_list_transcripts",
        lambda _: (_ for _ in ()).throw(StubIpBlocked()),
    )

    with pytest.raises(SystemExit) as exc:
        youtube.get_transcript("https://youtu.be/dQw4w9WgXcQ", ["en"])

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert "blocked transcript access" in captured.err


def test_get_transcript_no_transcript_found_exits(monkeypatch, capsys):
    class StubNoTranscriptFound(Exception):
        pass

    monkeypatch.setattr(youtube, "NoTranscriptFound", StubNoTranscriptFound)

    class TranscriptList:
        def find_transcript(self, languages):
            raise StubNoTranscriptFound()

        def __iter__(self):
            return iter([])

    monkeypatch.setattr(youtube, "_list_transcripts", lambda _: TranscriptList())

    with pytest.raises(SystemExit) as exc:
        youtube.get_transcript("https://youtu.be/dQw4w9WgXcQ", ["de"])

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert "No transcript found" in captured.err


def test_is_youtube_video_requires_url():
    with pytest.raises(AttributeError):
        youtube.is_youtube_video(None)


@pytest.mark.parametrize("value", [None, "not a url"])
def test_extract_video_id_returns_none_for_invalid(value):
    assert youtube.extract_video_id(value) is None


def test_get_transcript_invalid_url_exits(capsys):
    with pytest.raises(SystemExit) as exc:
        youtube.get_transcript("not-a-url")

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert "Invalid YouTube URL." in captured.err


def test_get_transcript_defaults_language_to_en(monkeypatch):
    transcript_data = [{"text": "hello", "start": 0.0, "duration": 1.0}]
    captured = {}

    monkeypatch.setattr(youtube, "_list_transcripts", lambda _: "list")

    def fake_select(_list, languages):
        captured["languages"] = languages
        return StubTranscript(transcript_data)

    monkeypatch.setattr(youtube, "_select_transcript", fake_select)

    result = youtube.get_transcript("https://youtu.be/dQw4w9WgXcQ")

    assert result == transcript_data
    assert captured["languages"] == ["en"]


def test_list_transcripts_type_error_uses_class_method(monkeypatch):
    class Api:
        def __init__(self):
            raise TypeError("bad init")

        @staticmethod
        def list_transcripts(video_id):
            return f"class:{video_id}"

    monkeypatch.setattr(youtube, "YouTubeTranscriptApi", Api)

    assert youtube._list_transcripts("video") == "class:video"


def test_list_transcripts_instance_list_transcripts(monkeypatch):
    class Api:
        def __init__(self):
            self.list_transcripts = lambda video_id: f"instance:{video_id}"

    monkeypatch.setattr(youtube, "YouTubeTranscriptApi", Api)

    assert youtube._list_transcripts("video") == "instance:video"


def test_list_transcripts_unsupported_version_raises(monkeypatch):
    class Api:
        def __init__(self):
            self.other = None

    monkeypatch.setattr(youtube, "YouTubeTranscriptApi", Api)

    with pytest.raises(RuntimeError) as exc:
        youtube._list_transcripts("video")

    assert "Unsupported youtube-transcript-api version." in str(exc.value)


def test_get_transcript_request_failed_exits(monkeypatch, capsys):
    class StubRequestFailed(Exception):
        pass

    monkeypatch.setattr(youtube, "YouTubeRequestFailed", StubRequestFailed)
    monkeypatch.setattr(
        youtube,
        "_list_transcripts",
        lambda _: (_ for _ in ()).throw(StubRequestFailed("rate limited")),
    )

    with pytest.raises(SystemExit) as exc:
        youtube.get_transcript("https://youtu.be/dQw4w9WgXcQ", ["en"])

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert "YouTube request failed: rate limited" in captured.err


@pytest.mark.parametrize(
    "timecode, expected",
    [
        (False, "Hello world"),
        (True, "|0.0| Hello |1.5| world"),
    ],
)
def test_format_transcript(timecode, expected):
    transcript = [
        {"text": "Hello", "start": 0.0},
        {"text": "world", "start": 1.5},
    ]

    assert youtube.format_transcript(transcript, timecode=timecode) == expected
