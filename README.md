# NewsAgent

A Telegram bot that scrapes recent news, identifies the most relevant articles using semantic embeddings, and delivers per-article summaries — automatically every morning at 6AM (Berlin time) or on demand via `/launch`.

## How it works

1. **Scrape** — fetches articles from Google News RSS for configured topics
2. **Embed** — encodes each article using `all-mpnet-base-v2` sentence transformer with chunking and averaging
3. **Rank** — finds the N articles closest to the embedding centroid (most representative of the overall news)
4. **Summarise** — generates a short summary for each via DeepSeek
5. **Deliver** — sends title, summary, and URL to the user via Telegram

## Usage

- `/launch` — trigger a fresh news run manually
- Automatic delivery every morning at **6:00 AM (Europe/Berlin)**

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
  "topics": ["ai", "artificial intelligence", "anthropic", "openai", "gemini"],
  "max_articles_per_topic": 30,
  "n_closest": 5,
  "scrape_window": "24h",
  "decode_interval": 2,
  "region": "hl=en-US&gl=US&ceid=US:en",
  "deepseek": "deepseek-chat",
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

## Project structure

```
newsagent/
├── newsagent/          # core package
│   ├── scraper.py      # Google News RSS scraper
│   ├── embedder.py     # sentence transformer embeddings
│   ├── summarizer.py   # DeepSeek summarisation
│   ├── utils.py        # centroid + closest-to-center
│   └── models.py       # Article dataclass
├── prompts/
│   └── summarize.md    # DeepSeek prompt (edit freely)
├── main.py             # Telegram bot entrypoint
├── config.json         # runtime configuration
├── .env.example        # environment variable template
├── Dockerfile
└── docker-compose.yml
```
