# Morning Digest

A personal daily briefing delivered to your inbox every morning. Pulls from RSS feeds across finance, geopolitics, and tech, then uses Gemini to synthesize the noise into a clean, opinionated email.

## What it does

- Fetches headlines from 13 RSS feeds across finance, geopolitics, and tech
- Sends everything to Gemini 2.5 Flash, which writes a prose-only digest — no bullet points, no filler
- Delivers a styled HTML email with section headers, dark theme, and a speed round of quick takes

## Stack

- **Python** — feedparser, google-genai, smtplib
- **Gemini 2.5 Flash** — summarization and tone
- **Gmail SMTP** — delivery
- **GitHub Actions** — scheduled daily at 6 AM ET

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and fill in your credentials:
   - `GEMINI_API_KEY` — free at [aistudio.google.com](https://aistudio.google.com/app/apikey)
   - `GMAIL_ADDRESS` — your Gmail address
   - `GMAIL_APP_PASSWORD` — a Gmail App Password (not your regular password)
   - `RECIPIENT_EMAIL` — where to send the digest
3. Install dependencies: `pip install -r requirements.txt`
4. Run manually: `python digest.py`

To run on a schedule, add your credentials as GitHub Actions secrets and enable the included workflow.
