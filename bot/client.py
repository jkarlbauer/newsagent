import telebot

from config import config

bot = telebot.TeleBot(config["bot_token"])
bot.set_my_commands([
    telebot.types.BotCommand("subscribe", "Subscribe to the daily news digest"),
    telebot.types.BotCommand("getnews", "Fetch your news digest now"),
    telebot.types.BotCommand("unsubscribe", "Stop receiving the daily news digest"),
])
