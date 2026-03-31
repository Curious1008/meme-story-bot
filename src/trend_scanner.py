"""Trend scanner — fetches trending topics from Google Trends RSS."""

import logging

import feedparser

from src.models import Trend
from src.safety import is_trend_safe

logger = logging.getLogger(__name__)

GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo=US"


def fetch_google_trends() -> list[Trend]:
    """Parse Google Trends RSS feed and return raw Trend objects."""
    feed = feedparser.parse(GOOGLE_TRENDS_RSS)
    return [
        Trend(title=entry.title, source="google_trends", meme_score=0.0)
        for entry in feed.entries
    ]


def scan_trends() -> list[Trend]:
    """Fetch trends, filter unsafe ones, return safe trends only."""
    try:
        trends = fetch_google_trends()
    except Exception:
        logger.warning("Failed to fetch Google Trends RSS, returning empty list")
        return []

    return [t for t in trends if is_trend_safe(t.title)]
