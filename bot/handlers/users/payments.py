from decimal import Decimal

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import LabeledPrice

from bot.data import texts
from bot.data.config import (CURRENCY_CODE, CURRENCY_MULTIPLIER, DELIVERY_FEE,
                             PROVIDER_TOKEN)
from bot.loader import bot, dp
from bot.utils.cart_product_utils import wipe_state_data
from bot.utils.db_api.quick_commands import update_order
from bot.utils.notify_admins import order_notify


def _to_minor_units(value) -> int:
    """Telegram summani eng kichik birlikda kutadi (1 so'm = 100 tiyin)."""
    return int(Decimal(str(value or 0)) * CURRENCY_MULTIPLIER)


async def show_invoice(chat_id: str, state: FSMContext):
    async with state.proxy() as state_data:
        labeled_price_list = []
        product_list = state_data.get("products")
        product_count = len(product_list.keys())
        for key in product_list.keys():
            product = product_list[key]
            labeled_price_list.append(
                LabeledPrice(
                    label=(f"{product['title']} — {product['quantity']} dona × "
                           f"{texts.money(product['price'])}"),
                    amount=_to_minor_units(product['total']),
                ))
        if state_data.get("shipping") == "courier":
            labeled_price_list.append(LabeledPrice(
                label="Yetkazib berish",
                amount=_to_minor_units(DELIVERY_FEE)))
        await bot.send_invoice(
            chat_id=chat_id,
            title=f"Buyurtma: {state_data.get('order_number')}",
            description=f"Jami {product_count} ta mahsulot",
            provider_token=PROVIDER_TOKEN,
            currency=CURRENCY_CODE,
            prices=labeled_price_list,
            payload=str(state_data.get("order_number")),
        )


@dp.pre_checkout_query_handler()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(
        pre_checkout_query_id=pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def payment_process(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    order_id = state_data.get("order_id")
    order_number = state_data.get("order_number")
    await update_order(order_id)
    charge_id = message.successful_payment.provider_payment_charge_id
    await message.answer(
        texts.ORDER_PAID.format(number=order_number) + "\n"
        f"<i>Tranzaksiya ID: {charge_id}</i>"
    )
    await order_notify(state)
    await wipe_state_data(state, products=True)
