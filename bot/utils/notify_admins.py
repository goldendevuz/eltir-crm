import logging

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext

from bot.data import texts
from bot.data.config import ADMINS
from bot.loader import bot
from bot.utils.cart_product_utils import create_cart_list


async def on_startup_notify(dp: Dispatcher):
    for admin in ADMINS:
        try:
            await dp.bot.send_message(admin, texts.BOT_STARTED)
        except Exception as err:
            # Admin hali botga /start bosmagan bo'lsa "chat not found"
            # qaytadi — bu botni to'xtatishga arzimaydi.
            logging.warning("Adminga (%s) xabar yuborilmadi: %s", admin, err)


async def order_notify(state: FSMContext):
    async with state.proxy() as state_data:
        address = state_data.get("user_address") or "—"
        phone_number = state_data.get("phone_number") or "—"
        order_number = state_data.get("order_number")
        shipping = ("Kuryer" if state_data.get("shipping") == "courier"
                    else "Olib ketish")
    cart_list = await create_cart_list(state)
    answer = texts.ADMIN_NEW_ORDER.format(
        number=order_number, cart=cart_list, shipping=shipping,
        address=address, phone=phone_number,
    )
    for admin in ADMINS:
        try:
            await bot.send_message(admin, answer)
        except Exception as err:
            logging.warning("Adminga (%s) buyurtma yuborilmadi: %s", admin, err)
