from sqlalchemy import (BigInteger, Boolean, Column, DECIMAL, ForeignKey,
                        Integer, String, Text, VARCHAR, sql)

from bot.utils.db_api.db_gino import BaseModel, TimedBaseModel


class CategoryGino(BaseModel):
    __tablename__ = 'tgbot_category'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), index=True)
    tg_name = Column(String(200))
    description = Column(Text)
    slug = Column(String(160), unique=True)
    position = Column(Integer)

    query: sql.select

    def __init__(self, **kw):
        super().__init__(**kw)
        self._children = set()

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, child):
        self._children.add(child)


class SubcategoryGino(BaseModel):
    __tablename__ = 'tgbot_subcategory'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), index=True)
    tg_name = Column(String(200))
    description = Column(Text)
    slug = Column(String(160), unique=True)
    category_id = Column(Integer, ForeignKey('tgbot_category.id'))
    position = Column(Integer)


class ProductGino(BaseModel):
    __tablename__ = 'tgbot_product'
    id = Column(Integer, primary_key=True)
    title = Column(VARCHAR(150), index=True)
    description = Column(Text)
    price = Column(DECIMAL(precision=12, scale=2))
    available = Column(Boolean)
    slug = Column(String(160), index=True)
    image = Column(VARCHAR(100))
    image_file_id = Column(VARCHAR(200), index=True)
    subcategory_id = Column(Integer, ForeignKey('tgbot_subcategory.id'))
    brand = Column(VARCHAR(16))
    kind = Column(VARCHAR(120))
    composition = Column(Text)
    flavour = Column(Text)
    storage = Column(Text)
    diameter = Column(VARCHAR(40))
    weight = Column(VARCHAR(40))
    is_new = Column(Boolean)
    position = Column(Integer)
    old_price = Column(DECIMAL(precision=12, scale=2), default=0)
    unit = Column(VARCHAR(8), default="DONA")
    stock = Column(DECIMAL(precision=10, scale=2), default=0)


# Django's `default=` is applied in Python by the ORM and leaves no DEFAULT on
# the column, so every NOT NULL column the bot does not name explicitly in an
# insert would go in as NULL and raise NotNullViolationError. These mirrors
# therefore carry the same defaults as the Django models.
class TgUserGino(TimedBaseModel):
    __tablename__ = 'tgbot_tguser'
    id = Column(Integer, primary_key=True)
    # Telegram ids exceed 2^31; Integer here overflows asyncpg's int4 encoder.
    user_id = Column(BigInteger, index=True, unique=True)
    name = Column(VARCHAR(100), default="")
    username = Column(VARCHAR(64), default="")
    phone = Column(VARCHAR(32), default="")
    is_blocked = Column(Boolean, default=False)


class OrdersGino(TimedBaseModel):
    __tablename__ = 'tgbot_orders'
    id = Column(Integer, primary_key=True)
    is_paid = Column(Boolean, default=False)
    tg_user_id = Column(Integer, ForeignKey('tgbot_tguser.id'))
    order_number = Column(VARCHAR(25), index=True, unique=True)
    total_price = Column(DECIMAL(precision=12, scale=2), default=0)
    status = Column(VARCHAR(16), default="NEW")
    payment_method = Column(VARCHAR(16), default="CASH")
    phone = Column(VARCHAR(32), default="")
    address = Column(Text, default="")
    comment = Column(Text, default="")
    courier_id = Column(Integer)
    operator_id = Column(Integer)


class OrderProductGino(TimedBaseModel):
    __tablename__ = 'tgbot_orderproduct'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("tgbot_orders.id"))
    product_id = Column(Integer, ForeignKey("tgbot_product.id"))
    quantity = Column(Integer, default=0)
    single_price = Column(DECIMAL(precision=12, scale=2))


class UserAddresses(TimedBaseModel):
    __tablename__ = 'tgbot_useraddresses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('tgbot_tguser.id'))
    address = Column(VARCHAR(150))
