"""Bot uchun ma'lumot qatlami — Django ORM ustida.

Ilgari bu yerda Gino (SQLAlchemy) ishlatilardi va jadvallar `db_tables.py`
da ikkinchi marta ta'riflanardi. Ikki sxema doim bir-biriga mos turishi
kerak edi: Django'ga ustun qo'shilsa, mirror ham yangilanmasa bot INSERT
qilganda NotNullViolationError bilan yiqilardi. Endi yagona manba —
`tgbot/models.py`.

Django ORM sinxron, aiogram esa asinxron. Shuning uchun har bir so'rov
`sync_to_async` orqali alohida bajariladi; `thread_sensitive=True` barcha
so'rovni bitta threadga yig'adi, ya'ni bitta ulanish ishlatiladi.

MUHIM: bu yerdagi funksiyalar natijani doim ro'yxat/obyekt qilib qaytaradi
va kerakli bog'lanishlarni `select_related` bilan oldindan yuklaydi.
Async kontekstda dangasa (lazy) yuklash `SynchronousOnlyOperation` beradi.
"""
from decimal import Decimal
from functools import wraps

from asgiref.sync import sync_to_async
from django.db import close_old_connections
from django.db.models import F, Q, Value
from django.db.models.functions import Greatest

from tgbot.models import (Category, OrderProduct, Orders, Product, Subcategory,
                          TgUser, UserAddresses)


def _db(func):
    """Sinxron ORM funksiyasini botdan chaqirsa bo'ladigan holga keltiradi.

    `close_old_connections` — bot haftalab ishlaydi, Postgres esa bo'sh
    turgan ulanishni uzib qo'yishi mumkin; eskirgani tashlanmasa keyingi
    so'rov "server closed the connection unexpectedly" bilan yiqiladi.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        def call():
            close_old_connections()
            try:
                return func(*args, **kwargs)
            finally:
                close_old_connections()

        return await sync_to_async(call, thread_sensitive=True)()

    return wrapper


# ------------------------------------------------------------------ katalog


@_db
def get_parent_child():
    """Kategoriyalar — asosiy menyu tugmalari uchun."""
    return list(Category.objects.order_by("position", "name"))


@_db
def get_child_parent(category_id: int):
    """Bitta kategoriyaning subkategoriyalari."""
    return list(Subcategory.objects
                .filter(category_id=category_id)
                .order_by("position", "name"))


@_db
def get_product(product_id: int):
    return (Product.objects
            .select_related("subcategory")
            .filter(id=product_id)
            .first())


@_db
def get_subcategory_products(subcategory_id: int):
    """Subkategoriyadagi mahsulotlar, katalogdagi tartibda."""
    return list(Product.objects
                .select_related("subcategory")
                .filter(subcategory_id=subcategory_id)
                .order_by("position", "id"))


@_db
def get_liked_products(liked_products_id: list):
    """Saralanganlar — holatdagi tartibni saqlagan holda."""
    ids = [int(pid) for pid in liked_products_id]
    found = {p.id: p for p in Product.objects
             .select_related("subcategory").filter(id__in=ids)}
    return [found[pid] for pid in ids if pid in found]


@_db
def search_products(query: str, limit: int = 30):
    """Nom va tarkib bo'yicha qidiruv.

    Sotuvda bo'lmagan mahsulotlar chiqmaydi — mijozga taklif qilib bo'lmasa
    ro'yxatni to'ldirishning ma'nosi yo'q.
    """
    text = query.strip()
    return list(Product.objects
                .select_related("subcategory")
                .filter(available=True)
                .filter(Q(title__icontains=text)
                        | Q(composition__icontains=text)
                        | Q(kind__icontains=text))
                .order_by("position", "id")[:limit])


@_db
def reduce_stock(product_id: int, quantity: int):
    """Buyurtma berilganda ombordan ayiradi.

    GREATEST bilan: bir vaqtda kelgan ikki buyurtma qoldiqni manfiyga
    tushirib yubormasligi kerak.
    """
    Product.objects.filter(id=product_id).update(
        stock=Greatest(F("stock") - Value(Decimal(quantity)),
                       Value(Decimal("0"))),
    )


# -------------------------------------------------------------------- mijoz


@_db
def get_user(user_id: int):
    return TgUser.objects.filter(user_id=user_id).first()


@_db
def create_user(user_id: int, name: str = "", username: str = ""):
    """Ro'yxatdan o'tkazish. Qayta /start bosilsa dublikat yaratmaydi."""
    user, _ = TgUser.objects.get_or_create(
        user_id=user_id,
        defaults={"name": name or "", "username": username or ""},
    )
    return user


@_db
def get_user_addresses(user_pk: int):
    return list(UserAddresses.objects.filter(user_id=user_pk))


@_db
def save_user_address(user_pk: int, address: str):
    """Yangi manzilni eslab qoladi — keyingi buyurtmada tugma bo'lib chiqadi."""
    obj, _ = UserAddresses.objects.get_or_create(user_id=user_pk,
                                                 address=address)
    return obj


# ---------------------------------------------------------------- buyurtma


@_db
def create_order(user_pk: int, order_number: str, total_price):
    """Botdan kelgan buyurtma.

    `source` shu yerda aniq beriladi: Django modelidagi default do'kon
    sotuvi (SHOP) — u panelda operator ochadigan buyurtma uchun.
    """
    return Orders.objects.create(
        tg_user_id=user_pk,
        order_number=order_number,
        total_price=total_price,
        source=Orders.TELEGRAM,
    )


@_db
def add_order_line(order_id: int, product_id: int, quantity: int,
                   single_price):
    return OrderProduct.objects.create(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        single_price=single_price,
    )


@_db
def get_user_orders(tg_user_pk: int, limit: int = 10):
    """Mijozning oxirgi buyurtmalari."""
    return list(Orders.objects
                .filter(tg_user_id=tg_user_pk)
                .order_by("-created_at")[:limit])


@_db
def get_order_lines(order_id: int):
    """Buyurtmadagi qatorlar — qayta buyurtma uchun ham ishlatiladi."""
    return list(OrderProduct.objects
                .select_related("product")
                .filter(order_id=order_id))


@_db
def update_order(order_id: int):
    """To'lov tasdiqlangach chaqiriladi."""
    Orders.objects.filter(id=order_id).update(is_paid=True)
