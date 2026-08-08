"""Savatni tahrirlash ekrani: qatorlarni varaqlash va miqdorni o'zgartirish.

Miqdorni o'zgartirish mantiqi bu yerda takrorlanmaydi — hammasi
bot.utils.cart orqali. Ilgari har bir handler "miqdorni oshir, jamini
qayta hisobla, 0 bo'lsa o'chir" qadamlarini o'zicha yozgan edi va savat
ekranidan qo'shishda ombor umuman tekshirilmasdi.
"""
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InputMediaPhoto

from bot.data import texts
from bot.keyboards.inline.callback_datas import (pagination_callback,
                                                 pagination_edit_callback)
from bot.keyboards.inline.gen_keyboard import CartKeyboardGen
from bot.loader import bot, dp
from bot.states.cart_states import PaginationStates
from bot.utils import cart
from bot.utils.cart_product_utils import check_quantity, stock_allows
from bot.utils.db_api.quick_commands import get_product


def line_caption(item: dict) -> str:
    """Savat qatorining matni — to'rt joyda bir xil ko'rinishi uchun."""
    return (f"{item['title']}\n\n"
            f"{item['quantity']} dona × {texts.money(item['price'])} = "
            f"{texts.amount(item['total'])}")


def indexed_product_id(page: int, state_data: dict):
    """Sahifa raqami bo'yicha mahsulot id'si. Faqat haqiqiy qatorlar."""
    ids = dict(enumerate(cart.lines(state_data).keys(), start=1))
    if not ids:
        return None
    return ids.get(page) or ids[1]


async def _render(call, state_data, page: int, edit_mode: bool = True):
    product_id = indexed_product_id(page, state_data)
    if product_id is None:
        return False
    item = cart.lines(state_data)[product_id]
    product = await get_product(int(product_id))
    keyboard = CartKeyboardGen(page=page, data=state_data)
    markup = (keyboard.build_edit_keyboard() if edit_mode
              else keyboard.build_pagination_keyboard())
    media = InputMediaPhoto(product.image_file_id, caption=line_caption(item))
    await call.message.edit_media(media=media, reply_markup=markup)
    return True


@dp.callback_query_handler(pagination_callback.filter())
async def paginate_cart_products(call: types.CallbackQuery, callback_data: dict,
                                 state: FSMContext):
    page_number = int(callback_data.get("page"))
    edit = callback_data.get("edit")
    async with state.proxy() as state_data:
        await _render(call, state_data, page_number, edit_mode=(edit != "False"))
    await call.answer()


@dp.callback_query_handler(
    pagination_edit_callback.filter(edit="True", add="False", reduce="False"))
async def edit_quantity(call: types.CallbackQuery, callback_data: dict,
                        state: FSMContext):
    await state.update_data(product_id=callback_data.get("product_id"),
                            page=int(callback_data.get("page")),
                            message_data=call.message.message_id)
    await PaginationStates.QUANTITY_EDIT.set()
    await call.message.answer(text=texts.ASK_QUANTITY)


@dp.message_handler(state=PaginationStates.QUANTITY_EDIT)
async def accept_quantity(message: types.Message, state: FSMContext):
    if not await check_quantity(message=message):
        return
    quantity = int(message.text)
    async with state.proxy() as state_data:
        product_id = state_data.get("product_id")
        allowed, stock = await stock_allows(product_id, quantity)
        if not allowed:
            await message.answer(texts.out_of_stock(stock))
            return
        page = state_data.get("page")
        message_id = state_data.get("message_data")
        cart.set_quantity(state_data, await get_product(int(product_id)),
                          quantity)
        item = cart.lines(state_data).get(str(product_id))
        if item is not None:
            markup = CartKeyboardGen(page=page, data=state_data).build_edit_keyboard()
            await bot.edit_message_caption(
                chat_id=message.chat.id, message_id=message_id,
                caption=line_caption(item), reply_markup=markup)
        state_data.pop('message_data', None)
        state_data.pop('page', None)
    await state.reset_state(with_data=False)
    await message.answer(texts.CART_UPDATED)


@dp.callback_query_handler(pagination_edit_callback.filter(reduce="True"))
async def reduce_quantity(call: types.CallbackQuery, callback_data: dict,
                          state: FSMContext):
    page = int(callback_data.get("page"))
    product_id = callback_data.get("product_id")
    async with state.proxy() as state_data:
        product = await get_product(int(product_id))
        left = cart.change_quantity(state_data, product, -1)
        if cart.is_empty(state_data):
            await call.message.delete()
            await call.message.answer(texts.CART_EMPTY)
            await call.answer()
            return
        # Qator o'chgan bo'lsa sahifa raqami eskirdi — boshiga qaytamiz.
        await _render(call, state_data, 1 if left == 0 else page)
    await call.answer(texts.REMOVED_FROM_CART if left == 0 else texts.CART_UPDATED)


@dp.callback_query_handler(pagination_edit_callback.filter(add="True"))
async def add_quantity(call: types.CallbackQuery, callback_data: dict,
                       state: FSMContext):
    page = int(callback_data.get("page"))
    product_id = callback_data.get("product_id")
    async with state.proxy() as state_data:
        wanted = cart.quantity_of(state_data, product_id) + 1
        allowed, stock = await stock_allows(product_id, wanted)
        if not allowed:
            await call.answer(texts.out_of_stock(stock), show_alert=True)
            return
        cart.set_quantity(state_data, await get_product(int(product_id)), wanted)
        await _render(call, state_data, page)
    await call.answer(texts.ADDED_TO_CART)


@dp.callback_query_handler(text="end_edit")
async def end_editing(call: types.CallbackQuery, state: FSMContext):
    from bot.handlers.users.cart import show_cart

    await call.message.delete()
    await show_cart(call, state)
