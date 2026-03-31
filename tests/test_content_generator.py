"""Tests for content generator module."""

import json
from unittest.mock import patch, MagicMock

import pytest

from src.models import Trend, Round
from src.content_generator import generate_opening, generate_branch, generate_finale


def _make_trend(title: str = "Elon buys the moon") -> Trend:
    return Trend(title=title, source="google_trends", meme_score=8.5)


def _mock_response(text: str):
    """Build a fake Anthropic messages.create response."""
    resp = MagicMock()
    resp.content = [MagicMock(text=text)]
    return resp


# --- generate_opening ---


def test_generate_opening_returns_tweet_and_options():
    payload = json.dumps({
        "tweet": "EP #1: Elon just bought the moon and renamed it ElonLand lmaooo",
        "poll_options": ["Build a Wendy's up there", "Moon tax for normies", "Lunar dogecoin launch"],
    })
    trend = _make_trend()

    with patch("src.content_generator.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_response(payload)
        mock_get.return_value = mock_client

        tweet, options = generate_opening(trend, episode_number=1)

    assert tweet.startswith("EP #1:")
    assert len(options) == 3
    assert all(isinstance(o, str) for o in options)
    mock_client.messages.create.assert_called_once()


# --- generate_branch ---


def test_generate_branch_incorporates_winning_vote():
    payload = json.dumps({
        "tweet": "EP #2: The moon Wendy's is now serving zero-gravity frosties",
        "poll_options": ["Frosty revolt", "Spicy nugget meteor", "Drive-thru black hole"],
    })
    prev_round = Round(
        round_number=1,
        tweet_text="EP #1: Elon bought the moon",
        poll_options=["Build a Wendy's up there", "Moon tax", "Lunar dogecoin"],
        votes={"Build a Wendy's up there": 42, "Moon tax": 10, "Lunar dogecoin": 5},
        best_replies=["lmao put a drive thru on the dark side"],
    )
    trend = _make_trend()

    with patch("src.content_generator.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_response(payload)
        mock_get.return_value = mock_client

        tweet, options = generate_branch(trend, prev_round)

    assert isinstance(tweet, str)
    assert len(options) == 3
    # Verify the prompt included the winning vote
    call_args = mock_client.messages.create.call_args
    messages = call_args[1]["messages"] if "messages" in call_args[1] else call_args[0][0]
    user_msg = messages[0]["content"]
    assert "Build a Wendy's up there" in user_msg


# --- generate_finale ---


def test_generate_finale_produces_tweet():
    payload = json.dumps({
        "tweet": "EP #1 FINALE: The moon Wendy's collapsed into a black hole. "
                 "Thanks @alice @bob @charlie for this chaos"
    })
    rounds = [
        Round(round_number=1, tweet_text="opening", poll_options=["a", "b", "c"]),
        Round(round_number=2, tweet_text="branch", poll_options=["d", "e", "f"]),
    ]
    contributors = {"@alice": 5, "@bob": 3, "@charlie": 1}
    trend = _make_trend()

    with patch("src.content_generator.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_response(payload)
        mock_get.return_value = mock_client

        tweet = generate_finale(trend, rounds, contributors, episode_number=1)

    assert isinstance(tweet, str)
    assert len(tweet) > 0


# --- safety retry ---


def test_generate_opening_retries_when_content_fails_safety():
    unsafe_payload = json.dumps({
        "tweet": "EP #1: some unsafe content with retarded jokes",
        "poll_options": ["bad", "worse", "worst"],
    })
    safe_payload = json.dumps({
        "tweet": "EP #1: Elon bought the moon and it's hilarious",
        "poll_options": ["Moon party", "Lunar memes", "Space chaos"],
    })
    trend = _make_trend()

    with patch("src.content_generator.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            _mock_response(unsafe_payload),
            _mock_response(safe_payload),
        ]
        mock_get.return_value = mock_client

        tweet, options = generate_opening(trend, episode_number=1)

    # Should have retried and returned the safe content
    assert tweet == "EP #1: Elon bought the moon and it's hilarious"
    assert mock_client.messages.create.call_count == 2
