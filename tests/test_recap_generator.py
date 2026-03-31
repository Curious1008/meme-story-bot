"""Tests for daily recap generator module."""

import json
from unittest.mock import patch, MagicMock

from src.models import Episode, EpisodeState, Trend, Round
from src.recap_generator import generate_daily_recap


def _mock_response(text: str):
    """Build a fake Anthropic messages.create response."""
    resp = MagicMock()
    resp.content = [MagicMock(text=text)]
    return resp


def _make_episode(number: int, title: str, contributors: list[str], num_rounds: int = 3) -> Episode:
    """Helper to build a test Episode."""
    trend = Trend(title=title, source="google_trends", meme_score=8.0)
    rounds = [
        Round(round_number=i + 1, tweet_text=f"round {i + 1}", poll_options=["a", "b", "c"])
        for i in range(num_rounds)
    ]
    return Episode(
        id=f"ep-{number}",
        episode_number=number,
        trend=trend,
        state=EpisodeState.COMPLETED,
        rounds=rounds,
        contributors=contributors,
    )


def test_generate_daily_recap_with_episodes():
    """Two episodes should produce a recap tweet via Claude."""
    episodes = [
        _make_episode(1, "Elon buys the moon", ["@alice", "@bob", "@alice", "@charlie"]),
        _make_episode(2, "Dogecoin hits $420", ["@bob", "@dave", "@bob"]),
    ]
    payload = json.dumps({
        "tweet": "Today's recap: 2 episodes of pure chaos. "
                 "MVPs @bob @alice @charlie carried us. See you tomorrow!"
    })

    with patch("src.recap_generator.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_response(payload)
        mock_get.return_value = mock_client

        result = generate_daily_recap(episodes)

    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0
    mock_client.messages.create.assert_called_once()

    # Verify prompt includes episode info
    call_args = mock_client.messages.create.call_args
    user_msg = call_args[1]["messages"][0]["content"]
    assert "EP #1" in user_msg
    assert "EP #2" in user_msg
    assert "@bob" in user_msg


def test_generate_daily_recap_empty_list_returns_none():
    """Empty episode list should return None without calling the API."""
    with patch("src.recap_generator.get_client") as mock_get:
        mock_client = MagicMock()
        mock_get.return_value = mock_client

        result = generate_daily_recap([])

    assert result is None
    mock_client.messages.create.assert_not_called()
