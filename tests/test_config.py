"""Tests for config.py constants and env loading."""

from src import config


def test_episode_limits():
    assert config.MAX_CONCURRENT_EPISODES == 2
    assert config.MAX_EPISODES_PER_DAY == 3


def test_timing_constants():
    assert config.SCAN_INTERVAL_SECONDS == 5400
    assert config.ADVANCE_INTERVAL_SECONDS == 300
    assert config.DEFAULT_POLL_DURATION_MINUTES == 60
    assert config.COOLDOWN_SECONDS == 3600


def test_round_voting_constants():
    assert config.MAX_ROUNDS_PER_EPISODE == 5
    assert config.MIN_VOTES_THRESHOLD == 5
    assert config.ENGAGEMENT_DECAY_RATIO == 0.5
    assert config.EARLY_CLOSE_VOTE_THRESHOLD == 50
    assert config.EARLY_CLOSE_MINUTES == 30


def test_api_constants():
    assert config.MAX_RETRIES == 3
    assert config.MONTHLY_READ_QUOTA == 10000
    assert config.MAX_REPLIES_PER_FETCH == 10


def test_paths():
    assert config.DB_PATH == "data/meme_bot.db"
    assert config.TEMPLATE_DIR == "templates"
    assert config.KILL_SWITCH_FILE == "data/KILL"


def test_api_keys_are_strings():
    """API keys should be strings (empty when no .env is loaded)."""
    assert isinstance(config.ANTHROPIC_API_KEY, str)
    assert isinstance(config.TWITTER_CONSUMER_KEY, str)
    assert isinstance(config.TWITTER_CONSUMER_SECRET, str)
    assert isinstance(config.TWITTER_ACCESS_TOKEN, str)
    assert isinstance(config.TWITTER_ACCESS_TOKEN_SECRET, str)
    assert isinstance(config.TWITTER_BEARER_TOKEN, str)
