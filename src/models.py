"""Data models for Meme Story Bot."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


@dataclass
class Trend:
    """A trending topic detected from a source."""

    title: str
    source: str
    meme_score: float


@dataclass
class Round:
    """A single interactive round within an episode."""

    round_number: int
    tweet_text: str
    poll_options: list[str]
    image_tweet_id: Optional[str] = None
    poll_tweet_id: Optional[str] = None
    votes: dict[str, int] = field(default_factory=dict)
    best_replies: list[str] = field(default_factory=list)
    total_votes: int = 0


class EpisodeState(Enum):
    """Lifecycle states for an episode."""

    OPENING = "OPENING"
    IN_PROGRESS = "IN_PROGRESS"
    ENDING = "ENDING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


@dataclass
class Episode:
    """A complete meme narrative episode."""

    id: str
    episode_number: int
    trend: Trend
    state: EpisodeState
    rounds: list[Round] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    contributors: list[str] = field(default_factory=list)
