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
from newsagent.utils import closest_to_center

load_dotenv()

with open("config.json") as f:
    config = json.load(f)

config["deepseek_api_key"] = os.environ["DEEPSEEK_API_KEY"]
config["chat_id"] = os.environ["CHAT_ID"]

scraper = Scraper(config)
summarizer = Summarizer(config)

bot = telebot.TeleBot(os.environ["BOT_TOKEN"])


def _embed_worker(articles, config, queue):
    from newsagent.embedder import Embedder
    embedder = Embedder(config)
    queue.put(embedder.embed_articles(articles))


def embed_in_subprocess(articles, config):
    queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=_embed_worker, args=(articles, config, queue))
    p.start()
    result = queue.get()
    p.join()
    return result


def get_news():
    articles = scraper.scrape_all()
    articles = embed_in_subprocess(articles, config)
    closest = closest_to_center(articles, n=config["n_closest"])
    return summarizer.summarize_all(closest)


def format_article(article):
    return f"*{article.title}*\n{article.summary}\n{article.url}"


def send_news(chat_id):
    articles = get_news()
    for article in articles:
        bot.send_message(chat_id, format_article(article), parse_mode="Markdown")


@bot.message_handler(commands=["launch"])
def handle_launch(message):
    bot.reply_to(message, "Scraping and summarising news, please wait...")
    send_news(message.chat.id)


scheduler = BackgroundScheduler()
scheduler.add_job(
    lambda: send_news(config["chat_id"]),
    CronTrigger(hour=6, minute=0, timezone=pytz.timezone("Europe/Berlin")),
)
scheduler.start()

bot.infinity_polling()
