# Design System — Meme Story Bot

## Product Context
- **What this is:** Twitter bot that turns trending topics into interactive meme narrative "episodes"
- **Who it's for:** English-speaking Twitter users who enjoy memes and interactive entertainment
- **Space/industry:** Social media entertainment, meme culture, interactive fiction
- **Project type:** Twitter bot with branded image cards (Pillow-generated)

## Aesthetic Direction
- **Direction:** Retro-Futuristic
- **Decoration level:** Intentional (subtle CRT scan lines, noise texture)
- **Mood:** Old-school TV game show meets internet culture. Familiar enough to feel fun, weird enough to stand out. Think "what if a 1980s game show ran on Twitter and was hosted by an AI."
- **Reference:** CRT monitors, retro terminal interfaces, old game show title cards

## Typography
- **Episode Number (hero):** JetBrains Mono Bold — monospace creates the "terminal/scoreboard" feel. Episode number is the brand's visual anchor.
- **Title/Headlines:** Satoshi Bold — modern geometric sans-serif. Clean, confident, pairs well with the monospace accent.
- **Body/Description:** DM Sans Regular — friendly and readable at small sizes. Neutral enough to let the content speak.
- **Data/Stats:** JetBrains Mono Regular — tabular-nums for vote counts, round numbers.
- **Loading:** Google Fonts CDN for Satoshi and DM Sans. JetBrains Mono self-hosted or Bunny Fonts.
- **Scale:** EP number 48px, title 36px, body 24px, caption 20px, brand 16px

## Color
- **Approach:** Restrained (1 accent + 1 secondary + neutrals)
- **Background:** #0D0D0D — near-black, anchors the dark aesthetic
- **Primary Accent:** #00FF88 — CRT phosphor green. The brand color. Used for episode numbers, dividers, badges, highlights.
- **Secondary Accent:** #FF6B35 — warm orange. Used sparingly for urgency/excitement moments (finales, "VOTE NOW", high engagement alerts).
- **Primary Text:** #E0E0E0 — soft white, easy on eyes against dark background
- **Muted Text:** #888888 — secondary info, brand watermark, timestamps
- **Dark mode:** N/A (always dark, this IS the dark mode)

## Spacing
- **Base unit:** 8px
- **Density:** Comfortable
- **Card padding:** 60px horizontal, 40px vertical
- **Element gaps:** 16px (tight), 24px (standard), 40px (section break)

## Layout — Card Templates

### Episode Card (1200x675px, 16:9)
```
+--------------------------------------------------+
|  EP #42                          [near-black bg]  |
|  ─────────────────────── (green divider line)     |
|                                                    |
|  CEO declares his chatbot                          |
|  has feelings                                      |
|                                                    |
|                                                    |
|  VOTE NOW                    MEME STORY BOT       |
|  (green badge)               (gray, small)        |
+--------------------------------------------------+
```
- Episode number: top-left, 48px, JetBrains Mono Bold, #00FF88
- Divider: 3px line, #00FF88, spans card width minus padding
- Trend title: center-left, 36px, Satoshi Bold, #E0E0E0
- "VOTE NOW" badge: bottom-left, 28px, JetBrains Mono, #00FF88
- Brand: bottom-right, 16px, DM Sans, #888888
- Texture: subtle scan line overlay at 5% opacity

### Recap Card (1200x675px, 16:9)
```
+--------------------------------------------------+
|  DAILY RECAP                                      |
|  ─────────────────────── (green divider)          |
|                                                    |
|  EP #42: CEO drama (3R, 150V)                     |
|  EP #43: AI uprising (2R, 80V)                    |
|                                                    |
|  MVPs:                                             |
|    @user1 (5x)                                     |
|    @user2 (3x)                                     |
|                                                    |
|                              MEME STORY BOT       |
+--------------------------------------------------+
```
- "DAILY RECAP": 42px, JetBrains Mono Bold, #00FF88
- Episode list: 24px, DM Sans, #E0E0E0
- MVP section: 28px header (Satoshi Bold, #00FF88), 24px names (DM Sans, #E0E0E0)
- Brand: bottom-right, 16px, DM Sans, #888888

## Tweet Formatting
- Episode number always first: "EP #42:"
- Line breaks between sections (not a wall of text)
- Poll reply starts with "What happens next?"
- Finale tweets start with "GAME OVER" or "SERIES FINALE"
- Recap tweets start with "DAILY RECAP"
- Contributor mentions use @username format
- No hashtags in v1 (test organic reach first)

## Motion
- **Approach:** N/A (static images, no animation in v1)
- **Future (v2+):** GIF episode cards with typing animation, vote counter ticking up

## CRT Texture Effect
- Subtle horizontal scan lines: 1px lines at 5% opacity, every 4px
- Optional: very light noise overlay at 2-3% opacity
- Do NOT overdo it. The texture should be felt, not seen. If you notice the scan lines on first glance, they're too strong.

## Anti-Patterns (never do)
- Purple/violet gradients
- Rounded bubbly corners on everything
- Generic stock-photo-style imagery
- Rainbow color accents
- Comic Sans or any "fun" fonts
- Centered everything with uniform spacing
- Bright white backgrounds
- Emoji as visual elements on cards (emoji in tweet text is fine)

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-31 | Initial design system | Created by /design-consultation. Retro-Futuristic direction chosen for uniqueness on Twitter + natural "game show" fit. CRT green (#00FF88) as brand color for instant recognition in feeds. |
| 2026-03-31 | Episode number as visual hero | Differentiator: most meme accounts emphasize content, we emphasize the episode number. Creates serial identity ("EP #47 was legendary"). |
| 2026-03-31 | Dark-only, no light mode | Twitter meme audience expects dark. Dark backgrounds also make the CRT green pop more. |
