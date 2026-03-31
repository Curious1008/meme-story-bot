"""Tests for the Scheduler dual-loop orchestrator."""

from unittest.mock import MagicMock, patch

import pytest

from src.models import Episode, EpisodeState, Round, Trend
from src.scheduler import Scheduler


def _make_trend():
    return Trend(title="Cats vs Cucumbers", source="google_trends", meme_score=8.5)


def _make_episode(ep_id="ep-1", number=1, state=EpisodeState.IN_PROGRESS):
    trend = _make_trend()
    return Episode(
        id=ep_id,
        episode_number=number,
        trend=trend,
        state=state,
        rounds=[
            Round(
                round_number=1,
                tweet_text="EP #1: Cats declare war on cucumbers",
                poll_options=["Run", "Fight", "Negotiate"],
                image_tweet_id="img-111",
                poll_tweet_id="poll-222",
                votes={"Run": 20, "Fight": 15, "Negotiate": 5},
                total_votes=40,
            )
        ],
    )


@patch("src.scheduler.post_poll_reply", return_value="poll-222")
@patch("src.scheduler.post_image_tweet", return_value="img-111")
@patch("src.scheduler.create_episode_card", return_value="/tmp/card.png")
@patch("src.scheduler.generate_opening", return_value=("EP #1: Cats vs Cucumbers!", ["A", "B", "C"]))
@patch("src.scheduler.score_trends")
@patch("src.scheduler.scan_trends")
def test_scan_and_start_creates_episode(
    mock_scan, mock_score, mock_gen_open, mock_card, mock_img_tweet, mock_poll_reply
):
    """scan_and_start creates an episode when slots are available."""
    trend = _make_trend()
    mock_scan.return_value = [trend]
    mock_score.return_value = [trend]

    sched = Scheduler(db_path=":memory:")
    sched.scan_and_start()

    # Episode was created and saved
    active = sched.em.get_active_episodes()
    assert len(active) == 1
    ep = active[0]
    assert ep.state == EpisodeState.IN_PROGRESS
    assert len(ep.rounds) == 1
    assert ep.rounds[0].image_tweet_id == "img-111"
    assert ep.rounds[0].poll_tweet_id == "poll-222"


@patch("src.scheduler.scan_trends")
def test_scan_skips_when_slots_full(mock_scan):
    """scan_and_start does nothing when can_start_episode returns False."""
    sched = Scheduler(db_path=":memory:")

    # Fill up slots by patching can_start_episode
    with patch.object(sched.em, "can_start_episode", return_value=False):
        sched.scan_and_start()

    # scan_trends should not have been called
    mock_scan.assert_not_called()
    assert sched.em.get_active_episodes() == []


@patch("src.scheduler.post_poll_reply", return_value="poll-333")
@patch("src.scheduler.post_image_tweet", return_value="img-333")
@patch("src.scheduler.create_episode_card", return_value="/tmp/card2.png")
@patch("src.scheduler.generate_branch", return_value=("The cats advanced!", ["X", "Y", "Z"]))
@patch("src.scheduler.get_top_replies", return_value=[{"user": "alice", "text": "lol", "likes": 5}])
@patch("src.scheduler.get_poll_results", return_value=({"Run": 30, "Fight": 20, "Negotiate": 10}, 60))
def test_advance_continues_on_high_engagement(
    mock_poll, mock_replies, mock_branch, mock_card, mock_img_tweet, mock_poll_reply
):
    """advance_episode creates a new round when engagement is high."""
    sched = Scheduler(db_path=":memory:")

    # Manually create an episode with one round
    ep = _make_episode()
    ep_obj = sched.em.start_episode(ep.trend)
    ep_obj.state = EpisodeState.IN_PROGRESS
    ep_obj.rounds = ep.rounds
    sched.em.save_episode(ep_obj)

    sched.advance_episode(ep_obj.id)

    updated = sched.em.get_episode(ep_obj.id)
    assert len(updated.rounds) == 2
    assert updated.rounds[1].poll_tweet_id == "poll-333"
    assert updated.state == EpisodeState.IN_PROGRESS
