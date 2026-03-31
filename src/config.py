"""Configuration constants and environment variable loading for Meme Story Bot."""

import os

from dotenv import load_dotenv

load_dotenv()

# --- Episode limits ---
MAX_CONCURRENT_EPISODES = 2
MAX_EPISODES_PER_DAY = 3

# --- Timing ---
SCAN_INTERVAL_SECONDS = 5400  # 90 min
ADVANCE_INTERVAL_SECONDS = 300  # 5 min
DEFAULT_POLL_DURATION_MINUTES = 60
COOLDOWN_SECONDS = 3600

# --- Round / voting ---
MAX_ROUNDS_PER_EPISODE = 5
MIN_VOTES_THRESHOLD = 5
ENGAGEMENT_DECAY_RATIO = 0.5
EARLY_CLOSE_VOTE_THRESHOLD = 50
EARLY_CLOSE_MINUTES = 30

# --- API / rate-limit ---
MAX_RETRIES = 3
MONTHLY_READ_QUOTA = 10000
MAX_REPLIES_PER_FETCH = 10

# --- API keys (from environment) ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "")  # 留空则用官方端点
TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY", "")
TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

# --- Paths ---
DB_PATH = "data/meme_bot.db"
TEMPLATE_DIR = "templates"
KILL_SWITCH_FILE = "data/KILL"
