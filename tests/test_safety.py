"""Tests for safety filter module."""

from src.safety import is_trend_safe, is_content_safe


# --- is_trend_safe ---

def test_safe_trend_passes():
    assert is_trend_safe("Taylor Swift new album drops Friday") is True
    assert is_trend_safe("#CatMemes") is True
    assert is_trend_safe("Bitcoin hits 100k") is True


def test_violence_blocked():
    assert is_trend_safe("Mass shooting at mall") is False
    assert is_trend_safe("MASSACRE in downtown") is False
    assert is_trend_safe("Man killed in road rage") is False
    assert is_trend_safe("Suspect kills three people") is False
    assert is_trend_safe("Murder suspect arrested") is False
    assert is_trend_safe("Bombing rocks city center") is False
    assert is_trend_safe("Stabbing on subway") is False


def test_disaster_with_casualties_blocked():
    assert is_trend_safe("Earthquake leaves 50 dead") is False
    assert is_trend_safe("Tsunami death toll rises") is False
    assert is_trend_safe("Hurricane kills dozens") is False
    assert is_trend_safe("Flood victims rescued") is False
    assert is_trend_safe("Wildfire deaths confirmed") is False


def test_disaster_without_casualties_passes():
    assert is_trend_safe("Earthquake felt in LA") is True
    assert is_trend_safe("Hurricane season forecast") is True
    assert is_trend_safe("Flood warnings issued") is True


def test_terrorism_blocked():
    assert is_trend_safe("Terrorist attack leaves 10 dead") is False
    assert is_trend_safe("Terrorism victims identified") is False
    assert is_trend_safe("Attack kills 5 injured 20") is False


def test_self_harm_blocked():
    assert is_trend_safe("Celebrity suicide shocks fans") is False
    assert is_trend_safe("Self-harm awareness month") is False
    assert is_trend_safe("Self harm prevention") is False


def test_child_abuse_blocked():
    assert is_trend_safe("Child abuse case uncovered") is False
    assert is_trend_safe("Child exploitation ring busted") is False
    assert is_trend_safe("Child porn arrests") is False


# --- is_content_safe ---

def test_safe_content_passes():
    assert is_content_safe("This meme is hilarious, what a great trend!") is True
    assert is_content_safe("Chapter 3: The plot thickens...") is True


def test_slur_blocked():
    assert is_content_safe("You're such a nigger") is False
    assert is_content_safe("What a faggot") is False
    assert is_content_safe("Stupid retard can't do anything") is False
    assert is_content_safe("She's so retarded") is False


def test_self_harm_language_blocked():
    assert is_content_safe("Just kill yourself already") is False
    assert is_content_safe("lol kys") is False


def test_child_abuse_content_blocked():
    assert is_content_safe("child porn is bad") is False
    assert is_content_safe("child exploitation material") is False
