"""Tests for image generator module."""

import os

import pytest
from PIL import Image

from src.image_generator import create_episode_card, create_recap_card


# --- create_episode_card ---


def test_create_episode_card_returns_valid_png(tmp_path):
    path = create_episode_card(
        episode_number=7,
        trend_title="CEO declares his chatbot has feelings",
        output_dir=str(tmp_path),
    )
    assert path.endswith(".png")
    assert os.path.isfile(path)
    img = Image.open(path)
    assert img.size == (1200, 675)


def test_create_episode_card_truncates_long_title(tmp_path):
    long_title = "A" * 120
    path = create_episode_card(
        episode_number=1,
        trend_title=long_title,
        output_dir=str(tmp_path),
    )
    assert os.path.isfile(path)
    # Just verify it does not crash and produces a valid image
    img = Image.open(path)
    assert img.size == (1200, 675)


# --- create_recap_card ---


def test_create_recap_card_returns_valid_png(tmp_path):
    episodes = [
        {"number": 1, "title": "CEO meltdown", "retweets": 42, "votes": 310},
        {"number": 2, "title": "Dogecoin saga", "retweets": 18, "votes": 155},
    ]
    mvps = [("@degen_king", 5), ("@meme_lord", 3)]
    path = create_recap_card(
        episodes=episodes,
        mvps=mvps,
        output_dir=str(tmp_path),
    )
    assert path.endswith(".png")
    assert os.path.isfile(path)
    img = Image.open(path)
    assert img.size == (1200, 675)


def test_create_recap_card_handles_zero_episodes(tmp_path):
    path = create_recap_card(
        episodes=[],
        mvps=[],
        output_dir=str(tmp_path),
    )
    assert os.path.isfile(path)
    img = Image.open(path)
    assert img.size == (1200, 675)
