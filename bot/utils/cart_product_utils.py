from decimal import Decimal

from aiogram import types
from aiogram.dispatcher import FSMContext

from bot.data import texts
from bot.data.config import DELIVERY_FEE


async def create_cart_list(state: FSMContext) -> str:
    answer_texts = []
    total = Decimal()
    async with state.proxy() as state_data:
        for product_id in state_data.get("products").keys():
            product = state_data['products'].get(product_id)
            answer_texts.append(
                f"<b>{product['title']}</b>\n"
                f"{product['quantity']} dona × {texts.money(product['price'])}"
                f" = {texts.money(product['total'])}\n"
            )
            total += Decimal(product['total'])
        body = "\n".join(answer_texts)
        if state_data.get("shipping") == "courier":
            total += Decimal(DELIVERY_FEE)
            delivery_text = (f"{texts.CART_DELIVERY}: "
                             f"<i>{texts.money(DELIVERY_FEE)}</i>\n")
        else:
            delivery_text = ""
    return (
        f"{texts.CART_TITLE}\n\n"
        "----------\n"
        f"{body}"
        "----------\n\n"
        f"{delivery_text}"
        f"<b>{texts.CART_TOTAL}</b>: <i>{texts.money(total)}</i>"
    )


async def check_quantity(message: types.Message) -> bool:
    try:
        quantity = int(message.text)
    except ValueError:
        await message.answer(texts.QUANTITY_NOT_INT)
        return False
    if quantity > 0:
        return True
    await message.answer(texts.QUANTITY_TOO_SMALL)
    return False


async def gen_total_price(state: FSMContext) -> Decimal:
    async with state.proxy() as state_data:
        product_list = state_data['products']
        total = Decimal()
        for key in product_list.keys():
            price = product_list[key]["price"]
            quantity = product_list[key]["quantity"]
            total += Decimal(price) * quantity
        if not total:
            return Decimal("0.00")
        if state_data.get("shipping") == "courier":
            total += Decimal(DELIVERY_FEE)
    return total


async def wipe_state_data(state: FSMContext, products: bool = False):
    field_list = ['order_id', 'order_number', 'phone_number', 'user_address',
                  'user_db_id', "shipping", "payment"]
    async with state.proxy() as state_data:
        if products:
            del state_data['products']
        for field in field_list:
            if field in state_data.keys():
                del state_data[field]
