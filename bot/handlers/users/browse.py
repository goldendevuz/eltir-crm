"""Katalogni chatdagi oddiy xabar orqali varaqlash.

Ilgari subkategoriya tugmasi inline galereyani ochardi
(switch_inline_query_current_chat). Galereya ba'zi klientlarda rasmlarni
yuklamay turib qolardi va natijani tanlab bo'lmasdi, shuning uchun katalog
oddiy xabarga ko'chirildi: bitta mahsulot kartochkasi joyida tahrirlanib
varaqlanadi — har bir mahsulot uchun alohida xabar yubormaydi.

Uchta ro'yxat bir xil ko'rinishda varaqlanadi: katalog, saralanganlar va
qidiruv natijalari ("mode").
"""
import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InputMediaPhoto
from aiogram.utils.exceptions import MessageNotModified

from bot.data import texts
from bot.keyboards.inline.callback_datas import (browse_callback,
                                                 liked_browse_callback,
                                                 search_browse_callback)
from bot.keyboards.inline.gen_keyboard import KeyboardGen
from bot.loader import bot, dp
from bot.utils.db_api.quick_commands import (get_liked_products, get_product,
                                             get_subcategory_products)


def _message_of(target):
    """Message ham, CallbackQuery ham kelishi mumkin."""
    if isinstance(target, types.CallbackQuery):
        return target.message
    return None


async def _notify(target, text):
    if isinstance(target, types.CallbackQuery):
        await target.answer(text, show_alert=True)
    else:
        await target.answer(text)


async def render_product(target, state: FSMContext, products: list, index: int,
                         mode: str = "catalog"):
    """Mahsulot kartochkasini ko'rsatadi yoki joyida yangilaydi."""
    if not products:
        await _notify(target, texts.NOTHING_HERE)
        return

    index %= len(products)
    product = products[index]

    async with state.proxy() as state_data:
        state_data["product_info"] = {"is_liked": int(mode == "liked")}
        markup = KeyboardGen(product=product, data=state_data, index=index,
                             total=len(products), mode=mode).build_auto_kb()

    caption = texts.product_card(product)
    message = _message_of(target)
    chat_id = target.from_user.id

    # Rasmli xabarni rasmli xabarga almashtirish mumkin, matnlisini esa yo'q —
    # subkategoriya ro'yxati matn xabari bo'lgani uchun birinchi marta yangi
    # xabar yuboriladi.
    if message is not None and message.photo and product.image_file_id:
        try:
            await bot.edit_message_media(
                chat_id=message.chat.id, message_id=message.message_id,
                media=InputMediaPhoto(media=product.image_file_id,
                                      caption=caption, parse_mode="HTML"),
                reply_markup=markup)
            return
        except MessageNotModified:
            return

    if message is not None:
        try:
            await message.delete()
        except Exception:
            # Eski xabarni o'chirib bo'lmasa ham yangisini yuborish kerak.
            pass

    if product.image_file_id:
        await bot.send_photo(chat_id=chat_id, photo=product.image_file_id,
                             caption=caption, parse_mode="HTML",
                             reply_markup=markup)
    else:
        await bot.send_message(chat_id=chat_id, text=caption,
                               parse_mode="HTML", reply_markup=markup)


@dp.callback_query_handler(browse_callback.filter())
async def browse_products(call: types.CallbackQuery, callback_data: dict,
                          state: FSMContext):
    subcategory_id = int(callback_data["subcategory_id"])
    index = int(callback_data["index"])
    products = await get_subcategory_products(subcategory_id)
    logging.info("browse: user=%s subkategoriya=%s index=%s -> %s mahsulot",
                 call.from_user.id, subcategory_id, index, len(products))
    await call.answer()
    await render_product(call, state, products, index)


@dp.callback_query_handler(liked_browse_callback.filter())
async def browse_liked(call: types.CallbackQuery, callback_data: dict,
                       state: FSMContext):
    index = int(callback_data["index"])
    state_data = await state.get_data()
    products = await get_liked_products(state_data.get("liked_products") or [])
    await call.answer()
    await render_product(call, state, products, index, mode="liked")


@dp.callback_query_handler(search_browse_callback.filter())
async def browse_search(call: types.CallbackQuery, callback_data: dict,
                        state: FSMContext):
    """Qidiruv natijalari holatdagi id ro'yxati bo'yicha varaqlanadi.

    So'rov matnini callback_data'ga sig'dirib bo'lmaydi (64 bayt), shuning
    uchun natijalar bir marta topilib, id'lari holatda saqlanadi.
    """
    index = int(callback_data["index"])
    state_data = await state.get_data()
    ids = state_data.get("search_results") or []
    products = [p for p in
                [await get_product(int(pid)) for pid in ids] if p is not None]
    await call.answer()
    await render_product(call, state, products, index, mode="search")


@dp.callback_query_handler(text="noop")
async def noop(call: types.CallbackQuery):
    """Varaqlash qatoridagi "3/18" tugmasi — faqat ko'rsatkich."""
    await call.answer()
