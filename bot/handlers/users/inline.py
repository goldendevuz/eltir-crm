import logging

from aiogram import types
from aiogram.dispatcher import FSMContext

from bot.filters import IsSubcategoryName
from bot.loader import dp
from bot.utils.db_api.quick_commands import (get_liked_product,
                                             show_products_inline)

PAGE_SIZE = 25


@dp.inline_handler(IsSubcategoryName())
async def inline_products(query: types.InlineQuery, state: FSMContext):
    offset = int(query.offset) if query.offset else 0
    results = await show_products_inline(query.query, state, offset=offset)

    # next_offset faqat sahifa to'la bo'lsa beriladi. Aks holda Telegram
    # "yana sahifa bor" deb hisoblab qo'shimcha so'rov yuboradi va klient
    # ro'yxatni yuklashda davom etayotgandek turib qoladi.
    next_offset = str(offset + PAGE_SIZE) if len(results) == PAGE_SIZE else ""

    logging.info("inline: user=%s query=%r offset=%s -> %s natija",
                 query.from_user.id, query.query, offset, len(results))
    await query.answer(results=results, cache_time=0, next_offset=next_offset,
                       is_personal=True)


@dp.inline_handler(text="💘 Saralanganlar")
async def liked_list(query: types.InlineQuery, state: FSMContext):
    state_data = await state.get_data()
    liked_products_id = state_data.get("liked_products") or []
    results = await get_liked_product(liked_products_id=liked_products_id,
                                      state=state)
    logging.info("inline saralangan: user=%s -> %s natija",
                 query.from_user.id, len(results))
    await query.answer(results=results, cache_time=0, is_personal=True)


# Oxirgi bo'lib ro'yxatdan o'tadi, shuning yuqoridagilar mos kelmagandagina
# ishlaydi. Busiz mos kelmagan so'rov jimgina yo'qoladi: hech qanday handler
# ishlamaydi, logda iz qolmaydi va foydalanuvchi uchun bot javob bermagandek
# ko'rinadi. Endi bunday holat ham logga tushadi, ham foydalanuvchiga ko'rinadi.
@dp.inline_handler()
async def inline_fallback(query: types.InlineQuery, state: FSMContext):
    logging.warning("inline MOS KELMADI: user=%s query=%r",
                    query.from_user.id, query.query)
    await query.answer(
        results=[],
        cache_time=0,
        is_personal=True,
        switch_pm_text="Katalogni ochish uchun bosing",
        switch_pm_parameter="katalog",
    )
