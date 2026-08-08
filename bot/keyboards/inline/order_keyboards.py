from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.data import texts
from bot.keyboards.inline.callback_datas import (payment_callback,
                                                 shipping_callback,
                                                 user_address_callback)
from bot.utils.db_api.schemas.db_tables import UserAddresses


async def generate_addresses_keyboard(state: FSMContext):
    state_data = await state.get_data()
    user_id = state_data['user_db_id']
    addresses = await UserAddresses.query.where(
        UserAddresses.user_id == user_id).gino.all()
    if not addresses:
        return
    keyboard = InlineKeyboardMarkup()
    for address in addresses:
        keyboard.insert(
            InlineKeyboardButton(
                text=address.address,
                callback_data=user_address_callback.new(
                    id=address.id, name=address.address),
            )
        )
    return keyboard


def gen_check_keyboard():
    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [InlineKeyboardButton(text=texts.BTN_YES, callback_data="make_order"),
         InlineKeyboardButton(text=texts.BTN_NO,
                              callback_data="cancel_order")],
    ])


def gen_shipping_keyboard():
    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [InlineKeyboardButton(text=texts.BTN_PICKUP,
                              callback_data=shipping_callback.new('pickup')),
         InlineKeyboardButton(text=texts.BTN_COURIER,
                              callback_data=shipping_callback.new('courier'))],
    ])


def gen_payment_keyboard():
    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [InlineKeyboardButton(text=texts.BTN_CASH,
                              callback_data=payment_callback.new('cash')),
         InlineKeyboardButton(text=texts.BTN_CARD,
                              callback_data=payment_callback.new('card'))],
    ])
