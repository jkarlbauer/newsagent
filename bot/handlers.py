import telebot

import db
from bot.client import bot
from bot.decorators import registered
from bot.agent import generate_topics
from bot.delivery import _deliver_to_user

# holds generated topics awaiting user confirmation {chat_id: [topics]}
_pending_topics: dict = {}


def _confirmation_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("✅ Looks good", callback_data="ob:confirm"),
        telebot.types.InlineKeyboardButton("🔄 Try again", callback_data="ob:retry"),
    )
    return markup


def _ask_interests(chat_id):
    bot.send_message(chat_id, "What would you like to stay informed about? Describe your interests in your own words.")
    bot.register_next_step_handler_by_chat_id(chat_id, _handle_interests)


def _handle_interests(message):
    chat_id = message.chat.id
    thinking = bot.send_message(chat_id, "Curating your topics...")
    try:
        topics = generate_topics(message.text.strip())
    except Exception:
        bot.edit_message_text("Something went wrong. Please try again.", chat_id, thinking.message_id)
        _ask_interests(chat_id)
        return

    if topics is None:
        bot.edit_message_text("I can't help with that. Please describe the news topics you're interested in.", chat_id, thinking.message_id)
        _ask_interests(chat_id)
        return

    if not topics:
        bot.edit_message_text("I couldn't generate topics from that. Could you describe your interests differently?", chat_id, thinking.message_id)
        _ask_interests(chat_id)
        return

    _pending_topics[chat_id] = topics
    topic_list = "\n".join(f"• {t}" for t in topics)
    bot.edit_message_text(
        f"Here are the topics I'll track for you:\n\n{topic_list}",
        chat_id, thinking.message_id,
        reply_markup=_confirmation_keyboard(),
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("ob:"))
def handle_onboarding_callback(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    cmd = call.data[3:]

    if cmd == "confirm":
        topics = _pending_topics.pop(chat_id, [])
        db.set_topics(chat_id, topics)
        db.set_active(chat_id, True)
        bot.edit_message_text(
            "You're all set! I'll monitor these topics daily and surface the most relevant, breaking stories — "
            "no noise, just what matters.\n\n"
            "Can't wait? Use /getnews to fetch your digest right now.\n\n"
            "Use /unsubscribe at any time to stop.",
            chat_id, call.message.message_id,
        )

    elif cmd == "retry":
        _pending_topics.pop(chat_id, None)
        bot.edit_message_text("No problem. Let's try again.", chat_id, call.message.message_id)
        _ask_interests(chat_id)


@bot.message_handler(commands=["subscribe"])
def handle_subscribe(message):
    chat_id = message.chat.id
    if db.is_registered(chat_id):
        db.set_topics(chat_id, [])
        db.set_active(chat_id, True)
        bot.reply_to(message, "Welcome back! Let's set up your topics again.")
        _ask_interests(chat_id)
        return
    db.create_user(chat_id, message.from_user.username)
    bot.send_message(chat_id, "👋 Hey! I'm your personal news agent. I'll keep you up to date on what matters to you.")
    _ask_interests(chat_id)


@bot.message_handler(commands=["getnews"])
@registered
def handle_getnews(message):
    bot.reply_to(message, "On it! Your digest will arrive here within 10 minutes.")
    try:
        _deliver_to_user(db.get_user(message.chat.id), fast=True)
    except Exception as e:
        print(f"[getnews] delivery failed for {message.chat.id}: {e}")
        bot.send_message(message.chat.id, "Something went wrong while fetching your news. Please try again later.")


@bot.message_handler(commands=["unsubscribe"])
@registered
def handle_unsubscribe(message):
    db.set_active(message.chat.id, False)
    bot.reply_to(message, "You've unsubscribed. Use /subscribe to set up a new digest anytime.")
