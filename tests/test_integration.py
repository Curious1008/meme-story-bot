"""Integration test — full episode lifecycle with all external APIs mocked."""

from unittest.mock import patch, MagicMock

import pytest

from src.models import EpisodeState, Trend
from src.scheduler import Scheduler


# --- Mock return values ---

MOCK_TRENDS = [
    Trend(title="CEO yeets car into sun", source="google_trends", meme_score=0.0),
    Trend(title="Boring earnings report", source="google_trends", meme_score=0.0),
]

MOCK_SCORED = [
    Trend(title="CEO yeets car into sun", source="google_trends", meme_score=9.0),
]

MOCK_OPENING = (
    'EP #1: CEO yeets car into sun',
    ["Sun explodes", "Car returns", "Insurance"],
)

MOCK_BRANCH = (
    "Sun rejected the car",
    ["Mars", "Sue", "NASA"],
)

MOCK_FINALE = "RIP car. MVP: @fan1. 10/10 would meme again."

HIGH_ENGAGEMENT_VOTES = (
    {"Sun explodes": 80, "Car returns": 30, "Insurance": 10},
    120,
)

LOW_ENGAGEMENT_VOTES = (
    {"Mars": 1, "Sue": 1, "NASA": 0},
    2,
)

MOCK_REPLIES = [
    {"user": "fan1", "text": "lmao the car is toast", "likes": 42},
    {"user": "fan2", "text": "insurance denied", "likes": 10},
]


@pytest.fixture
def scheduler(tmp_path):
    """Create a scheduler with an in-memory DB."""
    db = str(tmp_path / "test.db")
    return Scheduler(db_path=db)


@patch("src.scheduler.scan_trends", return_value=MOCK_TRENDS)
@patch("src.scheduler.score_trends", return_value=MOCK_SCORED)
@patch("src.scheduler.generate_opening", return_value=MOCK_OPENING)
@patch("src.scheduler.generate_branch", return_value=MOCK_BRANCH)
@patch("src.scheduler.generate_finale", return_value=MOCK_FINALE)
@patch("src.scheduler.create_episode_card", return_value="/tmp/card.png")
@patch("src.scheduler.create_recap_card", return_value="/tmp/recap.png")
@patch("src.scheduler.post_image_tweet", return_value="tweet_100")
@patch("src.scheduler.post_poll_reply", return_value="poll_100")
@patch("src.scheduler.post_tweet", return_value="tweet_finale")
@patch("src.scheduler.get_poll_results")
@patch("src.scheduler.get_top_replies", return_value=MOCK_REPLIES)
def test_full_episode_lifecycle(
    mock_get_top_replies,
    mock_get_poll_results,
    mock_post_tweet,
    mock_post_poll_reply,
    mock_post_image_tweet,
    mock_create_recap_card,
    mock_create_episode_card,
    mock_generate_finale,
    mock_generate_branch,
    mock_generate_opening,
    mock_score_trends,
    mock_scan_trends,
    scheduler,
):
    """Full lifecycle: scan -> start -> advance (high) -> advance (low) -> completed."""

    # Configure get_poll_results to return high then low engagement
    mock_get_poll_results.side_effect = [HIGH_ENGAGEMENT_VOTES, LOW_ENGAGEMENT_VOTES]

    # ---- Step 1: scan_and_start ----
    scheduler.scan_and_start()

    episodes = scheduler.em.get_active_episodes()
    assert len(episodes) == 1

    ep = episodes[0]
    assert ep.state == EpisodeState.IN_PROGRESS
    assert ep.episode_number == 1
    assert len(ep.rounds) == 1
    assert ep.rounds[0].tweet_text == MOCK_OPENING[0]
    assert ep.rounds[0].poll_options == MOCK_OPENING[1]
    assert ep.rounds[0].image_tweet_id == "tweet_100"
    assert ep.rounds[0].poll_tweet_id == "poll_100"

    ep_id = ep.id

    # ---- Step 2: advance with high engagement (120 votes) ----
    scheduler.advance_episode(ep_id)

    ep = scheduler.em.get_episode(ep_id)
    assert ep.state == EpisodeState.IN_PROGRESS
    assert len(ep.rounds) == 2
    assert ep.rounds[1].tweet_text == MOCK_BRANCH[0]
    assert ep.rounds[1].poll_options == MOCK_BRANCH[1]

    # Verify round 1 got votes and replies recorded
    assert ep.rounds[0].total_votes == 120
    assert ep.rounds[0].votes == HIGH_ENGAGEMENT_VOTES[0]
    assert "fan1" in ep.contributors
    assert "fan2" in ep.contributors

    # ---- Step 3: advance with low engagement (2 votes) -> episode ends ----
    scheduler.advance_episode(ep_id)

    ep = scheduler.em.get_episode(ep_id)
    assert ep.state == EpisodeState.COMPLETED

    # Verify finale was posted
    mock_generate_finale.assert_called_once()
    mock_post_tweet.assert_called_with(MOCK_FINALE)
