# Newzyx V2

Automated daily news podcast pipeline for kids aged 10-16. Scrapes headlines, scores them with AI, generates a podcast, builds an episode page, and publishes to AWS S3.

## Pipeline

Each run walks through 9 steps:

| Step | Module | What it does |
|------|--------|--------------|
| 1 | `pipeline/collect.py` | Scrapes headlines from Guardian, PopSci, BBC, NatGeo, ABC, NBC |
| 2 | `pipeline/extract.py` | Visits each URL, pulls article text from `<article>`/`<p>` tags |
| 3 | `pipeline/process.py` | Sends articles to GPT-4o-mini for scoring (0-100) and summarization |
| 4 | `pipeline/episode.py` | Selects top 6 articles using weighted scoring with diversity/recency |
| 5 | `pipeline/episode.py` | Builds podcast script, polishes flow with LLM |
| 6 | `pipeline/tts.py` | Converts script to audio via ElevenLabs |
| 7 | `pipeline/episode.py` | Generates dated HTML episode page from template |
| 8 | `pipeline/rss.py` | Updates podcast RSS feed |
| 9 | `pipeline/upload.py` | Uploads everything to S3, invalidates CloudFront |

## Data

All article data lives in a single SQLite database (`data/newzyx.db`). Articles flow through states:

```
collected → extracted → scored → published
```

No CSVs, no pandas, no full-file rewrites.

## Project Structure

```
Newzyx/
├── main.py                  # Daily scheduler (runs at 5:02 AM)
├── run_once.py              # One-shot run
├── config.py                # Loads API keys from .env
├── utils.py                 # Text cleanup, content filters, retry logic
├── .env                     # API keys (not committed)
├── .env.example             # Template
├── requirements.txt
│
├── pipeline/
│   ├── db.py                # SQLite database layer
│   ├── collect.py           # Step 1 — scrape URLs
│   ├── extract.py           # Step 2 — pull article text
│   ├── process.py           # Step 3 — AI scoring
│   ├── episode.py           # Steps 4/5/7 — select, script, HTML
│   ├── tts.py               # Step 6 — ElevenLabs TTS
│   ├── rss.py               # Step 8 — RSS feed
│   └── upload.py            # Step 9 — S3 upload
│
├── data/
│   └── newzyx.db            # SQLite database
│
├── website/
│   ├── template.html        # HTML episode template
│   ├── index.html           # Latest episode (auto-generated)
│   ├── today.mp3            # Latest audio (auto-generated)
│   ├── feed.xml             # Podcast RSS feed
│   ├── episodes/            # All episodes organized by date
│   │   └── YYYY-MM-DD/
│   │       ├── YYYY-MM-DD.html
│   │       ├── YYYY-MM-DD.mp3
│   │       ├── YYYY-MM-DD_summary.txt
│   │       └── script.txt
│   ├── NewzyxV2-removebg.png
│   ├── NewzyxV2Favicon.ico
│   └── fmt_artwork.jpg
│
└── assets/
    └── NewzyxV2.jpg          # Source logo
```

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # Fill in your API keys
python run_once.py            # Run the full pipeline once
```

## Configuration

All secrets are in `.env`:

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | GPT-4o-mini for scoring and script polish |
| `ELEVENLABS_API_KEY` | Text-to-speech |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | S3 uploads to `kidsnewsfeed` bucket |
| `DISTRIBUTION_ID` | CloudFront cache invalidation (optional) |

## Article Selection

Articles are selected using weighted scoring:

- **Score threshold**: Only articles scoring 80+ from the LLM
- **Recency boost**: 1.0x today, 0.9x yesterday, 0.7x for 2+ days old
- **Diversity penalty**: 0.6x if same source already selected, 0.8x if same topic
- **Hard minimum**: If fewer than 3 qualify, the episode is skipped entirely
