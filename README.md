# Meme Story Bot (Episode Engine)

AI-driven interactive meme narrative game on Twitter. Each trending topic becomes an "episode" where users vote on story direction through polls and contribute via replies.

## How It Works

1. Bot scans Google Trends for trending topics (every 90 min)
2. AI generates a meme-style opening tweet with an episode card image
3. A reply tweet with a poll asks "What happens next?"
4. Users vote and reply with their own takes
5. AI picks the winning vote + best replies, generates the next round (every 5 min check)
6. Repeat 2-5 rounds based on engagement
7. AI posts a finale with contributor shoutouts
8. Daily recap with MVP highlights and episode summary card

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in API keys in .env
```

## Run

```bash
source .venv/bin/activate
python run.py
```

## Kill Switch

```bash
touch data/KILL    # stop
rm data/KILL       # resume
```

## Test

```bash
# Unit tests (no API calls)
pytest tests/ -v --ignore=tests/test_eval.py

# Eval tests (calls Claude API, costs money)
RUN_EVALS=1 pytest tests/test_eval.py -v -s
```
