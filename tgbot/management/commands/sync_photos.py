# -*- coding: utf-8 -*-
"""Upload product photos to Telegram once and cache the returned file_id.

Why this exists: inline query results must reference media Telegram already
holds — there is no way to upload a file while answering an inline query, and
a local /media/ URL is not reachable from Telegram's servers. So every photo
is pushed once here, and the bot then refers to products by file_id.

Photos are sent to the first ADMINS chat and the message is deleted right
after, so it is a scratch upload rather than a visible post. That admin must
have pressed /start on the bot at least once.

    python manage.py sync_photos          # faqat file_id yo'q mahsulotlar
    python manage.py sync_photos --force  # hammasini qayta yuklash
"""
import asyncio
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from bot.data.config import ADMINS, BOT_TOKEN
from tgbot.models import Product


class Command(BaseCommand):
    help = "Mahsulot rasmlarini Telegramga yuklab, file_id larni saqlaydi"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true",
                            help="file_id bor mahsulotlarni ham qayta yuklash")
        parser.add_argument("--chat", default=None,
                            help="Yuklash uchun chat id (default: birinchi admin)")

    def handle(self, *args, **options):
        chat_id = options["chat"] or (ADMINS[0] if ADMINS else None)
        if not chat_id:
            raise CommandError("ADMINS bo'sh va --chat berilmadi")

        qs = Product.objects.exclude(image="")
        if not options["force"]:
            qs = qs.filter(image_file_id="")
        products = list(qs)
        if not products:
            self.stdout.write("Yangilanadigan rasm yo'q")
            return

        # Yuklash — async, bazaga yozish — sync. Django ORM ni event loop
        # ichidan chaqirib bo'lmaydi, shuning uchun natijani yig'ib olamiz.
        jobs = [(p.pk, p.slug, Path(p.image.path)) for p in products]
        results, failed = asyncio.new_event_loop().run_until_complete(
            self._upload(jobs, chat_id))

        for pk, file_id in results:
            # Faqat shu ustunni yozamiz — parallel ishlayotgan bot boshqa
            # maydonlarni o'zgartirgan bo'lishi mumkin.
            Product.objects.filter(pk=pk).update(image_file_id=file_id)

        self.stdout.write(self.style.SUCCESS(
            f"{len(results)} ta rasm yuklandi"
            + (f", {failed} ta xato" if failed else "")))

    async def _upload(self, jobs, chat_id):
        from aiogram import Bot
        from aiogram.types import InputFile

        bot = Bot(token=BOT_TOKEN)
        results, failed = [], 0
        try:
            for pk, slug, path in jobs:
                if not path.exists():
                    self.stderr.write(f"  ! fayl yo'q: {path}")
                    failed += 1
                    continue
                try:
                    msg = await bot.send_photo(chat_id, InputFile(str(path)))
                    file_id = msg.photo[-1].file_id
                    await bot.delete_message(chat_id, msg.message_id)
                except Exception as err:
                    self.stderr.write(f"  ! {slug}: {err}")
                    failed += 1
                    continue
                results.append((pk, file_id))
                self.stdout.write(f"  {slug} -> {file_id[:24]}…")
        finally:
            await bot.session.close()
        return results, failed
