"""Dual-loop scheduler orchestrating all Meme Story Bot modules."""

import logging
import os
import random
import threading
import time
from datetime import datetime, timezone
from typing import Optional

from src.config import (
    ADVANCE_INTERVAL_SECONDS,
    DB_PATH,
    DEFAULT_POLL_DURATION_MINUTES,
    KILL_SWITCH_FILE,
    SCAN_INTERVAL_SECONDS,
)
from src.content_generator import generate_branch, generate_finale, generate_opening
from src.episode_manager import EpisodeManager
from src.image_generator import create_episode_card, create_recap_card
from src.models import EpisodeState, Round
from src.recap_generator import generate_daily_recap
from src.trend_scanner import scan_trends
from src.trend_scorer import score_trends
from src.twitter_publisher import (
    QuotaTracker,
    get_poll_results,
    get_top_replies,
    post_image_tweet,
    post_poll_reply,
    post_tweet,
)

logger = logging.getLogger(__name__)

IMAGE_DIR = "data/images"


class Scheduler:
    """Orchestrates trend scanning, episode progression, and daily recaps."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.em = EpisodeManager(db_path or DB_PATH)
        self.quota = QuotaTracker()
        os.makedirs(IMAGE_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    def scan_and_start(self) -> None:
        """Scan trends, pick the best, and start a new episode."""
        if not self.em.can_start_episode():
            logger.info("Cannot start episode (slot/daily/cooldown limit reached)")
            return

        try:
            trends = scan_trends()
            scored = score_trends(trends)
            if not scored:
                logger.info("No trends scored high enough to start an episode")
                return

            best = scored[0]
            episode = self.em.start_episode(best)

            tweet_text, poll_options = generate_opening(best, episode.episode_number)
            card_path = create_episode_card(
                episode.episode_number, best.title, IMAGE_DIR
            )
            image_tweet_id = post_image_tweet(tweet_text, card_path)
            poll_tweet_id = post_poll_reply(
                image_tweet_id,
                "What happens next?",
                poll_options,
                DEFAULT_POLL_DURATION_MINUTES,
            )

            rnd = Round(
                round_number=1,
                tweet_text=tweet_text,
                poll_options=poll_options,
                image_tweet_id=image_tweet_id,
                poll_tweet_id=poll_tweet_id,
            )
            episode.rounds.append(rnd)
            episode.state = EpisodeState.IN_PROGRESS
            self.em.save_episode(episode)
            logger.info("Started episode %s (EP #%d)", episode.id, episode.episode_number)

        except Exception:
            logger.exception("Error in scan_and_start")
            if "episode" in locals():
                self.em.mark_error(episode.id)

    def advance_episode(self, ep_id: str) -> None:
        """Advance an active episode by reading poll results and continuing."""
        try:
            episode = self.em.get_episode(ep_id)
            if episode.state not in (EpisodeState.OPENING, EpisodeState.IN_PROGRESS):
                return

            last = episode.rounds[-1]
            votes, total_votes = get_poll_results(last.poll_tweet_id, self.quota)
            replies = get_top_replies(last.poll_tweet_id, self.quota)

            # Update round data
            last.votes = votes
            last.total_votes = total_votes
            last.best_replies = [r["text"] for r in replies]

            # Update contributors
            for r in replies:
                user = r["user"]
                if user not in episode.contributors:
                    episode.contributors.append(user)

            # Decide whether to continue
            should_go = self.em.should_continue(
                last, total_votes, len(episode.rounds) + 1
            )

            if not should_go:
                self._end_episode(episode)
                return

            # Generate next round
            tweet_text, poll_options = generate_branch(episode.trend, last)
            card_path = create_episode_card(
                episode.episode_number, episode.trend.title, IMAGE_DIR
            )
            image_tweet_id = post_image_tweet(tweet_text, card_path)
            poll_tweet_id = post_poll_reply(
                image_tweet_id,
                "What happens next?",
                poll_options,
                DEFAULT_POLL_DURATION_MINUTES,
            )

            new_round = Round(
                round_number=len(episode.rounds) + 1,
                tweet_text=tweet_text,
                poll_options=poll_options,
                image_tweet_id=image_tweet_id,
                poll_tweet_id=poll_tweet_id,
            )
            episode.rounds.append(new_round)
            self.em.save_episode(episode)
            logger.info(
                "Advanced episode %s to round %d", ep_id, new_round.round_number
            )

        except Exception:
            logger.exception("Error advancing episode %s", ep_id)
            if "episode" in locals():
                self._end_episode(episode)

    def _end_episode(self, episode) -> None:
        """Generate finale, post it, and mark episode completed."""
        try:
            # Build contributors dict (name -> count based on replies)
            contrib_dict = {name: 1 for name in episode.contributors}
            finale_text = generate_finale(
                episode.trend,
                episode.rounds,
                contrib_dict,
                episode.episode_number,
            )
            post_tweet(finale_text)
        except Exception:
            logger.exception("Error posting finale for episode %s", episode.id)
        finally:
            self.em.complete_episode(episode.id)
            logger.info("Completed episode %s", episode.id)

    def daily_recap(self) -> None:
        """Generate and post a daily recap if there are completed episodes."""
        completed = self.em.get_todays_completed()
        if not completed:
            return

        try:
            recap_text = generate_daily_recap(completed)
            if not recap_text:
                return

            # Build data for recap card
            ep_data = [
                {
                    "number": ep.episode_number,
                    "title": ep.trend.title,
                    "retweets": 0,
                    "votes": sum(r.total_votes for r in ep.rounds),
                }
                for ep in completed
            ]
            # Aggregate MVPs
            from collections import Counter

            mvp_counter: Counter = Counter()
            for ep in completed:
                mvp_counter.update(ep.contributors)
            mvps = mvp_counter.most_common(5)

            card_path = create_recap_card(ep_data, mvps, IMAGE_DIR)
            post_tweet(recap_text, image_path=card_path)
            logger.info("Posted daily recap")

        except Exception:
            logger.exception("Error posting daily recap")

    def advance_tick(self) -> None:
        """Advance all active episodes."""
        for ep in self.em.get_active_episodes():
            self.advance_episode(ep.id)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def _is_killed(self) -> bool:
        return os.path.exists(KILL_SWITCH_FILE)

    def run(self) -> None:
        """Main loop with scan, advance, and daily recap threads."""
        logger.info("Scheduler starting")

        def scan_loop():
            while not self._is_killed():
                self.scan_and_start()
                jitter = random.randint(-900, 900)
                time.sleep(SCAN_INTERVAL_SECONDS + jitter)

        def advance_loop():
            while not self._is_killed():
                self.advance_tick()
                time.sleep(ADVANCE_INTERVAL_SECONDS)

        scan_thread = threading.Thread(target=scan_loop, daemon=True, name="scan-loop")
        advance_thread = threading.Thread(
            target=advance_loop, daemon=True, name="advance-loop"
        )

        scan_thread.start()
        advance_thread.start()

        # Main thread: daily recap at ~23:55 UTC
        try:
            while not self._is_killed():
                now = datetime.now(timezone.utc)
                if now.hour == 23 and now.minute >= 55:
                    self.daily_recap()
                    # Sleep past midnight to avoid double-firing
                    time.sleep(600)
                else:
                    time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by keyboard interrupt")

        logger.info("Scheduler exiting")
