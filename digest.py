import os
import re
import smtplib
import feedparser
from google import genai
from google.genai import types
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

FEEDS = {
    "finance": [
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/topstories/",
        "https://finance.yahoo.com/news/rssindex",
        "http://feeds.bbci.co.uk/news/business/rss.xml",
        "https://www.theguardian.com/uk/business/rss",
        "https://api.axios.com/feed/",
    ],
    "geopolitics": [
        "https://feeds.npr.org/1004/rss.xml",
        "https://foreignpolicy.com/feed/",
        "https://rss.dw.com/rdf/rss-en-all",
    ],
    "tech": [
        "https://hnrss.org/frontpage",
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://www.wired.com/feed/rss",
    ],

}

MAX_ARTICLES_PER_FEED = 3


def fetch_articles(feeds: dict) -> dict:
    articles = {}
    for category, urls in feeds.items():
        articles[category] = []
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:MAX_ARTICLES_PER_FEED]:
                    title = entry.get("title", "").strip()
                    summary = entry.get("summary", entry.get("description", "")).strip()
                    link = entry.get("link", "").strip()
                    if title:
                        articles[category].append({
                            "title": title,
                            "summary": summary[:300] if summary else "",
                            "link": link,
                        })
            except Exception as e:
                print(f"  Failed to fetch {url}: {e}")
    return articles


def build_prompt(articles: dict) -> str:
    lines = [
        "You are a well-read, thoughtful friend summarizing the day's news over coffee — "
        "conversational and occasionally witty, but never try-hard. No slang, no hype, no exclamation points. "
        "Write like someone who takes the news seriously but doesn't take themselves too seriously. "
        "Write a morning digest email with the following sections:\n",
        "1. **Finance** — markets and economics. Explain what's happening and why it matters. Dry wit welcome.",
        "2. **Geopolitics** — international news. Clear-eyed and direct. Treat the reader as an adult.",
        "3. **Tech** — tech industry news. Informed opinions are fine; snark for its own sake isn't.",
        "4. **Speed Round** — 4-6 one-sentence takes on anything else worth knowing from today's headlines.\n",
        "For each section write 3-5 paragraphs, one per story. No bullet points or lists — prose only. "
        "Format each paragraph like this: start with a short bold headline (3-6 words, wrapped in <strong>) "
        "followed by a period, then the paragraph text in the same <p> tag. "
        "Example: <p><strong>Fed Holds Rates Steady.</strong> The Federal Reserve opted to...</p> "
        "Each paragraph should stand on its own: lead with the news, add context or a take, move on. "
        "Be concise and substantive. No filler. No corporate speak. No Gen Z slang. "
        "Use plain HTML only (p, strong, em). Do NOT use ul, li, h3, or any other tags. "
        "Do NOT include <html>, <head>, <body>, or any wrapper tags — just the inner content.\n",
        "Here are today's articles:\n",
    ]

    category_labels = {
        "finance": "FINANCE",
        "geopolitics": "GEOPOLITICS",
        "tech": "TECH",
    }

    for category, items in articles.items():
        lines.append(f"\n--- {category_labels[category]} ---")
        for item in items:
            lines.append(f"- {item['title']}")
            if item["summary"]:
                lines.append(f"  {item['summary']}")

    return "\n".join(lines)


def clean_markdown(text: str) -> str:
    # Convert **bold** to <strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Strip leftover * or --- dividers
    text = re.sub(r'^\s*[-*]{3,}\s*$', '', text, flags=re.MULTILINE)
    return text


def call_gemini(prompt: str) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.85,
            max_output_tokens=8192,
        ),
    )
    return clean_markdown(response.text)


def build_html_email(digest_body: str, date_str: str) -> str:
    section_colors = {
        "Finance": "#f0b429",
        "Geopolitics": "#56ab91",
        "Tech": "#6c63ff",
        "Speed Round": "#4fc3f7",
    }

    # Inject colored section headers
    for section, color in section_colors.items():
        styled = (
            f'<h2 style="color:{color};font-family:\'Segoe UI\',sans-serif;'
            f'font-size:1.1rem;text-transform:uppercase;letter-spacing:2px;'
            f'border-left:4px solid {color};padding-left:12px;margin-top:36px;">'
            f'{section}</h2>'
        )
        digest_body = digest_body.replace(
            f"<h2>{section}</h2>", styled
        ).replace(
            f"<h2><strong>{section}</strong></h2>", styled
        ).replace(
            f"**{section}**", styled
        ).replace(
            f"<strong>{section}</strong>", styled
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Morning Digest</title>
</head>
<body style="margin:0;padding:0;background:#0f0f0f;font-family:'Segoe UI',Arial,sans-serif;color:#e0e0e0;">

  <!-- Header -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#1a1a2e;">
    <tr>
      <td align="center" style="padding:36px 24px 28px;">
        <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:4px;color:#888;margin-bottom:8px;">
          {date_str}
        </div>
        <div style="font-size:2rem;font-weight:700;color:#ffffff;letter-spacing:1px;">
          Morning Digest
        </div>
        <div style="font-size:0.85rem;color:#aaa;margin-top:8px;">
          Finance &middot; Geopolitics &middot; Tech
        </div>
      </td>
    </tr>
  </table>

  <!-- Body -->
  <div style="max-width:640px;margin:0 auto;padding:24px 12px;">
    <div style="background:#1e1e1e;border-radius:12px;padding:28px 24px;line-height:1.75;font-size:0.95rem;color:#d4d4d4;">
      <style>
        .digest-body p {{ margin:0; padding:16px 0; border-bottom:1px solid #2a2a2a; }}
        .digest-body p:last-of-type {{ border-bottom:none; }}
      </style>
      <div class="digest-body">{digest_body}</div>
    </div>
  </div>

  <!-- Footer -->
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:24px;color:#555;font-size:0.75rem;">
        Generated by your personal morning digest &bull; {date_str}
      </td>
    </tr>
  </table>

</body>
</html>"""
    return html


def send_email(html: str, date_str: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Morning Digest — {date_str}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())


def main():
    date_str = datetime.now().strftime("%A, %B %d, %Y").replace(" 0", " ")

    print("Fetching articles...")
    articles = fetch_articles(FEEDS)
    total = sum(len(v) for v in articles.values())
    print(f"  Fetched {total} articles across {len(articles)} categories.")

    print("Calling Gemini...")
    prompt = build_prompt(articles)
    digest_body = call_gemini(prompt)
    print("  Digest generated.")

    print("Building HTML email...")
    html = build_html_email(digest_body, date_str)

    print("Sending email...")
    send_email(html, date_str)
    print(f"  Sent to {RECIPIENT_EMAIL}.")


if __name__ == "__main__":
    main()
