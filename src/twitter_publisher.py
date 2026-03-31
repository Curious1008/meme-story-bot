"""Twitter publishing and reading via Tweepy (v2 + v1.1 APIs)."""

from __future__ import annotations

import tweepy

from src.config import (
    MONTHLY_READ_QUOTA,
    MAX_REPLIES_PER_FETCH,
    TWITTER_CONSUMER_KEY,
    TWITTER_CONSUMER_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
    TWITTER_BEARER_TOKEN,
)


# ---------------------------------------------------------------------------
# Quota tracker
# ---------------------------------------------------------------------------

class QuotaTracker:
    """Track monthly Twitter read API usage against MONTHLY_READ_QUOTA."""

    def __init__(self) -> None:
        self.reads_this_month: int = 0

    def add_reads(self, count: int) -> None:
        self.reads_this_month += count

    @property
    def remaining(self) -> int:
        return MONTHLY_READ_QUOTA - self.reads_this_month


# ---------------------------------------------------------------------------
# Client factories
# ---------------------------------------------------------------------------

def get_client_v2() -> tweepy.Client:
    """Return a Tweepy v2 Client with OAuth 1.0a (writes) + Bearer (reads)."""
    return tweepy.Client(
        bearer_token=TWITTER_BEARER_TOKEN,
        consumer_key=TWITTER_CONSUMER_KEY,
        consumer_secret=TWITTER_CONSUMER_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
    )


def get_api_v1() -> tweepy.API:
    """Return a Tweepy v1.1 API handle for media uploads."""
    auth = tweepy.OAuth1UserHandler(
        consumer_key=TWITTER_CONSUMER_KEY,
        consumer_secret=TWITTER_CONSUMER_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
    )
    return tweepy.API(auth)


# ---------------------------------------------------------------------------
# Posting helpers
# ---------------------------------------------------------------------------

def post_image_tweet(text: str, image_path: str) -> str:
    """Upload an image via v1.1 and post a tweet with it via v2.

    Returns the tweet ID as a string.
    """
    api_v1 = get_api_v1()
    media = api_v1.media_upload(image_path)

    client = get_client_v2()
    response = client.create_tweet(text=text, media_ids=[media.media_id])
    return response.data["id"]


def post_poll_reply(
    reply_to: str,
    text: str,
    poll_options: list[str],
    poll_duration_minutes: int = 60,
) -> str:
    """Post a reply tweet containing a poll (no image -- Twitter API restriction).

    Returns the tweet ID as a string.
    """
    client = get_client_v2()
    response = client.create_tweet(
        text=text,
        in_reply_to_tweet_id=reply_to,
        poll_options=poll_options,
        poll_duration_minutes=poll_duration_minutes,
    )
    return response.data["id"]


def post_tweet(
    text: str,
    reply_to: str | None = None,
    image_path: str | None = None,
) -> str:
    """General-purpose tweet posting with optional reply and image.

    Returns the tweet ID as a string.
    """
    media_ids = None
    if image_path:
        api_v1 = get_api_v1()
        media = api_v1.media_upload(image_path)
        media_ids = [media.media_id]

    client = get_client_v2()
    kwargs: dict = {"text": text}
    if reply_to:
        kwargs["in_reply_to_tweet_id"] = reply_to
    if media_ids:
        kwargs["media_ids"] = media_ids

    response = client.create_tweet(**kwargs)
    return response.data["id"]


# ---------------------------------------------------------------------------
# Reading helpers
# ---------------------------------------------------------------------------

def _fetch_poll_data(tweet_id: str) -> dict:
    """Fetch raw poll data from the Twitter API (separated for testability).

    Returns the raw response from client.get_tweet with poll expansions.
    """
    client = get_client_v2()
    return client.get_tweet(
        tweet_id,
        expansions=["attachments.poll_ids"],
        poll_fields=["options"],
    )


def get_poll_results(
    tweet_id: str,
    tracker: QuotaTracker,
) -> tuple[dict[str, int], int]:
    """Fetch poll voting data from a tweet.

    Returns (votes_dict, total_votes).
    """
    response = _fetch_poll_data(tweet_id)
    tracker.add_reads(1)

    poll = response.includes["polls"][0]
    votes: dict[str, int] = {}
    total = 0
    for option in poll.options:
        votes[option["label"]] = option["votes"]
        total += option["votes"]

    return votes, total


def get_top_replies(
    tweet_id: str,
    tracker: QuotaTracker,
    limit: int = 5,
) -> list[dict]:
    """Search recent replies to a tweet, sorted by like_count descending.

    Returns a list of dicts: [{user, text, likes}, ...].
    """
    client = get_client_v2()
    response = client.search_recent_tweets(
        query=f"conversation_id:{tweet_id}",
        max_results=MAX_REPLIES_PER_FETCH,
        tweet_fields=["public_metrics", "author_id"],
        expansions=["author_id"],
        user_fields=["username"],
    )

    if not response.data:
        tracker.add_reads(0)
        return []

    tracker.add_reads(len(response.data))

    # Build author_id -> username map
    user_map: dict[str, str] = {}
    if response.includes and "users" in response.includes:
        for user in response.includes["users"]:
            user_map[user.id] = user.username

    results = []
    for tweet in response.data:
        likes = tweet.public_metrics.get("like_count", 0)
        results.append({
            "user": user_map.get(tweet.author_id, tweet.author_id),
            "text": tweet.text,
            "likes": likes,
        })

    results.sort(key=lambda r: r["likes"], reverse=True)
    return results[:limit]
