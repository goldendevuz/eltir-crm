"""Katalog bo'yicha qidiruv.

Enatega storefront'ida menyu sahifasida nom va tavsif bo'yicha qidiruv bor
edi; katalog 51 ta mahsulotga yetgach, kategoriyalarni varaqlab yurishdan
ko'ra nomni yozib topish tezroq. Bot tomonida ham xuddi shu mantiq.
"""
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from bot.data import texts
from bot.handlers.users.browse import render_product
from bot.loader import dp
from bot.states.search_states import SearchStates
from bot.utils.db_api.quick_commands import search_products

MIN_QUERY = 2


@dp.message_handler(text=texts.BTN_SEARCH, state="*")
@dp.message_handler(Command("qidiruv"), state="*")
async def ask_query(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=False)
    await message.answer(texts.SEARCH_ASK)
    await SearchStates.QUERY.set()


@dp.message_handler(state=SearchStates.QUERY)
async def run_search(message: types.Message, state: FSMContext):
    query = (message.text or "").strip()
    await state.reset_state(with_data=False)

    if len(query) < MIN_QUERY:
        await message.answer(texts.SEARCH_TOO_SHORT)
        return

    products = await search_products(query)
    if not products:
        await message.answer(texts.search_empty(query))
        return

    # Natijalar ham katalog kabi varaqlanadi. Id'lar holatda saqlanadi,
    # chunki varaqlash callback'iga so'rov matni sig'maydi.
    await state.update_data(search_results=[p.id for p in products])
    await message.answer(texts.search_found(query, len(products)))
    await render_product(message, state, products, index=0, mode="search")
