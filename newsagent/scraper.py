import json
import time
import trafilatura
import urllib.parse
import feedparser
from trafilatura.settings import use_config
from googlenewsdecoder import gnewsdecoder
from newsagent.models import Article

class Scraper:
    def __init__(self, config):
        self.max_articles = config["max_articles_per_topic"]
        self.topics = config["topics"]
        self.scrape_window = config["scrape_window"]
        self.region = config["region"]
        self.decode_interval = config["decode_interval"]

        self.trafilatura_config = use_config()
        self.trafilatura_config.set("DEFAULT", "USER_AGENTS", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        self.trafilatura_config.set("DEFAULT", "DOWNLOAD_TIMEOUT", "20")

    def get_feed(self, topic):
        query = urllib.parse.quote(f"{topic} when:{self.scrape_window}")
        rss_url = f"https://news.google.com/rss/search?q={query}&{self.region}"
        return feedparser.parse(rss_url)

    def decode_url(self, link):
        result = gnewsdecoder(link)
        time.sleep(self.decode_interval)
        return result.get("decoded_url") if result.get("status") else None

    def fetch_article(self, url):
        downloaded = trafilatura.fetch_url(url, config=self.trafilatura_config)
        return trafilatura.extract(downloaded, config=self.trafilatura_config) if downloaded else None

    def scrape_topic(self, topic):
        feed = self.get_feed(topic)
        articles = []
        for entry in feed.entries[:self.max_articles]:
            url = self.decode_url(entry.link)
            if not url:
                print(f"  skipping (decode failed): {entry.title}")
                continue
            content = self.fetch_article(url)
            if content:
                articles.append(Article(title=entry.title, content=content, url=url, topic=topic))
                print(f"  scraped: {entry.title}")
            else:
                print(f"  skipping (extraction failed): {entry.title}")
        return articles

    def scrape_all(self):
        articles = []
        for topic in self.topics:
            print(f"\n=== {topic} ===")
            articles.extend(self.scrape_topic(topic))
        return articles


