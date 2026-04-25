import time
from openai import OpenAI, APIStatusError

PROMPT_PATH = "prompts/summarize.md"
MAX_RETRIES = 4
BACKOFF_BASE = 2


class Summarizer:
    def __init__(self, config):
        self.client = OpenAI(
            api_key=config["deepseek_api_key"],
            base_url="https://api.deepseek.com",
        )
        self.model = config["deepseek_model"]
        with open(PROMPT_PATH) as f:
            self.prompt = f.read()

    def summarize(self, article):
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.prompt},
                        {"role": "user", "content": article.content},
                    ],
                )
                article.summary = response.choices[0].message.content.strip()
                return article
            except APIStatusError as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                wait = BACKOFF_BASE ** attempt
                print(f"  API error {e.status_code}, retrying in {wait}s... ({attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait)

    def summarize_all(self, articles):
        for article in articles:
            self.summarize(article)
        return articles
