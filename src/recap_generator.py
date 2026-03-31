"""Daily recap tweet generator using Claude."""

import json
import logging
from collections import Counter
from typing import Optional

import anthropic

from src.config import ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL
from src.models import Episode

logger = logging.getLogger(__name__)

RECAP_SYSTEM = (
    "You write daily recap tweets for a meme game show on Twitter. "
    "Be brief, funny, mention MVPs by @username. Under 280 chars. JSON only."
)


def get_client() -> anthropic.Anthropic:
    """Create Anthropic client with API key from config."""
    kwargs = {"api_key": ANTHROPIC_API_KEY}
    if ANTHROPIC_BASE_URL:
        kwargs["base_url"] = ANTHROPIC_BASE_URL
    return anthropic.Anthropic(**kwargs)


def generate_daily_recap(episodes: list[Episode]) -> Optional[str]:
    """Generate a daily recap tweet summarizing completed episodes.

    Args:
        episodes: List of today's completed episodes.

    Returns:
        Recap tweet text, or None if no episodes provided.
    """
    if not episodes:
        return None

    # Aggregate contributors across all episodes
    contributor_counts: Counter[str] = Counter()
    for ep in episodes:
        contributor_counts.update(ep.contributors)

    # Top 3 contributors by count
    top_contributors = [name for name, _ in contributor_counts.most_common(3)]

    # Build episode summaries
    episode_lines = []
    for ep in episodes:
        episode_lines.append(
            f"EP #{ep.episode_number}: \"{ep.trend.title}\" ({len(ep.rounds)} rounds)"
        )
    episodes_summary = "\n".join(episode_lines)

    prompt = (
        f"Write a daily recap tweet for today's meme game show.\n"
        f"Episodes today:\n{episodes_summary}\n"
        f"Top contributors (MVPs): {', '.join(top_contributors) if top_contributors else 'none'}\n"
        f"Respond with JSON: {{\"tweet\": \"...\"}}"
    )

    client = get_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=RECAP_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    data = json.loads(response.content[0].text)
    return data["tweet"]
