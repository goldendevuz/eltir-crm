from sqlalchemy import func, or_

from bot.utils.db_api.db_gino import db
from bot.utils.db_api.schemas.db_tables import (CategoryGino, OrderProductGino,
                                                OrdersGino, ProductGino,
                                                SubcategoryGino, TgUserGino)
from bot.data import texts


async def get_parent_child():  # get child model with children attribute
    query = SubcategoryGino.outerjoin(CategoryGino).select()
    return await query.gino.load(
        CategoryGino.distinct(CategoryGino.id).load(children=SubcategoryGino)).all()


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


async def get_subcategory_products(subcategory_id: int):
    """Subkategoriyadagi mahsulotlar, katalogdagi tartibda."""
    async with db.transaction():
        query = (ProductGino.load(parent=SubcategoryGino)
                 .where(ProductGino.subcategory_id == subcategory_id)
                 .order_by(ProductGino.position, ProductGino.id))
        return await query.gino.all()


async def get_liked_products(liked_products_id: list):
    """Saralanganlar — holatdagi tartibni saqlagan holda."""
    products = []
    async with db.transaction():
        for product_id in liked_products_id:
            query = ProductGino.load(parent=SubcategoryGino).where(
                ProductGino.id == int(product_id))
            product = await query.gino.first()
            if product is not None:
                products.append(product)
    return products


async def search_products(query: str, limit: int = 30):
    """Nom va tarkib bo'yicha qidiruv (Enatega storefront'idagi kabi).

    Sotuvda bo'lmagan mahsulotlar chiqmaydi — mijozga taklif qilib bo'lmasa
    ro'yxatni to'ldirishning ma'nosi yo'q.
    """
    pattern = f"%{query.strip()}%"
    async with db.transaction():
        db_query = (ProductGino.load(parent=SubcategoryGino)
                    .where(ProductGino.available.is_(True))
                    .where(or_(ProductGino.title.ilike(pattern),
                               ProductGino.composition.ilike(pattern),
                               ProductGino.kind.ilike(pattern)))
                    .order_by(ProductGino.position, ProductGino.id)
                    .limit(limit))
        return await db_query.gino.all()


async def get_user_orders(tg_user_id: int, limit: int = 10):
    """Mijozning oxirgi buyurtmalari."""
    async with db.transaction():
        db_query = (OrdersGino.query
                    .where(OrdersGino.tg_user_id == tg_user_id)
                    .order_by(OrdersGino.created_at.desc())
                    .limit(limit))
        return await db_query.gino.all()


async def get_order_lines(order_id: int):
    """Buyurtmadagi qatorlar — qayta buyurtma uchun ham ishlatiladi."""
    async with db.transaction():
        db_query = (OrderProductGino.load(parent=ProductGino)
                    .where(OrderProductGino.order_id == order_id))
        return await db_query.gino.all()


async def reduce_stock(product_id: int, quantity: int):
    """Buyurtma berilganda ombordan ayiradi.

    GREATEST bilan: bir vaqtda kelgan ikki buyurtma qoldiqni manfiyga
    tushirib yubormasligi kerak.
    """
    async with db.transaction():
        await (ProductGino.update
               .values(stock=func.greatest(ProductGino.stock - quantity, 0))
               .where(ProductGino.id == product_id)
               .gino.status())


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
