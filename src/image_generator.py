"""Generate branded card images for Meme Story Bot tweets.

Uses Pillow to create 1200x675 episode and recap cards following
the retro-futuristic design system defined in DESIGN.md.
"""

import os
from datetime import datetime, timezone

from PIL import Image, ImageDraw, ImageFont

# --- Design tokens (from DESIGN.md) ---

WIDTH, HEIGHT = 1200, 675
BG_COLOR = "#0D0D0D"
ACCENT = "#00FF88"
TEXT_PRIMARY = "#E0E0E0"
TEXT_MUTED = "#888888"
PAD_H, PAD_V = 60, 40

# --- Font loading with fallback ---

_MONO_CANDIDATES = [
    "JetBrainsMono-Bold",
    "JetBrains Mono Bold",
    "Menlo-Bold",
    "Menlo Bold",
    "DejaVuSansMono-Bold",
    "LiberationMono-Bold",
]

_SANS_CANDIDATES = [
    "Helvetica",
    "Helvetica Neue",
    "DejaVuSans",
    "LiberationSans",
    "Arial",
]


def _load_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    """Try each candidate font name; fall back to Pillow default."""
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    # Last resort: Pillow built-in bitmap font (no size control)
    return ImageFont.load_default()


def _mono(size: int) -> ImageFont.FreeTypeFont:
    return _load_font(_MONO_CANDIDATES, size)


def _sans(size: int) -> ImageFont.FreeTypeFont:
    return _load_font(_SANS_CANDIDATES, size)


def _truncate(text: str, limit: int = 80) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


# --- Public API ---


def create_episode_card(
    episode_number: int,
    trend_title: str,
    output_dir: str,
) -> str:
    """Create a branded episode card image.

    Returns the absolute path to the saved PNG file.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    y = PAD_V

    # Episode number (top-left, 48px, accent green)
    ep_font = _mono(48)
    ep_text = f"EP #{episode_number}"
    draw.text((PAD_H, y), ep_text, font=ep_font, fill=ACCENT)

    # Move below episode number
    ep_bbox = draw.textbbox((PAD_H, y), ep_text, font=ep_font)
    y = ep_bbox[3] + 16

    # Divider line (3px, accent green, spans width minus padding)
    draw.line([(PAD_H, y), (WIDTH - PAD_H, y)], fill=ACCENT, width=3)
    y += 3 + 24  # line thickness + section gap

    # Trend title (center-left area, 36px, primary text, truncated)
    title_font = _sans(36)
    title_text = _truncate(trend_title, 80)
    draw.text((PAD_H, y), title_text, font=title_font, fill=TEXT_PRIMARY)

    # "VOTE NOW" badge (bottom-left, 28px, accent green)
    vote_font = _mono(28)
    vote_y = HEIGHT - PAD_V - 28
    draw.text((PAD_H, vote_y), "VOTE NOW", font=vote_font, fill=ACCENT)

    # "MEME STORY BOT" brand (bottom-right, 16px, muted)
    brand_font = _sans(16)
    brand_text = "MEME STORY BOT"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text(
        (WIDTH - PAD_H - brand_w, HEIGHT - PAD_V - 16),
        brand_text,
        font=brand_font,
        fill=TEXT_MUTED,
    )

    # Save
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"ep{episode_number}_{ts}.png"
    path = os.path.join(output_dir, filename)
    img.save(path, "PNG")
    return path


def create_recap_card(
    episodes: list[dict],
    mvps: list[tuple[str, int]],
    output_dir: str,
) -> str:
    """Create a daily recap card image.

    episodes: list of dicts with keys number, title, retweets, votes.
    mvps: list of (username, count) tuples.
    Returns the absolute path to the saved PNG file.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    y = PAD_V

    # "DAILY RECAP" header (42px, accent green)
    header_font = _mono(42)
    draw.text((PAD_H, y), "DAILY RECAP", font=header_font, fill=ACCENT)
    header_bbox = draw.textbbox((PAD_H, y), "DAILY RECAP", font=header_font)
    y = header_bbox[3] + 16

    # Divider line
    draw.line([(PAD_H, y), (WIDTH - PAD_H, y)], fill=ACCENT, width=3)
    y += 3 + 24

    # Episode list (max 5)
    ep_font = _sans(24)
    for ep in episodes[:5]:
        num = ep.get("number", "?")
        title = _truncate(ep.get("title", ""), 50)
        rt = ep.get("retweets", 0)
        votes = ep.get("votes", 0)
        line = f"EP #{num}: {title} ({rt}r, {votes}v)"
        draw.text((PAD_H, y), line, font=ep_font, fill=TEXT_PRIMARY)
        y += 32

    if not episodes:
        draw.text((PAD_H, y), "No episodes today.", font=ep_font, fill=TEXT_MUTED)
        y += 32

    # MVPs section
    if mvps:
        y += 16  # section gap
        mvp_header_font = _mono(28)
        draw.text((PAD_H, y), "MVPs", font=mvp_header_font, fill=ACCENT)
        mvp_bbox = draw.textbbox((PAD_H, y), "MVPs", font=mvp_header_font)
        y = mvp_bbox[3] + 12

        mvp_font = _sans(24)
        for name, count in mvps[:5]:
            draw.text(
                (PAD_H, y),
                f"{name} ({count}x)",
                font=mvp_font,
                fill=TEXT_PRIMARY,
            )
            y += 32

    # Brand (bottom-right, 16px, muted)
    brand_font = _sans(16)
    brand_text = "MEME STORY BOT"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text(
        (WIDTH - PAD_H - brand_w, HEIGHT - PAD_V - 16),
        brand_text,
        font=brand_font,
        fill=TEXT_MUTED,
    )

    # Save
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"recap_{ts}.png"
    path = os.path.join(output_dir, filename)
    img.save(path, "PNG")
    return path
