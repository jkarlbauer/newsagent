import time
import trafilatura
import urllib.parse
import feedparser
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from trafilatura.settings import use_config
from googlenewsdecoder import gnewsdecoder
from news.models import Article


class Scraper:
    def __init__(self, config):
        self.max_articles = config["max_articles_per_topic"]
        self.topics = config["topics"]
        self.scrape_window = config["scrape_window"]
        self.region = config["region"]
        self.decode_interval = config["decode_interval"]
        self.timeout = config["scraper_timeout"]

        self.trafilatura_config = use_config()
        self.trafilatura_config.set("DEFAULT", "MAX_REDIRECTS", str(config["scraper_max_redirects"]))
        self.trafilatura_config.set("DEFAULT", "RETRY_UNAVAILABLE", str(config["scraper_retry_unavailable"]).lower())

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Referer": "https://www.google.com/",
        }

    def get_feed(self, topic):
        query = urllib.parse.quote(f"{topic} when:{self.scrape_window}")
        rss_url = f"https://news.google.com/rss/search?q={query}&{self.region}"
        return feedparser.parse(rss_url)

    def decode_url(self, link):
        result = gnewsdecoder(link)
        time.sleep(self.decode_interval)
        return result.get("decoded_url") if result.get("status") else None

    def fetch_article(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return trafilatura.extract(response.text, config=self.trafilatura_config)
        except Exception:
            return None

    def scrape_topic(self, topic):
        feed = self.get_feed(topic)

        # Decode URLs sequentially to respect the rate-limit sleep
        entries = []
        for entry in feed.entries[:self.max_articles]:
            url = self.decode_url(entry.link)
            if url:
                entries.append((entry.title, url))
            else:
                print(f"  skipping (decode failed): {entry.title}")

        # Fetch article content in parallel
        articles = []
        with ThreadPoolExecutor(max_workers=len(entries) or 1) as executor:
            futures = {executor.submit(self.fetch_article, url): (title, url) for title, url in entries}
            for future in as_completed(futures):
                title, url = futures[future]
                content = future.result()
                if content:
                    articles.append(Article(title=title, content=content, url=url, topic=topic))
                    print(f"  scraped: {title}")
                else:
                    print(f"  skipping (extraction failed): {title}")
        return articles

    def scrape_all(self):
        articles = []
        with ThreadPoolExecutor(max_workers=len(self.topics)) as executor:
            futures = {executor.submit(self.scrape_topic, topic): topic for topic in self.topics}
            for future in as_completed(futures):
                topic = futures[future]
                print(f"\n=== {topic} ===")
                articles.extend(future.result())
        return articles


