from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.inline.callback_datas import (browse_callback,
                                                 liked_browse_callback,
                                                 navigate_callback)
from bot.utils.db_api.quick_commands import get_child_parent, get_parent_child


async def category_keyboard(liked_products_quantity: int = None,
                            has_liked_products: bool = None):
    current_level = 0
    categories_qs = await get_parent_child()
    categories_markup = InlineKeyboardMarkup(row_width=1)
    if has_liked_products:
        categories_markup.insert(InlineKeyboardButton(
            text=f"💘 Saralanganlar ({liked_products_quantity})",
            callback_data=liked_browse_callback.new(index=0)))
    for category in categories_qs:
        callback_data = navigate_callback(level=current_level + 1,
                                          category_id=category.id)
        categories_markup.insert(InlineKeyboardButton(
            text=f"{category.tg_name}", callback_data=callback_data))
    return categories_markup


async def subcategory_keyboard(category_id: int):
    """Subkategoriya tugmalari mahsulot ko'ruvchisini ochadi.

    Ilgari bu tugmalar switch_inline_query_current_chat ishlatgan: bosilganda
    inline galereya ochilardi, u esa ba'zi klientlarda rasmlar yuklanmay
    turib qolardi va tanlab bo'lmasdi. Endi oddiy callback — mahsulot chatga
    xabar bo'lib keladi.
    """
    current_level = 1
    subcategories_qs = await get_child_parent(category_id=category_id)
    subcategories_markup = InlineKeyboardMarkup(row_width=1)
    for subcategory in subcategories_qs:
        subcategories_markup.insert(InlineKeyboardButton(
            text=f"{subcategory.tg_name}",
            callback_data=browse_callback.new(subcategory_id=subcategory.id,
                                              index=0)))
    subcategories_markup.row(InlineKeyboardButton(
        text="◀ Orqaga",
        callback_data=navigate_callback(level=current_level - 1)))
    return subcategories_markup
