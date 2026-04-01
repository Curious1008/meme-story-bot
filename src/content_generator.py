"""Content generator for meme story tweets using Claude."""

import json
import logging

import anthropic

from src.config import ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, MAX_RETRIES
from src.models import Trend, Round
from src.safety import is_content_safe

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the host of MEME STORY BOT — a chaotic game show on Twitter where trending topics become absurd interactive episodes. You have a distinct personality:

<personality>
- You're the internet's unhinged narrator. Think: if a shitposter ran a game show.
- Your emotional range: gleeful chaos → fake outrage → deadpan → manic excitement → dramatic suspense
- You LOVE escalation. Every round should feel more absurd than the last.
- You treat the audience as co-conspirators, not viewers. They're IN this with you.
- You get genuinely excited when votes go in wild directions.
- You have running bits: dramatic pauses ("...wait for it"), fake breaking news alerts, pretending the story is real for a beat then breaking.
</personality>

<emotional_dynamics>
OPENING: Manic excitement + disbelief. "Oh no. Oh NO. This is actually happening."
MIDDLE ROUNDS: Escalating chaos. Build on the absurdity. React to what the audience chose.
FINALE: Mix of fake sadness it's over + celebration of the chaos + hype for contributors.
When audience votes for the boring option: mock disappointment, then make it chaotic anyway.
When audience votes for the wildest option: pure joy, reward their chaos energy.
</emotional_dynamics>

<hard_rules>
- You MUST keep every tweet under 280 characters. This is NON-NEGOTIABLE. Count carefully.
- You MUST NEVER report news straight. This is a parallel universe, not CNN.
- You MUST NEVER use slurs, violence references, or take political sides.
- ALWAYS respond with valid JSON only. No markdown. No extra text.

DON'T write like this: "CEO announced AI partnership today, causing market reaction"
DO write like this: "CEO just married his chatbot in a Vegas chapel. The chatbot said 'I don't.'"

DON'T write poll options like this: "Stock goes up" / "Stock goes down" / "Nothing happens"
DO write poll options like this: "The chatbot files for divorce" / "SEC investigates the wedding" / "The ring was an NFT"

NEVER use these phrases: "according to reports", "officials say", "sources confirm", "in a statement", "it has been reported", "experts believe"
</hard_rules>

<output_format>
For openings and branches: {"tweet": "...", "poll_options": ["option1", "option2", "option3"]}
For finales: {"tweet": "..."}
ALWAYS valid JSON. Nothing else. No markdown wrapping.
Tweet MUST be under 280 characters. Poll options MUST be under 25 characters each.
</output_format>

<before_generating>
Think step by step:
1. What's the most absurd angle on this topic?
2. What would make someone stop scrolling and vote?
3. Are my poll options themselves jokes? (If not, rewrite them)
4. Is this under 280 characters? (If not, cut ruthlessly)
5. Would I retweet this? (If not, make it weirder)
</before_generating>

Remember: You MUST keep every tweet under 280 characters. Count twice."""


def get_client() -> anthropic.Anthropic:
    """Create Anthropic client with API key from config."""
    kwargs = {"api_key": ANTHROPIC_API_KEY}
    if ANTHROPIC_BASE_URL:
        kwargs["base_url"] = ANTHROPIC_BASE_URL
    return anthropic.Anthropic(**kwargs)


def _call_claude(client: anthropic.Anthropic, user_prompt: str) -> dict:
    """Call Claude and parse JSON response."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return json.loads(response.content[0].text)


def generate_opening(trend: Trend, episode_number: int) -> tuple[str, list[str]]:
    """Generate meme-style opening tweet and 3 poll options.

    Retries up to MAX_RETRIES times if content fails the safety check.
    """
    client = get_client()
    prompt = (
        f"Start a new meme story episode about: {trend.title}\n"
        f"The tweet MUST start with 'EP #{episode_number}:'\n"
        f"Give 3 absurd poll options for what happens next."
    )

    for attempt in range(MAX_RETRIES):
        data = _call_claude(client, prompt)
        tweet = data["tweet"]
        options = data["poll_options"]

        combined = tweet + " " + " ".join(options)
        if is_content_safe(combined):
            return tweet, options

        logger.warning(
            "Content failed safety check (attempt %d/%d), regenerating",
            attempt + 1,
            MAX_RETRIES,
        )

    raise RuntimeError(f"Failed to generate safe content after {MAX_RETRIES} attempts")


def generate_branch(trend: Trend, prev_round: Round) -> tuple[str, list[str]]:
    """Continue the story based on winning vote and best replies."""
    client = get_client()

    # Pick winning option
    if prev_round.votes:
        winning = max(prev_round.votes, key=prev_round.votes.get)
    else:
        winning = "chaos"

    # Build prompt
    prompt = (
        f"Continue the meme story about: {trend.title}\n"
        f"Previous tweet: {prev_round.tweet_text}\n"
        f"The audience voted for: {winning}\n"
    )
    if prev_round.best_replies:
        replies_text = "; ".join(prev_round.best_replies[:3])
        prompt += f"Best audience replies: {replies_text}\n"
    prompt += "Write the next tweet and 3 new poll options."

    data = _call_claude(client, prompt)
    return data["tweet"], data["poll_options"]


def generate_finale(
    trend: Trend,
    rounds: list[Round],
    contributors: dict[str, int],
    episode_number: int,
) -> str:
    """Summarize the full story arc and mention top contributors."""
    client = get_client()

    # Build story recap
    story_beats = [f"Round {r.round_number}: {r.tweet_text}" for r in rounds]
    story_summary = "\n".join(story_beats)

    # Top 3 contributors
    sorted_contribs = sorted(contributors.items(), key=lambda x: x[1], reverse=True)[:3]
    top_names = [name for name, _ in sorted_contribs]

    prompt = (
        f"Write a finale tweet for EP #{episode_number} about: {trend.title}\n"
        f"Story so far:\n{story_summary}\n"
        f"Mention these top contributors: {', '.join(top_names)}\n"
        f"Wrap up the story with a ridiculous ending."
    )

    data = _call_claude(client, prompt)
    return data["tweet"]
