from aiogram import types
from aiogram.dispatcher import FSMContext
from bot.keyboards.inline.gen_keyboard import KeyboardGen
from bot.utils.db_api.db_gino import db
from bot.utils.db_api.schemas.db_tables import SubcategoryGino, CategoryGino, ProductGino, TgUserGino, OrdersGino
from bot.data import texts


async def get_parent_child():  # get child model with children attribute
    query = SubcategoryGino.outerjoin(CategoryGino).select()
    parent = await query.gino.load(CategoryGino.distinct(CategoryGino.id).load(children=SubcategoryGino)).all()
    print(parent)
    print("ended")
    return parent


async def get_child_parent(category_id: int):
    async with db.transaction():
        query = SubcategoryGino.load(parent=CategoryGino).where(CategoryGino.id == category_id)
        result = await query.gino.all()
    return result


async def get_product(product_id: int):
    async with db.transaction():
        product = ProductGino.load(parent=SubcategoryGino)
        result = await product.where(ProductGino.id == product_id).gino.first()
    return result


def _product_result(product, markup, is_liked: bool = False):
    """Inline natijasi: rasm bor bo'lsa foto, aks holda oddiy maqola.

    Telegram inline javobida faylni yuklab bo'lmaydi, shuning uchun rasm
    oldindan yuklangan file_id orqali beriladi (manage.py sync_photos).
    """
    caption = f"<b>{product.title}</b>\n{texts.money(product.price)}"
    if product.image_file_id:
        return types.InlineQueryResultCachedPhoto(
            id=str(product.id),
            photo_file_id=product.image_file_id,
            title=product.title,
            description=texts.money(product.price),
            caption=caption,
            parse_mode="HTML",
            reply_markup=markup,
        )
    return types.InlineQueryResultArticle(
        id=str(product.id),
        title=product.title,
        description=texts.money(product.price),
        input_message_content=types.InputTextMessageContent(
            message_text=caption, parse_mode="HTML"),
        reply_markup=markup,
    )


async def get_liked_product(liked_products_id: list, state: FSMContext):
    query_answer = []
    async with db.transaction():
        for product_id in liked_products_id:
            db_query = ProductGino.load(parent=SubcategoryGino)
            product = await db_query.where(ProductGino.id == product_id).gino.first()
            async with state.proxy() as state_data:
                state_data["product_info"] = {"is_liked": 1}
                markup = KeyboardGen(product=product, data=state_data).build_product_kb()
            query_answer.append(_product_result(product, markup, is_liked=True))
    return query_answer


async def show_products_inline(subcategory_title: str, state: FSMContext, offset: int):
    start = offset
    end = offset + 25
    query_answer = []
    async with db.transaction():
        query = ProductGino.load(parent=SubcategoryGino).where(SubcategoryGino.tg_name == subcategory_title)
        result = await query.gino.all()
    for product in result[start:end]:
        async with state.proxy() as state_data:
            state_data["product_info"] = {"is_liked": 0}
            keyboard = KeyboardGen(product=product, data=state_data)
            markup = keyboard.build_product_kb()
        query_answer.append(_product_result(product, markup))
    return query_answer


async def get_user(user_id: int):
    result = await TgUserGino.query.where(TgUserGino.user_id == user_id).gino.first()
    return result


async def show_all_subcategory():
    subcategories = await SubcategoryGino.query.gino.all()
    return subcategories


async def get_ordered_products(order_id: int):
    async with db.transaction():
        query = SubcategoryGino.load(parent=OrdersGino).where(CategoryGino.id == order_id)
        result = await query.gino.all()
    return result


async def update_order(order_id: int):
    order = await OrdersGino.query.where(OrdersGino.id == order_id).gino.first()
    await order.update(is_paid=True).apply()
    return
