"""Tests for trend scanner module."""

from unittest.mock import patch, MagicMock

from src.models import Trend
from src.trend_scanner import fetch_google_trends, scan_trends


# --- fetch_google_trends ---


def _make_feed(entries):
    """Build a fake feedparser result with the given entry titles."""
    feed = MagicMock()
    feed.bozo = False
    feed.entries = [MagicMock(title=t) for t in entries]
    return feed


def test_fetch_parses_rss_entries():
    titles = ["Taylor Swift", "Bitcoin 100k", "Cat meme"]
    with patch("src.trend_scanner.feedparser.parse", return_value=_make_feed(titles)):
        trends = fetch_google_trends()

    assert len(trends) == 3
    for trend, title in zip(trends, titles):
        assert isinstance(trend, Trend)
        assert trend.title == title
        assert trend.source == "google_trends"
        assert trend.meme_score == 0.0


def test_fetch_handles_empty_feed():
    with patch("src.trend_scanner.feedparser.parse", return_value=_make_feed([])):
        trends = fetch_google_trends()

    assert trends == []


# --- scan_trends ---


def test_scan_trends_filters_unsafe():
    titles = ["Fun meme", "Mass shooting at mall", "Cat videos"]
    with patch("src.trend_scanner.feedparser.parse", return_value=_make_feed(titles)):
        trends = scan_trends()

    result_titles = [t.title for t in trends]
    assert "Fun meme" in result_titles
    assert "Cat videos" in result_titles
    assert "Mass shooting at mall" not in result_titles


def test_scan_trends_handles_rss_failure():
    with patch("src.trend_scanner.feedparser.parse", side_effect=Exception("Network error")):
        trends = scan_trends()

    assert trends == []
