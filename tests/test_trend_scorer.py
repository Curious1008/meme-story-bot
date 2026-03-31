"""Tests for trend scorer module."""

import json
from unittest.mock import patch, MagicMock

import pytest

from src.models import Trend
from src.trend_scorer import get_client, score_trends


# --- get_client ---


def test_get_client_returns_anthropic_client():
    with patch("src.trend_scorer.anthropic.Anthropic") as mock_cls:
        mock_cls.return_value = MagicMock()
        client = get_client()
        mock_cls.assert_called_once_with(api_key=pytest.importorskip("src.config").ANTHROPIC_API_KEY)
        assert client is mock_cls.return_value


# --- score_trends ---


def _make_trend(title: str) -> Trend:
    return Trend(title=title, source="google_trends", meme_score=0.0)


def _mock_response(score: float, reason: str = "test reason"):
    """Build a fake Anthropic messages.create response."""
    resp = MagicMock()
    resp.content = [MagicMock(text=json.dumps({"score": score, "reason": reason}))]
    return resp


def test_score_trends_returns_sorted_highest_first():
    trends = [_make_trend("Boring news"), _make_trend("Dank meme"), _make_trend("Mid topic")]
    responses = [_mock_response(3.0), _mock_response(9.0), _mock_response(6.0)]

    with patch("src.trend_scorer.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = responses
        mock_get.return_value = mock_client

        result = score_trends(trends, min_score=0.0)

    assert len(result) == 3
    assert result[0].meme_score == 9.0
    assert result[1].meme_score == 6.0
    assert result[2].meme_score == 3.0


def test_score_trends_filters_below_min_score():
    trends = [_make_trend("Great meme"), _make_trend("Boring stuff")]
    responses = [_mock_response(8.0), _mock_response(3.0)]

    with patch("src.trend_scorer.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = responses
        mock_get.return_value = mock_client

        result = score_trends(trends, min_score=5.0)

    assert len(result) == 1
    assert result[0].title == "Great meme"
    assert result[0].meme_score == 8.0


def test_score_trends_handles_api_failure_gracefully():
    trends = [_make_trend("Topic A"), _make_trend("Topic B")]

    with patch("src.trend_scorer.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API error")
        mock_get.return_value = mock_client

        result = score_trends(trends, min_score=5.0)

    # All trends get score 0.0 on failure, filtered out by min_score
    assert result == []
