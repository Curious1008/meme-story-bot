"""LLM quality eval tests — require ANTHROPIC_API_KEY and RUN_EVALS=1."""

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY") or not os.getenv("RUN_EVALS"),
    reason="Eval tests require ANTHROPIC_API_KEY and RUN_EVALS=1",
)

from src.models import Trend
from src.trend_scorer import score_trends
from src.content_generator import generate_opening


NEWS_WORDS = ["according to", "officials say", "reports indicate", "sources confirm"]


def test_eval_scorer_ranks_absurd_higher():
    """Absurd trend should score higher than boring corporate news."""
    absurd = Trend(
        title="Tech CEO live-tweets divorce",
        source="google_trends",
        meme_score=0.0,
    )
    boring = Trend(
        title="Company Q3 earnings beat estimates by 2%",
        source="google_trends",
        meme_score=0.0,
    )

    # Score both (min_score=0 so neither gets filtered)
    scored = score_trends([absurd, boring], min_score=0.0)

    # Find scores by title
    scores = {t.title: t.meme_score for t in scored}
    assert scores[absurd.title] > scores[boring.title], (
        f"Absurd ({scores[absurd.title]}) should score higher than boring ({scores[boring.title]})"
    )


def test_eval_opening_is_meme_style():
    """Generated opening should be meme-style, not news-style."""
    trend = Trend(
        title="Billionaire launches car into sun",
        source="google_trends",
        meme_score=9.5,
    )

    tweet, options = generate_opening(trend, episode_number=42)

    # Must be tweet-length
    assert len(tweet) <= 280, f"Tweet is {len(tweet)} chars, must be <=280"

    # Must have 2-4 poll options
    assert 2 <= len(options) <= 4, f"Expected 2-4 options, got {len(options)}"

    # Must not use news-style language
    lower_tweet = tweet.lower()
    for phrase in NEWS_WORDS:
        assert phrase not in lower_tweet, (
            f"Tweet contains news-style phrase '{phrase}': {tweet}"
        )
