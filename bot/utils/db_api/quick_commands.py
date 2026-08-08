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
