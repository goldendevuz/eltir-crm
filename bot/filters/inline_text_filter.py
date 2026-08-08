from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from bot.data.texts import normalize
from bot.utils.db_api.quick_commands import show_all_subcategory


class IsSubcategoryName(BoundFilter):
    """Inline so'rov subkategoriya nomiga to'g'ri kelishini tekshiradi.

    Taqqoslash normalize() orqali: aniq mos kelishni talab qilsak, klient
    qo'shgan bitta bo'sh joy ham so'rovni jimgina rad etadi va foydalanuvchi
    hech qanday natija ko'rmaydi.
    """

    async def check(self, query: types.InlineQuery) -> bool:
        subcategories = await show_all_subcategory()
        names = {normalize(s.tg_name) for s in subcategories}
        return normalize(query.query) in names
