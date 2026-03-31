"""Safety filters for trend selection and content generation."""

import re

# --- Trend filters (case-insensitive) ---

# Direct violence keywords — always blocked
_VIOLENCE_RE = re.compile(
    r"shooting|massacre|killed|kills|murder|bombing|stabbing",
    re.IGNORECASE,
)

# Disaster + casualties — only blocked when both present
_DISASTER_RE = re.compile(
    r"earthquake|tsunami|hurricane|flood|wildfire",
    re.IGNORECASE,
)
_CASUALTIES_RE = re.compile(
    r"dead|death|kills|victims",
    re.IGNORECASE,
)

# Terrorism + casualties
_TERRORISM_RE = re.compile(
    r"terrorist|terrorism|attack",
    re.IGNORECASE,
)
_TERRORISM_CASUALTIES_RE = re.compile(
    r"dead|death|kills|victims|injured",
    re.IGNORECASE,
)

# Self-harm
_SELF_HARM_RE = re.compile(
    r"suicide|self.harm",
    re.IGNORECASE,
)

# Child abuse
_CHILD_ABUSE_RE = re.compile(
    r"child\s*(abuse|porn|exploitation)",
    re.IGNORECASE,
)

# --- Content filters (case-insensitive) ---

_SLURS_RE = re.compile(
    r"\bnigger\b|\bfaggot\b|\bretard(?:ed)?\b",
    re.IGNORECASE,
)

_CONTENT_SELF_HARM_RE = re.compile(
    r"kill\s+yourself|\bkys\b",
    re.IGNORECASE,
)

_CONTENT_CHILD_RE = re.compile(
    r"child\s*(porn|exploitation)",
    re.IGNORECASE,
)


def is_trend_safe(trend_title: str) -> bool:
    """Return False if the trend touches sensitive topics."""
    if _VIOLENCE_RE.search(trend_title):
        return False
    if _DISASTER_RE.search(trend_title) and _CASUALTIES_RE.search(trend_title):
        return False
    if _TERRORISM_RE.search(trend_title) and _TERRORISM_CASUALTIES_RE.search(trend_title):
        return False
    if _SELF_HARM_RE.search(trend_title):
        return False
    if _CHILD_ABUSE_RE.search(trend_title):
        return False
    return True


def is_content_safe(content: str) -> bool:
    """Return False if content contains slurs or dangerous language."""
    if _SLURS_RE.search(content):
        return False
    if _CONTENT_SELF_HARM_RE.search(content):
        return False
    if _CONTENT_CHILD_RE.search(content):
        return False
    return True
