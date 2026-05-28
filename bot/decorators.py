from functools import wraps

import db
from bot.client import bot


def registered(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        if not db.is_registered(message.chat.id):
            bot.reply_to(message, "Please register first with /subscribe.")
            return
        return func(message, *args, **kwargs)
    return wrapper
