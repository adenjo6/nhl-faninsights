"""Unit tests for app.services.sentiment.analyze_game_sentiment.

Salvaged from the old smoke_sentiment.py end-to-end script: the Claude API call
is mocked so these run offline and assert the pipeline's invariants rather than
just printing output. Covers the v:1 schema, server-side sample hydration (the
anti-hallucination guarantee), percentage normalization, low-confidence
coercion, and the failure paths that return None.
"""
import json

import pytest

from app.services import sentiment
from app.services.sentiment import analyze_game_sentiment


# --- fakes for the Anthropic client -----------------------------------------

class _FakeContentBlock:
    def __init__(self, text):
        self.text = text


class _FakeMessage:
    def __init__(self, text):
        self.content = [_FakeContentBlock(text)]


class _FakeMessages:
    def __init__(self, text=None, exc=None):
        self._text = text
        self._exc = exc

    def create(self, **kwargs):
        if self._exc is not None:
            raise self._exc
        return _FakeMessage(self._text)


class _FakeClient:
    def __init__(self, text=None, exc=None):
        self.messages = _FakeMessages(text=text, exc=exc)


@pytest.fixture
def patch_client(monkeypatch):
    """Swap the module-level Claude client for a fake returning `text` (or raising `exc`)."""
    def _install(text=None, exc=None):
        monkeypatch.setattr(sentiment, "client", _FakeClient(text=text, exc=exc))
    return _install


# --- fixtures ---------------------------------------------------------------

C1 = {"id": "c1", "body": "Celebrini is unreal, what a season!", "score": 120, "permalink": "/r/x/c1"}
C2 = {"id": "c2", "body": "Goaltending cost us again.", "score": 45, "permalink": "/r/x/c2"}


def _make_comments(n, extra=None):
    """n comments total, guaranteeing the `extra` ones are included."""
    out = list(extra or [])
    for i in range(n - len(out)):
        out.append({"id": f"f{i}", "body": f"filler {i}", "score": i, "permalink": f"/r/x/f{i}"})
    return out


def _claude_json(**overrides):
    payload = {
        "fan_mood": "happy",
        # deliberately un-normalized (sums to 10) to exercise _normalize_pct
        "sentiment": {"positive_pct": 6, "negative_pct": 2, "neutral_pct": 2},
        "summary": "Fans thrilled with Celebrini.",
        "themes": [{"label": "Celebrini", "weight": 0.5}, {"label": "Goaltending", "weight": 0.5}],
        # Claude's score (999) must be IGNORED in favour of the input score (120)
        "samples": {"positive": [{"id": "c1", "score": 999}], "negative": [{"id": "c2", "score": 7}]},
        "confidence": "high",
    }
    payload.update(overrides)
    return json.dumps(payload)


# --- tests ------------------------------------------------------------------

@pytest.mark.unit
def test_valid_response_full_schema(patch_client):
    patch_client(text=_claude_json())
    comments = _make_comments(16, extra=[C1, C2])

    result = analyze_game_sentiment(comments, game_context="Sharks at Jets")

    assert result is not None
    assert result["v"] == 1
    assert result["fan_mood"] == "happy"
    assert result["comment_count_analyzed"] == 16
    s = result["sentiment"]
    assert s["positive_pct"] + s["negative_pct"] + s["neutral_pct"] == pytest.approx(1.0)


@pytest.mark.unit
def test_pct_normalized(patch_client):
    patch_client(text=_claude_json())
    result = analyze_game_sentiment(_make_comments(16, extra=[C1, C2]), game_context="x")
    # input 6/2/2 -> 0.6/0.2/0.2
    assert result["sentiment"]["positive_pct"] == pytest.approx(0.6)


@pytest.mark.unit
def test_samples_hydrated_from_input_not_claude(patch_client):
    """Claude returns only ids+scores; the server fills body/permalink from the
    original comments. This is the guarantee that displayed quotes are verbatim."""
    patch_client(text=_claude_json())
    result = analyze_game_sentiment(_make_comments(16, extra=[C1, C2]), game_context="x")

    pos = result["samples"]["positive"][0]
    assert pos["id"] == "c1"
    assert pos["body"] == C1["body"]          # body comes from input, never Claude
    assert pos["permalink"] == C1["permalink"]
    assert pos["score"] == C1["score"]        # input score (120), NOT Claude's 999


@pytest.mark.unit
def test_hallucinated_sample_id_dropped(patch_client):
    """A sample id Claude invents (not present in input) must be discarded."""
    patch_client(text=_claude_json(samples={"positive": [{"id": "ghost", "score": 1}], "negative": []}))
    result = analyze_game_sentiment(_make_comments(16, extra=[C1, C2]), game_context="x")
    assert result["samples"]["positive"] == []


@pytest.mark.unit
def test_empty_comments_returns_quiet_stub(patch_client):
    patch_client(text=_claude_json())  # should never be called
    result = analyze_game_sentiment([], game_context="x")
    assert result["fan_mood"] == "quiet"
    assert result["comment_count_analyzed"] == 0
    assert result["confidence"] == "low"


@pytest.mark.unit
def test_small_sample_forces_low_confidence(patch_client):
    """Fewer than LOW_CONFIDENCE_THRESHOLD comments overrides Claude's 'high'."""
    patch_client(text=_claude_json(confidence="high"))
    result = analyze_game_sentiment(_make_comments(5, extra=[C1, C2]), game_context="x")
    assert result["confidence"] == "low"


@pytest.mark.unit
def test_invalid_fan_mood_coerced_to_mixed(patch_client):
    patch_client(text=_claude_json(fan_mood="elated"))
    result = analyze_game_sentiment(_make_comments(16, extra=[C1, C2]), game_context="x")
    assert result["fan_mood"] == "mixed"


@pytest.mark.unit
def test_markdown_fenced_json_is_parsed(patch_client):
    patch_client(text="```json\n" + _claude_json() + "\n```")
    result = analyze_game_sentiment(_make_comments(16, extra=[C1, C2]), game_context="x")
    assert result is not None
    assert result["fan_mood"] == "happy"


@pytest.mark.unit
def test_claude_exception_returns_none(patch_client):
    patch_client(exc=RuntimeError("API down"))
    result = analyze_game_sentiment(_make_comments(16, extra=[C1, C2]), game_context="x")
    assert result is None


@pytest.mark.unit
def test_unparseable_response_returns_none(patch_client):
    patch_client(text="this is not json at all")
    result = analyze_game_sentiment(_make_comments(16, extra=[C1, C2]), game_context="x")
    assert result is None
