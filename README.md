# NewsAgent

An AI agent that fetches recent news, identifies the most relevant and diverse articles using semantic embeddings, and delivers per-article summaries via Telegram — automatically at a configured time or on demand via `/launch`.

## How it works

1. **Fetch** — fetches articles from Google News RSS for configured topics
2. **Embed** — encodes each article using a sentence transformer in an isolated subprocess (RAM-safe)
3. **Score** — ranks articles by `(1 - distance_to_centroid) × duplicate_count`: articles that are central to the overall news and widely covered score highest
4. **Deduplicate** — greedily selects the top N articles, skipping any that are too similar (cosine similarity ≥ 0.85) to an already-selected one, so each distinct story appears only once
5. **Summarise** — generates a short summary for each via DeepSeek
6. **Deliver** — sends title, summary, and URL to the user via Telegram

## Usage

- `/launch` — trigger a fresh news run manually
- Automatic delivery at the time configured in `config.json`

## Setup

**1. Clone and create a virtual environment:**
```bash
git clone <repo-url>
cd newsagent
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

**2. Configure environment variables:**
```bash
cp .env.example .env
```
Fill in `.env`:
```
DEEPSEEK_API_KEY=your_deepseek_api_key
BOT_TOKEN=your_telegram_bot_token
CHAT_ID=your_telegram_chat_id
```
> Get your `CHAT_ID` by messaging [@userinfobot](https://t.me/userinfobot) on Telegram.

**3. Configure the bot** via `config.json`:
```json
{
  "topics": ["ai", "artificial intelligence", "anthropic", "openai", "gemini", "deepseek"],
  "max_articles_per_topic": 30,
  "scrape_window": "24h",
  "region": "hl=en-US&gl=US&ceid=US:en",
  "deepseek_model": "deepseek-chat",
  "n_articles": 5,
  "delivery_hour": 6,
  "delivery_minute": 0,
  "delivery_timezone": "Europe/Berlin"
}
```

Advanced parameters (rarely need changing) are in `system.json`:
```json
{
  "decode_interval": 2,
  "embedding_model": "all-mpnet-base-v2",
  "embedding_batch_size": 8,
  "embedding_overlap": 0.15
}
```

**4. Run:**
```bash
python main.py
```

## Docker

```bash
docker-compose up -d
```

Logs:
```bash
docker logs -f newsagent
```

## Project structure

```
newsagent/
├── newsagent/          # core package
│   ├── scraper.py      # Google News RSS scraper
│   ├── embedder.py     # sentence transformer embeddings
│   ├── scoring.py      # article scoring and deduplication
│   ├── summarizer.py   # DeepSeek summarisation
│   └── models.py       # Article dataclass
├── prompts/
│   └── summarize.md    # DeepSeek system prompt (edit freely)
├── main.py             # Telegram bot entrypoint
├── config.json         # user-facing configuration
├── system.json         # system-level parameters
├── .env.example        # environment variable template
├── Dockerfile
└── docker-compose.yml
```
