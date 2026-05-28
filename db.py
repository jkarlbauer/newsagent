import sqlite3
import json

DB_PATH = "users.db"

CREATE_USERS_TABLE = """
    CREATE TABLE IF NOT EXISTS users (
        chat_id                INTEGER PRIMARY KEY,
        username               TEXT,
        topics                 TEXT    DEFAULT '["artificial intelligence"]',
        n_articles             INTEGER DEFAULT 5,
        scrape_window          TEXT    DEFAULT '24h',
        region                 TEXT    DEFAULT 'hl=en-US&gl=US&ceid=US:en',
        delivery_hour          INTEGER DEFAULT 7,
        delivery_minute        INTEGER DEFAULT 0,
        timezone               TEXT    DEFAULT 'Europe/Berlin',
        active                 INTEGER DEFAULT 1,
        created_at             TEXT    DEFAULT CURRENT_TIMESTAMP
    )
"""

_MIGRATIONS = [
    ("scrape_window",       "TEXT DEFAULT '24h'"),
    ("region",              "TEXT DEFAULT 'hl=en-US&gl=US&ceid=US:en'"),
    ("last_delivered_date", "TEXT"),
]

GET_USER       = "SELECT * FROM users WHERE chat_id = ?"
GET_ALL_ACTIVE = "SELECT * FROM users WHERE active = 1"
INSERT_USER    = "INSERT INTO users (chat_id, username) VALUES (?, ?)"
UPDATE_TOPICS  = "UPDATE users SET topics = ? WHERE chat_id = ?"
UPDATE_SCHEDULE = "UPDATE users SET delivery_hour = ?, delivery_minute = ?, timezone = ? WHERE chat_id = ?"
UPDATE_ACTIVE  = "UPDATE users SET active = ? WHERE chat_id = ?"
UPDATE_LAST_DELIVERED = "UPDATE users SET last_delivered_date = ? WHERE chat_id = ?"
DELETE_USER    = "DELETE FROM users WHERE chat_id = ?"


def init():
    with sqlite3.connect(DB_PATH) as c:
        c.execute(CREATE_USERS_TABLE)
        for col, definition in _MIGRATIONS:
            try:
                c.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
            except sqlite3.OperationalError:
                pass  # column already exists


def get_user(chat_id: int) -> dict | None:
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        row = c.execute(GET_USER, (chat_id,)).fetchone()
    if row is None:
        return None
    user = dict(row)
    user["topics"] = json.loads(user["topics"])
    return user


def get_all_active_users() -> list[dict]:
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(GET_ALL_ACTIVE).fetchall()
    users = []
    for row in rows:
        user = dict(row)
        user["topics"] = json.loads(user["topics"])
        users.append(user)
    return users


def is_registered(chat_id: int) -> bool:
    return get_user(chat_id) is not None


def create_user(chat_id: int, username: str | None = None) -> dict:
    existing = get_user(chat_id)
    if existing:
        return existing
    with sqlite3.connect(DB_PATH) as c:
        c.execute(INSERT_USER, (chat_id, username))
    return get_user(chat_id)


def delete_user(chat_id: int) -> None:
    with sqlite3.connect(DB_PATH) as c:
        c.execute(DELETE_USER, (chat_id,))


def set_topics(chat_id: int, topics: list[str]) -> None:
    with sqlite3.connect(DB_PATH) as c:
        c.execute(UPDATE_TOPICS, (json.dumps(topics), chat_id))


def set_schedule(chat_id: int, hour: int, minute: int, timezone: str) -> None:
    with sqlite3.connect(DB_PATH) as c:
        c.execute(UPDATE_SCHEDULE, (hour, minute, timezone, chat_id))


def set_active(chat_id: int, active: bool) -> None:
    with sqlite3.connect(DB_PATH) as c:
        c.execute(UPDATE_ACTIVE, (int(active), chat_id))


def mark_delivered(chat_id: int, date_str: str) -> None:
    with sqlite3.connect(DB_PATH) as c:
        c.execute(UPDATE_LAST_DELIVERED, (date_str, chat_id))
