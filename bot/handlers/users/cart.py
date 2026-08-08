
from aiogram import types
from aiogram.dispatcher import FSMContext

from bot.keyboards.inline.callback_datas import buy_callback, liked_product, edit_quantity
from bot.keyboards.inline.gen_keyboard import cart_edit_kb, KeyboardGen, CartKeyboardGen
from bot.loader import dp, bot
from bot.states.cart_states import ProductStates
from decimal import Decimal

from bot.utils.cart_product_utils import (check_quantity, create_cart_list,
                                          stock_allows, wipe_state_data)
from bot.utils import cart
from bot.utils.db_api.quick_commands import get_product
from bot.utils.message_edit import edit_markup
from bot.data import texts


# async def update_product_info(product_id: int, state: FSMContext):
#
#     async with state.proxy() as state_data:
#         if str(product_id) not in state_data['products'].keys():
#             product = await get_product(product_id)
#             products = {
#                 str(product.id):
#                     {
#                         "title": product.title,
#                         "quantity": 0,
#                         "price": str(product.price),
#                         "total": "0.00",
#                     },
#             }
#             state_data['products'].update(products)
#     return True


def product_total_price(state_data: dict):
    products_list = state_data.get("products")
    result = str(products_list[state_data.get("product_id")]['quantity'] * Decimal(
        products_list[state_data.get("product_id")]['price']))
    return result


@dp.callback_query_handler(buy_callback.filter())
async def add_to_cart(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    product_id = callback_data.get("product_id")
    product = await get_product(int(product_id))
    if product is None:
        await call.answer(texts.PRODUCT_GONE, show_alert=True)
        return
    async with state.proxy() as state_data:
        wanted = cart.quantity_of(state_data, product_id) + 1
        allowed, stock = await stock_allows(product_id, wanted)
        if not allowed:
            await call.answer(texts.out_of_stock(stock), show_alert=True)
            return
        cart.set_quantity(state_data, product, wanted)
        keyboard = await KeyboardGen.from_product_id(product_id=int(product_id), data=state_data)
        markup = keyboard.build_auto_kb()
    await call.answer(texts.ADDED_TO_CART)
    await edit_markup(call, markup)


@dp.callback_query_handler(edit_quantity.filter(edit="True", add="False", reduce="False"))
async def edit_product_quantity(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    product_id = callback_data.get("product_id")
    await bot.send_message(chat_id=call.from_user.id, text=texts.ASK_QUANTITY)
    await state.update_data(message_data=dict(call))
    await state.update_data(product_id=product_id)
    await ProductStates.QUANTITY_EDIT.set()


@dp.message_handler(state=ProductStates.QUANTITY_EDIT)
async def accept_product_quantity(message: types.Message, state: FSMContext):
    if not await check_quantity(message=message):
        return
    async with state.proxy() as state_data:
        quantity = int(message.text)
        product_id = state_data.get("product_id")
        allowed, stock = await stock_allows(product_id, quantity)
        if not allowed:
            await message.answer(texts.out_of_stock(stock))
            return
        message_data = state_data.get("message_data")
        cart.set_quantity(state_data, await get_product(int(product_id)), quantity)
        keyboard = await KeyboardGen.from_product_id(product_id=int(product_id), data=state_data)
        markup = keyboard.build_edit_kb()
        await edit_markup(message_data, markup)
        del state_data['message_data']
    await message.answer("✅ Bajarildi")
    await state.reset_state(with_data=False)


@dp.callback_query_handler(edit_quantity.filter(edit="True", add="True"))
async def plus_quantity(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    product_id = callback_data.get("product_id")
    product = await get_product(int(product_id))
    async with state.proxy() as state_data:
        wanted = cart.quantity_of(state_data, product_id) + 1
        allowed, stock = await stock_allows(product_id, wanted)
        if not allowed:
            await call.answer(texts.out_of_stock(stock), show_alert=True)
            return
        cart.set_quantity(state_data, product, wanted)
        keyboard = await KeyboardGen.from_product_id(product_id=int(product_id), data=state_data)
        markup = keyboard.build_auto_kb()
    await call.answer(texts.ADDED_TO_CART)
    await edit_markup(call, markup)


@dp.callback_query_handler(edit_quantity.filter(edit="True", reduce="True"))
async def minus_quantity(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    product_id = callback_data.get("product_id")
    product = await get_product(int(product_id))
    async with state.proxy() as state_data:
        left = cart.change_quantity(state_data, product, -1)
        keyboard = await KeyboardGen.from_product_id(product_id=int(product_id), data=state_data)
        markup = keyboard.build_auto_kb()
    await call.answer(texts.REMOVED_FROM_CART if left == 0 else texts.CART_UPDATED)
    await edit_markup(call, markup)


@dp.callback_query_handler(liked_product.filter())
async def add_liked(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    product_id = int(callback_data.get("product_id"))
    async with state.proxy() as state_data:
        if callback_data.get("delete") == "False":
            state_data["liked_products"].append(product_id)
            await call.answer("Saralanganlarga qo'shildi")
        elif callback_data.get("add") == "False":
            for count, value in enumerate(state_data['liked_products']):
                if value == product_id:
                    del state_data["liked_products"][count]
            await call.answer("Saralanganlardan olib tashlandi")
        keyboard = await KeyboardGen.from_product_id(product_id=product_id, data=state_data)
        markup = keyboard.build_auto_kb()
    await edit_markup(call, markup)


@dp.callback_query_handler(text='show_cart')
async def show_cart(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as state_data:
        if cart.is_empty(state_data):
            await call.answer(texts.CART_EMPTY, show_alert=True)
            return
    answer = await create_cart_list(state)
    await call.answer()
    await bot.send_message(chat_id=call.from_user.id, text=answer, reply_markup=cart_edit_kb)


@dp.callback_query_handler(text="wipe_cart")
async def wipe_cart(call: types.CallbackQuery, state: FSMContext):
    await wipe_state_data(state, products=True)
    await bot.edit_message_text(text=texts.CART_CLEARED, chat_id=call.from_user.id,
                                message_id=call.message.message_id)
    await call.answer()


@dp.callback_query_handler(text="edit_cart")
async def edit_cart(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as state_data:
        product_id = int(list(state_data['products'].keys())[0])
        product = await get_product(product_id=product_id)
        cart_product = state_data['products'][str(product_id)]
        keyboard = CartKeyboardGen(data=state_data)
        markup = keyboard.build_pagination_keyboard()
        caption = (f"{cart_product['title']}\n\n"
                   f"{cart_product['quantity']} dona × "
                   f"{texts.money(cart_product['price'])} = "
                   f"{texts.money(cart_product['total'])}")
    await call.message.answer_photo(photo=product.image_file_id, caption=caption,
                                    reply_markup=markup)
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    await call.answer()
