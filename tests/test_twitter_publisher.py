"""Tests for twitter_publisher module."""

from unittest.mock import patch, MagicMock

from src.twitter_publisher import (
    QuotaTracker,
    post_image_tweet,
    post_poll_reply,
    get_poll_results,
    get_top_replies,
    _fetch_poll_data,
)


# --- QuotaTracker ---


def test_quota_tracker_tracks_reads():
    tracker = QuotaTracker()
    assert tracker.reads_this_month == 0
    assert tracker.remaining == 10000

    tracker.add_reads(5)
    assert tracker.reads_this_month == 5
    assert tracker.remaining == 9995

    tracker.add_reads(3)
    assert tracker.reads_this_month == 8
    assert tracker.remaining == 9992


# --- post_image_tweet ---


@patch("src.twitter_publisher.get_client_v2")
@patch("src.twitter_publisher.get_api_v1")
def test_post_image_tweet_returns_tweet_id(mock_v1, mock_v2):
    # v1.1 media upload
    media = MagicMock()
    media.media_id = 123456
    mock_v1.return_value.media_upload.return_value = media

    # v2 create_tweet
    response = MagicMock()
    response.data = {"id": "99887766"}
    mock_v2.return_value.create_tweet.return_value = response

    tweet_id = post_image_tweet("Hello world", "/tmp/image.png")

    assert tweet_id == "99887766"
    mock_v1.return_value.media_upload.assert_called_once_with("/tmp/image.png")
    mock_v2.return_value.create_tweet.assert_called_once_with(
        text="Hello world", media_ids=[123456]
    )


# --- post_poll_reply ---


@patch("src.twitter_publisher.get_client_v2")
def test_post_poll_reply_creates_reply_with_poll(mock_v2):
    response = MagicMock()
    response.data = {"id": "55443322"}
    mock_v2.return_value.create_tweet.return_value = response

    tweet_id = post_poll_reply(
        reply_to="11111111",
        text="What happens next?",
        poll_options=["Option A", "Option B", "Option C"],
        poll_duration_minutes=30,
    )

    assert tweet_id == "55443322"
    mock_v2.return_value.create_tweet.assert_called_once_with(
        text="What happens next?",
        in_reply_to_tweet_id="11111111",
        poll_options=["Option A", "Option B", "Option C"],
        poll_duration_minutes=30,
    )


# --- get_poll_results ---


@patch("src.twitter_publisher._fetch_poll_data")
def test_get_poll_results_returns_votes_dict(mock_fetch):
    poll_data = MagicMock()
    poll_data.options = [
        {"label": "Option A", "votes": 42},
        {"label": "Option B", "votes": 18},
        {"label": "Option C", "votes": 7},
    ]

    response = MagicMock()
    response.includes = {"polls": [poll_data]}
    mock_fetch.return_value = response

    tracker = QuotaTracker()
    votes, total = get_poll_results("99887766", tracker)

    assert votes == {"Option A": 42, "Option B": 18, "Option C": 7}
    assert total == 67
    assert tracker.reads_this_month == 1


# --- get_top_replies ---


@patch("src.twitter_publisher.get_client_v2")
def test_get_top_replies_sorted_by_likes(mock_v2):
    tweet1 = MagicMock()
    tweet1.text = "great thread"
    tweet1.author_id = "u1"
    tweet1.public_metrics = {"like_count": 3}

    tweet2 = MagicMock()
    tweet2.text = "lmao this is gold"
    tweet2.author_id = "u2"
    tweet2.public_metrics = {"like_count": 15}

    tweet3 = MagicMock()
    tweet3.text = "meh"
    tweet3.author_id = "u3"
    tweet3.public_metrics = {"like_count": 1}

    user1 = MagicMock()
    user1.id = "u1"
    user1.username = "alice"

    user2 = MagicMock()
    user2.id = "u2"
    user2.username = "bob"

    user3 = MagicMock()
    user3.id = "u3"
    user3.username = "charlie"

    response = MagicMock()
    response.data = [tweet1, tweet2, tweet3]
    response.includes = {"users": [user1, user2, user3]}
    mock_v2.return_value.search_recent_tweets.return_value = response

    tracker = QuotaTracker()
    replies = get_top_replies("99887766", tracker, limit=2)

    # Sorted by likes descending, limited to 2
    assert len(replies) == 2
    assert replies[0]["user"] == "bob"
    assert replies[0]["likes"] == 15
    assert replies[1]["user"] == "alice"
    assert replies[1]["likes"] == 3
    assert tracker.reads_this_month == 3
