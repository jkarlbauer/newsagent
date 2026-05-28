import logging
import threading
from datetime import datetime
import pytz

import db
from bot.client import bot
from config import config
from news.pipeline import get_news
from news.scorers import LLMRankingScorer
from news.formatter import format_article, digest_header

log = logging.getLogger(__name__)
_delivery_thread: threading.Thread | None = None
_delivery_lock = threading.Lock()


def _send_to_user(chat_id: int, articles: list) -> None:
    bot.send_message(chat_id, digest_header(articles), parse_mode="HTML")
    for article in articles:
        bot.send_message(chat_id, format_article(article), parse_mode="HTML")


def _deliver_to_user(user: dict, fast: bool = False) -> None:
    try:
        scorer = LLMRankingScorer(config, user["topics"])
        articles = get_news(user, scorer=scorer, fast=fast)
        if articles:
            _send_to_user(user["chat_id"], articles)
        today = datetime.now(pytz.timezone(user["timezone"])).date().isoformat()
        db.mark_delivered(user["chat_id"], today)
    except Exception:
        log.exception("Delivery failed for chat_id=%s", user.get("chat_id"))


def _is_due(user: dict) -> bool:
    now = datetime.now(pytz.timezone(user["timezone"]))
    today = now.date().isoformat()
    if user.get("last_delivered_date") == today:
        return False
    scheduled_minutes = user["delivery_hour"] * 60 + user["delivery_minute"]
    now_minutes = now.hour * 60 + now.minute
    return now_minutes >= scheduled_minutes


def _run_deliveries(users: list[dict]) -> None:
    for user in users:
        _deliver_to_user(user)


def scheduled_delivery() -> None:
    global _delivery_thread
    with _delivery_lock:
        if _delivery_thread and _delivery_thread.is_alive():
            log.warning("Previous delivery batch still running; skipping this tick")
            return
        due = [u for u in db.get_all_active_users() if _is_due(u)]
        if not due:
            return
        _delivery_thread = threading.Thread(
            target=_run_deliveries, args=(due,), name="delivery", daemon=True
        )
        _delivery_thread.start()
