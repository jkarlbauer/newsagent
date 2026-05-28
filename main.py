from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import db
from bot.client import bot
from bot.delivery import scheduled_delivery
from bot import handlers as _  # noqa: F401 — registers handlers


if __name__ == "__main__":
    db.init()

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        scheduled_delivery,
        CronTrigger(minute="*"),
        max_instances=1,
        coalesce=True,
        misfire_grace_time=30,
    )
    scheduler.start()

    bot.infinity_polling(skip_pending=True)
