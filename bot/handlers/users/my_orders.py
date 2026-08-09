"""Mijozning buyurtmalar tarixi va qayta buyurtma qilish.

Enatega storefront'ida ikkalasi ham bor edi va do'kon uchun ayni muddao:
mijoz odatda o'sha-o'sha mahsulotlarni qayta oladi, shuning uchun eski
buyurtmani bir tugma bilan savatga qaytarish katalogni qaytadan varaqlashdan
ancha tez.
"""
import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.data import texts
from bot.keyboards.inline.callback_datas import reorder_callback
from bot.loader import dp
from bot.utils.cart_product_utils import stock_allows
from bot.utils.db_api.quick_commands import (get_order_lines, get_user,
                                             get_user_orders)


@dp.message_handler(text=texts.BTN_MY_ORDERS, state="*")
@dp.message_handler(Command("buyurtmalarim"), state="*")
async def my_orders(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=False)
    user = await get_user(int(message.from_user.id))
    if user is None:
        await message.answer(texts.NO_ORDERS)
        return

    orders = await get_user_orders(user.id)
    if not orders:
        await message.answer(texts.NO_ORDERS)
        return

    for order in orders:
        lines = await get_order_lines(order.id)
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton(
            text=texts.BTN_REORDER,
            callback_data=reorder_callback.new(order_id=order.id)))
        await message.answer(texts.order_history_card(order, lines),
                             parse_mode="HTML", reply_markup=markup)


@dp.callback_query_handler(reorder_callback.filter(), state="*")
async def reorder(call: types.CallbackQuery, callback_data: dict,
                  state: FSMContext):
    """Eski buyurtma qatorlarini savatga qaytaradi.

    Narx bugungi narxdan olinadi (eskisidan emas) va omborda yetmagan
    mahsulotlar tashlab ketiladi — mijozga nima o'tmagani aytiladi.
    """
    order_id = int(callback_data["order_id"])
    lines = await get_order_lines(order_id)
    if not lines:
        await call.answer(texts.REORDER_EMPTY, show_alert=True)
        return

    added, skipped = 0, []
    async with state.proxy() as state_data:
        state_data.setdefault("products", {})
        for line in lines:
            product = line.product
            if product is None:
                continue
            allowed, _ = await stock_allows(product.id, line.quantity)
            if not allowed:
                skipped.append(product.title)
                continue
            state_data["products"][str(product.id)] = {
                "title": product.title,
                "quantity": line.quantity,
                # Bugungi narx: eski buyurtmadagi narx eskirgan bo'lishi mumkin.
                "price": str(product.price),
                "total": str(product.price * line.quantity),
            }
            added += 1

    logging.info("reorder: user=%s order=%s -> %s qo'shildi, %s o'tkazildi",
                 call.from_user.id, order_id, added, len(skipped))
    await call.answer()
    await call.message.answer(texts.reorder_result(added, skipped))
