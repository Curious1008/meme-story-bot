"""Score trending topics for meme potential using Claude."""

import json
import logging

import anthropic

from src.config import ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL
from src.models import Trend

logger = logging.getLogger(__name__)

SCORE_PROMPT = (
    "Rate this trending topic for meme potential on a scale of 1-10. "
    "High scores = absurd, controversial, remix-able, funny. "
    "Low scores = boring, serious news, not memeable. "
    'Topic: {title}. Respond as JSON: {{"score": N, "reason": "one sentence"}}'
)


def get_client() -> anthropic.Anthropic:
    """Create Anthropic client with API key from config."""
    kwargs = {"api_key": ANTHROPIC_API_KEY}
    if ANTHROPIC_BASE_URL:
        kwargs["base_url"] = ANTHROPIC_BASE_URL
    return anthropic.Anthropic(**kwargs)


def score_trends(trends: list[Trend], min_score: float = 5.0) -> list[Trend]:
    """Score each trend for meme potential, filter, and sort descending.

    Calls Claude for each trend. On API failure, the trend gets score 0.0
    and will be filtered out.
    """
    client = get_client()

    for trend in trends:
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                messages=[{"role": "user", "content": SCORE_PROMPT.format(title=trend.title)}],
            )
            data = json.loads(response.content[0].text)
            trend.meme_score = float(data["score"])
        except Exception:
            logger.warning("Failed to score trend %r, assigning score 0.0", trend.title)
            trend.meme_score = 0.0

    scored = [t for t in trends if t.meme_score >= min_score]
    scored.sort(key=lambda t: t.meme_score, reverse=True)
    return scored
