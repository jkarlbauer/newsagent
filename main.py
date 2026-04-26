import json
import os
import multiprocessing
import telebot
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from newsagent.scraper import Scraper
from newsagent.summarizer import Summarizer
from newsagent.scoring import score_articles, select_top

load_dotenv()

with open("config.json") as f:
    config = json.load(f)
with open("system.json") as f:
    config.update(json.load(f))

config["deepseek_api_key"] = os.environ["DEEPSEEK_API_KEY"]
config["chat_id"] = os.environ["CHAT_ID"]

scraper = Scraper(config)
summarizer = Summarizer(config)

bot = telebot.TeleBot(os.environ["BOT_TOKEN"])

EMBED_TIMEOUT = config["embed_timeout"]


def _embed_worker(articles, config, queue):
    from newsagent.embedder import Embedder
    embedder = Embedder(config)
    queue.put(embedder.embed_articles(articles))


def embed_in_subprocess(articles, config):
    queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=_embed_worker, args=(articles, config, queue))
    p.start()
    try:
        result = queue.get(timeout=EMBED_TIMEOUT)
    except Exception:
        p.terminate()
        raise RuntimeError("Embedding subprocess timed out or crashed.")
    p.join()
    return result


def get_news():
    articles = scraper.scrape_all()
    if not articles:
        print("No articles scraped.")
        return []
    articles = embed_in_subprocess(articles, config)
    articles = score_articles(articles)
    top = select_top(articles, n=config["n_articles"])
    return summarizer.summarize_all(top)


def _escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_article(article):
    title = _escape_html(article.title)
    summary = _escape_html(article.summary)
    coverage = round(article.coverage * 100)
    return f"<b>{title}</b>\nCoverage: {coverage}%\n{summary}\n{article.url}"


def send_news(chat_id):
    articles = get_news()
    if not articles:
        bot.send_message(chat_id, "No articles found.")
        return
    for article in articles:
        bot.send_message(chat_id, format_article(article), parse_mode="HTML")


@bot.message_handler(commands=["launch"])
def handle_launch(message):
    bot.reply_to(message, "Scraping and summarising news, please wait...")
    send_news(message.chat.id)


scheduler = BackgroundScheduler()
scheduler.add_job(
    lambda: send_news(config["chat_id"]),
    CronTrigger(
        hour=config["delivery_hour"],
        minute=config["delivery_minute"],
        timezone=pytz.timezone(config["delivery_timezone"]),
    ),
)
scheduler.start()

bot.infinity_polling()
