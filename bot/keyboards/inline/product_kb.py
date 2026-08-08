from decimal import Decimal

from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.data import texts
from bot.keyboards.inline.callback_datas import navigate_callback, test_callback, gen_buy_callback, liked_product


async def product_keyboard(product_id: str, product_title: str, tg_name: str, product_price: int,
                           category_id: int, state: FSMContext, liked: bool = False) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    callback_data = gen_buy_callback(product_id=product_id, product_price=product_price,
                                     category_id=category_id, edit=False, liked=liked)
    async with state.proxy() as state_data:
        price_text = texts.money(product_price)
        if product_id not in state_data["products"].keys():
            product_name = f'Sotib olish "{product_title}" · {price_text}'
        else:
            quantity = state_data["products"][product_id]["quantity"]
            product_name = (f"{quantity} dona | Sotib olish "
                            f'"{product_title}" · {price_text}')

        liked_products_list = state_data['liked_products']
        if product_id not in liked_products_list:
            text = "❤"
            liked_callback = liked_product.new(add=True, delete=False, product_id=product_id)
        else:
            text = "💘"
            liked_callback = liked_product.new(add=False, delete=True, product_id=product_id)
        another_text = tg_name if not liked else "💘 Saralanganlar"

    markup.insert(InlineKeyboardButton(text=product_name, callback_data=callback_data))
    markup.add(InlineKeyboardButton(text=text, callback_data=liked_callback))
    markup.insert(InlineKeyboardButton(
        text="🛒 " + texts.money(total_func(state_data["products"])),
        callback_data=callback_data))
    markup.add(InlineKeyboardButton(text="◀ Orqaga", callback_data=navigate_callback(level=1,
                                                                                    category_id=category_id)))
    markup.insert(InlineKeyboardButton(text="Yana " + another_text, switch_inline_query_current_chat=another_text))
    return markup


def product_edit_kb(data: dict, product_id: str, liked: str) -> InlineKeyboardMarkup:
    product = data["products"][product_id]
    liked_products_list = data['liked_products']
    if product_id not in liked_products_list:
        text = "❤"
        liked_callback = liked_product.new(add=True, delete=False, product_id=product_id)
    else:
        text = "💘"
        liked_callback = liked_product.new(add=False, delete=True, product_id=product_id)
    if liked == "False":
        another_text = data["product_data"]["subcategory_name"]
    else:
        another_text = "💘 Saralanganlar"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="-1", callback_data=gen_buy_callback(product_id=product_id,
                                                                           product_price=product['price'],
                                                                           reduce=True, edit=True)),

            InlineKeyboardButton(text="✏" + str(product['quantity']) + " dona",
                                 callback_data=gen_buy_callback(product_id=product_id,
                                                                product_price=product["price"],
                                                                edit=True)),

            InlineKeyboardButton(text="+1", callback_data=gen_buy_callback(product_id=product_id,
                                                                           product_price=product['price'],
                                                                           add=True, edit=True))
        ],
        [
            InlineKeyboardButton(text=text, callback_data=liked_callback),
            InlineKeyboardButton(text="🛒 " + texts.money(total_func(data["products"])),
                                 callback_data=test_callback.new(1))
        ],
        [
            InlineKeyboardButton(text="◀ Orqaga",
                                 callback_data=navigate_callback(level=1,
                                                                 category_id=data['product_data']['category_id'])),
            InlineKeyboardButton(text="Yana " + another_text,
                                 switch_inline_query_current_chat=another_text)
        ]
    ])
    return markup


def total_func(product_list: dict):
    total = 0
    for key in product_list.keys():
        price = product_list[key]["price"]
        quantity = product_list[key]["quantity"]
        total += (Decimal(price) * quantity)
    return total
