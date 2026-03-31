"""Tests for EpisodeManager -- SQLite-backed episode state machine."""

from datetime import datetime, timedelta

from src.episode_manager import EpisodeManager
from src.models import Episode, EpisodeState, Round, Trend


def _make_trend(title: str = "Test Trend") -> Trend:
    return Trend(title=title, source="reddit", meme_score=0.9)


# ---- can_start_episode ----


def test_can_start_when_empty():
    mgr = EpisodeManager(":memory:")
    assert mgr.can_start_episode() is True


def test_cannot_exceed_concurrent_limit():
    mgr = EpisodeManager(":memory:")
    mgr.start_episode(_make_trend("A"))
    mgr.start_episode(_make_trend("B"))
    # Two active episodes = at concurrent limit
    assert mgr.can_start_episode() is False


def test_cannot_exceed_daily_limit():
    mgr = EpisodeManager(":memory:")
    # Create and immediately complete 3 episodes (bypass cooldown by back-dating)
    for i in range(3):
        ep = mgr.start_episode(_make_trend(f"D{i}"))
        mgr.complete_episode(ep.id)

    # Hack completed_at timestamps so cooldown doesn't block us:
    # set all completed_at to > COOLDOWN_SECONDS ago but still today
    now = datetime.utcnow()
    today_early = now.replace(hour=0, minute=1, second=0, microsecond=0)
    cur = mgr._conn.cursor()
    cur.execute(
        "UPDATE episodes SET completed_at = ?",
        (today_early.isoformat(),),
    )
    mgr._conn.commit()

    assert mgr.can_start_episode() is False


# ---- start / numbers ----


def test_start_creates_episode_with_opening_state():
    mgr = EpisodeManager(":memory:")
    ep = mgr.start_episode(_make_trend())
    assert ep.state == EpisodeState.OPENING
    assert ep.episode_number == 1
    assert ep.trend.title == "Test Trend"
    assert ep.completed_at is None


def test_episode_numbers_increment():
    mgr = EpisodeManager(":memory:")
    ep1 = mgr.start_episode(_make_trend("A"))
    ep2 = mgr.start_episode(_make_trend("B"))
    ep3 = mgr.start_episode(_make_trend("C"))
    assert ep1.episode_number == 1
    assert ep2.episode_number == 2
    assert ep3.episode_number == 3


# ---- complete / error ----


def test_complete_episode_sets_completed():
    mgr = EpisodeManager(":memory:")
    ep = mgr.start_episode(_make_trend())
    mgr.complete_episode(ep.id)
    loaded = mgr.get_episode(ep.id)
    assert loaded.state == EpisodeState.COMPLETED
    assert loaded.completed_at is not None


def test_mark_error_sets_error():
    mgr = EpisodeManager(":memory:")
    ep = mgr.start_episode(_make_trend())
    mgr.mark_error(ep.id)
    loaded = mgr.get_episode(ep.id)
    assert loaded.state == EpisodeState.ERROR
    assert loaded.completed_at is not None


# ---- should_continue ----


def test_should_continue_high_engagement():
    prev = Round(round_number=1, tweet_text="x", poll_options=["A", "B"], total_votes=20)
    assert EpisodeManager.should_continue(prev, current_votes=15, round_number=2) is True


def test_should_continue_low_engagement():
    prev = Round(round_number=1, tweet_text="x", poll_options=["A", "B"], total_votes=20)
    # 8 < 20 * 0.5 = 10 -> engagement decayed
    assert EpisodeManager.should_continue(prev, current_votes=8, round_number=2) is False


def test_should_continue_at_max_rounds():
    prev = Round(round_number=4, tweet_text="x", poll_options=["A", "B"], total_votes=100)
    assert EpisodeManager.should_continue(prev, current_votes=100, round_number=5) is False


def test_should_continue_below_min_votes():
    prev = Round(round_number=1, tweet_text="x", poll_options=["A", "B"], total_votes=10)
    assert EpisodeManager.should_continue(prev, current_votes=3, round_number=2) is False


# ---- get_todays_completed ----


def test_get_todays_completed_returns_only_today():
    mgr = EpisodeManager(":memory:")

    # Episode completed today
    ep_today = mgr.start_episode(_make_trend("Today"))
    mgr.complete_episode(ep_today.id)

    # Episode "completed yesterday" -- manually back-date
    ep_yesterday = mgr.start_episode(_make_trend("Yesterday"))
    mgr.complete_episode(ep_yesterday.id)
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
    cur = mgr._conn.cursor()
    cur.execute(
        "UPDATE episodes SET completed_at = ? WHERE id = ?",
        (yesterday, ep_yesterday.id),
    )
    mgr._conn.commit()

    result = mgr.get_todays_completed()
    assert len(result) == 1
    assert result[0].id == ep_today.id
