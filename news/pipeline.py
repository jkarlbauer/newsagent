import multiprocessing

from config import config
from news.scraper import Scraper
from news.summarizer import Summarizer
from news.scorers import Scorer, select_top, CombinedScorer
from news.logger import save_run
from news import store

_summarizer = Summarizer(config)
_EMBED_TIMEOUT = config["embed_timeout"]
_DEFAULT_SCORER = CombinedScorer()


def _embed_worker(articles, cfg, queue):
    try:
        from news.embedder import Embedder
        queue.put(("ok", Embedder(cfg).embed_articles(articles)))
    except Exception as e:
        queue.put(("error", str(e)))


def _embed_in_subprocess(articles, embedding_model=None):
    cfg = {**config}
    if embedding_model:
        cfg["embedding_model"] = embedding_model
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()
    p = ctx.Process(target=_embed_worker, args=(articles, cfg, queue))
    p.start()
    try:
        result = queue.get(timeout=_EMBED_TIMEOUT)
    except Exception:
        p.terminate()
        p.join()
        raise RuntimeError(f"Embedding subprocess timed out after {_EMBED_TIMEOUT}s.")
    p.join()
    status, payload = result
    if status == "error":
        raise RuntimeError(f"Embedding subprocess crashed: {payload}")
    return payload


def get_news(user: dict, scorer: Scorer = _DEFAULT_SCORER, fast: bool = False) -> list:
    scraper = Scraper({**config, **user})
    articles = scraper.scrape_all()
    if not articles:
        return []
    embedding_model = config["embedding_model_fast"] if fast else None
    articles = _embed_in_subprocess(articles, embedding_model=embedding_model)
    path = store.save_embedded(user["chat_id"], articles)
    articles = store.load_embedded(path)
    articles = scorer.score(articles)
    top = select_top(articles, n=user["n_articles"])
    save_run(user["chat_id"], articles, selected_urls={a.url for a in top})
    return _summarizer.summarize_all(top)
