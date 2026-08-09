import os

import django

# Bot ham, admin panel ham bitta Django ilovasi ustida ishlaydi: modellar
# `tgbot/models.py` da, ma'lumot qatlami esa `bot/utils/db_api/quick_commands.py`
# da. Modellarni import qiladigan har qanday narsadan OLDIN Django yuklanishi
# shart, shuning uchun bu blok fayl boshida turadi.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tgbot_shop.settings")
django.setup()

from aiogram import executor  # noqa: E402

from bot import filters, handlers, middlewares  # noqa: E402,F401
from bot.loader import dp  # noqa: E402
from bot.utils.notify_admins import on_startup_notify  # noqa: E402
from bot.utils.set_bot_commands import set_default_commands  # noqa: E402


async def on_startup(dispatcher):
    await on_startup_notify(dispatcher)
    await set_default_commands(dispatcher)


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
