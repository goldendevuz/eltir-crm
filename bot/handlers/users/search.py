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

# Pastdagi doimiy menyu tugmalari. Qidiruv holatida turганda ular so'rov deb
# qabul qilinmasligi kerak: mijoz "🛒 Savat" bosganda bot «🛒 Savat» bo'yicha
# qidirib, "hech narsa topilmadi" deb javob berardi.
MENU_BUTTONS = {texts.BTN_PRODUCTS, texts.BTN_CART, texts.BTN_SEARCH,
                texts.BTN_MY_ORDERS}


@dp.message_handler(text=texts.BTN_SEARCH, state="*")
@dp.message_handler(Command("qidiruv"), state="*")
async def ask_query(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=False)
    await message.answer(texts.SEARCH_ASK)
    await SearchStates.QUERY.set()


@dp.message_handler(lambda m: (m.text or "") in MENU_BUTTONS,
                    state=SearchStates.QUERY)
async def leave_search(message: types.Message, state: FSMContext):
    """Menyu tugmasi bosildi — qidiruvdan chiqamiz.

    Holatni tozalab, xabarni qayta yo'naltirmaymiz: mijoz tugmani yana
    bossa, endi o'z handleriga tushadi. Shu sababli qisqa izoh beriladi.
    """
    await state.reset_state(with_data=False)
    await message.answer(texts.SEARCH_CANCELLED)


@dp.message_handler(state=SearchStates.QUERY)
async def run_search(message: types.Message, state: FSMContext):
    query = (message.text or "").strip()

    if len(query) < MIN_QUERY:
        await message.answer(texts.SEARCH_TOO_SHORT)
        return

    products = await search_products(query)
    if not products:
        # Holat saqlanadi — mijoz darhol boshqacha yozib ko'rishi mumkin.
        await message.answer(texts.search_empty(query))
        return

    await state.reset_state(with_data=False)
    # Natijalar ham katalog kabi varaqlanadi. Id'lar holatda saqlanadi,
    # chunki varaqlash callback'iga so'rov matni sig'maydi.
    await state.update_data(search_results=[p.id for p in products])
    await message.answer(texts.search_found(query, len(products)))
    await render_product(message, state, products, index=0, mode="search")
