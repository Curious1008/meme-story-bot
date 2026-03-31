"""SQLite-backed episode state machine for Meme Story Bot."""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

from src.config import (
    COOLDOWN_SECONDS,
    ENGAGEMENT_DECAY_RATIO,
    MAX_CONCURRENT_EPISODES,
    MAX_EPISODES_PER_DAY,
    MAX_ROUNDS_PER_EPISODE,
    MIN_VOTES_THRESHOLD,
)
from src.models import Episode, EpisodeState, Round, Trend


class EpisodeManager:
    """Manages episode lifecycle with SQLite persistence."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_tables()

    # ---- schema ----

    def _init_tables(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS episodes (
                id TEXT PRIMARY KEY,
                episode_number INTEGER NOT NULL,
                trend_json TEXT NOT NULL,
                state TEXT NOT NULL,
                rounds_json TEXT NOT NULL DEFAULT '[]',
                contributors_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS counters (
                key TEXT PRIMARY KEY,
                value INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        # Seed the episode counter if missing.
        cur.execute(
            "INSERT OR IGNORE INTO counters (key, value) VALUES ('episode_number', 0)"
        )
        self._conn.commit()

    # ---- helpers ----

    def _next_episode_number(self) -> int:
        cur = self._conn.cursor()
        cur.execute(
            "UPDATE counters SET value = value + 1 WHERE key = 'episode_number'"
        )
        cur.execute("SELECT value FROM counters WHERE key = 'episode_number'")
        row = cur.fetchone()
        return row["value"]

    @staticmethod
    def _trend_to_json(trend: Trend) -> str:
        return json.dumps(
            {"title": trend.title, "source": trend.source, "meme_score": trend.meme_score}
        )

    @staticmethod
    def _trend_from_json(raw: str) -> Trend:
        d = json.loads(raw)
        return Trend(title=d["title"], source=d["source"], meme_score=d["meme_score"])

    @staticmethod
    def _rounds_to_json(rounds: list[Round]) -> str:
        return json.dumps(
            [
                {
                    "round_number": r.round_number,
                    "tweet_text": r.tweet_text,
                    "poll_options": r.poll_options,
                    "image_tweet_id": r.image_tweet_id,
                    "poll_tweet_id": r.poll_tweet_id,
                    "votes": r.votes,
                    "best_replies": r.best_replies,
                    "total_votes": r.total_votes,
                }
                for r in rounds
            ]
        )

    @staticmethod
    def _rounds_from_json(raw: str) -> list[Round]:
        items = json.loads(raw)
        return [
            Round(
                round_number=d["round_number"],
                tweet_text=d["tweet_text"],
                poll_options=d["poll_options"],
                image_tweet_id=d.get("image_tweet_id"),
                poll_tweet_id=d.get("poll_tweet_id"),
                votes=d.get("votes", {}),
                best_replies=d.get("best_replies", []),
                total_votes=d.get("total_votes", 0),
            )
            for d in items
        ]

    def _row_to_episode(self, row: sqlite3.Row) -> Episode:
        completed_at = (
            datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
        )
        return Episode(
            id=row["id"],
            episode_number=row["episode_number"],
            trend=self._trend_from_json(row["trend_json"]),
            state=EpisodeState(row["state"]),
            rounds=self._rounds_from_json(row["rounds_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=completed_at,
            contributors=json.loads(row["contributors_json"]),
        )

    # ---- public API ----

    def can_start_episode(self) -> bool:
        """Check concurrent limit, daily limit, and cooldown."""
        now = datetime.utcnow()
        cur = self._conn.cursor()

        # Concurrent limit
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM episodes WHERE state IN (?, ?)",
            (EpisodeState.OPENING.value, EpisodeState.IN_PROGRESS.value),
        )
        if cur.fetchone()["cnt"] >= MAX_CONCURRENT_EPISODES:
            return False

        # Daily limit
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM episodes WHERE state = ? AND completed_at >= ?",
            (EpisodeState.COMPLETED.value, today_start),
        )
        if cur.fetchone()["cnt"] >= MAX_EPISODES_PER_DAY:
            return False

        # Cooldown: must be COOLDOWN_SECONDS since last completed episode
        cur.execute(
            "SELECT completed_at FROM episodes WHERE completed_at IS NOT NULL "
            "ORDER BY completed_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        if row:
            last_completed = datetime.fromisoformat(row["completed_at"])
            if (now - last_completed).total_seconds() < COOLDOWN_SECONDS:
                return False

        return True

    def start_episode(self, trend: Trend) -> Episode:
        """Create a new episode in OPENING state."""
        ep_id = str(uuid.uuid4())
        ep_num = self._next_episode_number()
        now = datetime.utcnow()

        episode = Episode(
            id=ep_id,
            episode_number=ep_num,
            trend=trend,
            state=EpisodeState.OPENING,
            created_at=now,
        )

        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO episodes (id, episode_number, trend_json, state,
                                  rounds_json, contributors_json, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                episode.id,
                episode.episode_number,
                self._trend_to_json(trend),
                episode.state.value,
                self._rounds_to_json(episode.rounds),
                json.dumps(episode.contributors),
                episode.created_at.isoformat(),
                None,
            ),
        )
        self._conn.commit()
        return episode

    def get_episode(self, ep_id: str) -> Episode:
        """Load an episode from the DB by id."""
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM episodes WHERE id = ?", (ep_id,))
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"Episode {ep_id} not found")
        return self._row_to_episode(row)

    def save_episode(self, episode: Episode) -> None:
        """Persist state, rounds, and contributors back to DB."""
        cur = self._conn.cursor()
        cur.execute(
            """
            UPDATE episodes
               SET state = ?,
                   rounds_json = ?,
                   contributors_json = ?,
                   completed_at = ?
             WHERE id = ?
            """,
            (
                episode.state.value,
                self._rounds_to_json(episode.rounds),
                json.dumps(episode.contributors),
                episode.completed_at.isoformat() if episode.completed_at else None,
                episode.id,
            ),
        )
        self._conn.commit()

    def complete_episode(self, ep_id: str) -> None:
        """Set state to COMPLETED with timestamp."""
        now = datetime.utcnow()
        cur = self._conn.cursor()
        cur.execute(
            "UPDATE episodes SET state = ?, completed_at = ? WHERE id = ?",
            (EpisodeState.COMPLETED.value, now.isoformat(), ep_id),
        )
        self._conn.commit()

    def mark_error(self, ep_id: str) -> None:
        """Set state to ERROR with timestamp."""
        now = datetime.utcnow()
        cur = self._conn.cursor()
        cur.execute(
            "UPDATE episodes SET state = ?, completed_at = ? WHERE id = ?",
            (EpisodeState.ERROR.value, now.isoformat(), ep_id),
        )
        self._conn.commit()

    def get_active_episodes(self) -> list[Episode]:
        """Return episodes in OPENING or IN_PROGRESS state."""
        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM episodes WHERE state IN (?, ?)",
            (EpisodeState.OPENING.value, EpisodeState.IN_PROGRESS.value),
        )
        return [self._row_to_episode(row) for row in cur.fetchall()]

    def get_todays_completed(self) -> list[Episode]:
        """Return COMPLETED episodes from today (UTC)."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM episodes WHERE state = ? AND completed_at >= ?",
            (EpisodeState.COMPLETED.value, today_start),
        )
        return [self._row_to_episode(row) for row in cur.fetchall()]

    @staticmethod
    def should_continue(prev_round: Round, current_votes: int, round_number: int) -> bool:
        """Decide whether to continue to the next round."""
        if round_number >= MAX_ROUNDS_PER_EPISODE:
            return False
        if current_votes < MIN_VOTES_THRESHOLD:
            return False
        if current_votes < prev_round.total_votes * ENGAGEMENT_DECAY_RATIO:
            return False
        return True
