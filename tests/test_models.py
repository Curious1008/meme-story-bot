"""Tests for data models."""

from datetime import datetime

from src.models import Episode, EpisodeState, Round, Trend


def test_trend_creation():
    t = Trend(title="Bitcoin ATH", source="reddit", meme_score=0.85)
    assert t.title == "Bitcoin ATH"
    assert t.source == "reddit"
    assert t.meme_score == 0.85


def test_round_defaults():
    r = Round(round_number=1, tweet_text="What happens next?", poll_options=["A", "B"])
    assert r.round_number == 1
    assert r.tweet_text == "What happens next?"
    assert r.poll_options == ["A", "B"]
    assert r.image_tweet_id is None
    assert r.poll_tweet_id is None
    assert r.votes == {}
    assert r.best_replies == []
    assert r.total_votes == 0


def test_round_with_values():
    r = Round(
        round_number=2,
        tweet_text="Plot twist!",
        poll_options=["X", "Y", "Z"],
        image_tweet_id="123",
        poll_tweet_id="456",
        votes={"X": 10, "Y": 5, "Z": 3},
        best_replies=["nice", "wow"],
        total_votes=18,
    )
    assert r.total_votes == 18
    assert r.image_tweet_id == "123"


def test_episode_state_values():
    assert EpisodeState.OPENING.value == "OPENING"
    assert EpisodeState.IN_PROGRESS.value == "IN_PROGRESS"
    assert EpisodeState.ENDING.value == "ENDING"
    assert EpisodeState.COMPLETED.value == "COMPLETED"
    assert EpisodeState.ERROR.value == "ERROR"


def test_episode_creation():
    trend = Trend(title="Test", source="hn", meme_score=0.9)
    ep = Episode(id="ep-001", episode_number=1, trend=trend, state=EpisodeState.OPENING)
    assert ep.id == "ep-001"
    assert ep.episode_number == 1
    assert ep.trend.title == "Test"
    assert ep.state == EpisodeState.OPENING
    assert ep.rounds == []
    assert isinstance(ep.created_at, datetime)
    assert ep.contributors == []


def test_episode_with_rounds():
    trend = Trend(title="Meme", source="twitter", meme_score=0.7)
    r1 = Round(round_number=1, tweet_text="Start", poll_options=["A", "B"])
    ep = Episode(
        id="ep-002",
        episode_number=2,
        trend=trend,
        state=EpisodeState.IN_PROGRESS,
        rounds=[r1],
        contributors=["@user1"],
    )
    assert len(ep.rounds) == 1
    assert ep.contributors == ["@user1"]
