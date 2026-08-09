"""Savat ustidagi barcha amallar — yagona manba.

Ilgari savatni o'zgartirish mantiqi uch joyda takrorlangan edi: mahsulot
kartochkasidagi +/- (cart.py), savatni tahrirlash ekranidagi +/-
(cart_pagination.py) va qo'lda miqdor kiritish. Har birida "miqdorni oshir,
jamini qayta hisobla, 0 bo'lsa o'chir" qadamlari qaytadan yozilgan va
o'zaro biroz farq qilardi.

Muhim: savat qatori faqat mijoz haqiqatan qo'shganda paydo bo'ladi. Avval
ProductInfo middleware ko'rilgan har bir mahsulotni `quantity: 0` bilan
yozib qo'yardi — natijada savat hech narsa qo'shilmagan holda ham "to'la"
ko'rinardi va ro'yxatda "0 dona" qatorlari chiqardi.
"""
from decimal import Decimal


def _products(state_data) -> dict:
    products = state_data.get("products")
    if products is None:
        products = {}
        state_data["products"] = products
    return products


def lines(state_data) -> dict:
    """Faqat haqiqiy qatorlar (miqdori musbat)."""
    return {pid: item for pid, item in _products(state_data).items()
            if int(item.get("quantity", 0)) > 0}


def is_empty(state_data) -> bool:
    return not lines(state_data)


def count(state_data) -> int:
    return sum(int(i["quantity"]) for i in lines(state_data).values())


def total(state_data) -> Decimal:
    return sum((Decimal(str(i["price"])) * int(i["quantity"])
                for i in lines(state_data).values()), Decimal("0"))


def quantity_of(state_data, product_id) -> int:
    item = _products(state_data).get(str(product_id))
    return int(item["quantity"]) if item else 0


def set_quantity(state_data, product, quantity: int):
    """Miqdorni belgilaydi. 0 yoki manfiy bo'lsa qatorni o'chiradi.

    `product` — Product modeli obyekti; qator mavjud bo'lmasa shundan yaratiladi,
    shuning uchun oldindan "bo'sh" yozuv qoldirishning hojati yo'q.
    """
    products = _products(state_data)
    pid = str(product.id)
    quantity = int(quantity)

    if quantity <= 0:
        products.pop(pid, None)
        if str(state_data.get("product_id")) == pid:
            state_data.pop("product_id", None)
        return 0

    price = Decimal(str(product.price))
    products[pid] = {
        "title": product.title,
        "quantity": quantity,
        "price": str(price),
        "total": str(price * quantity),
    }
    state_data["product_id"] = pid
    return quantity


def change_quantity(state_data, product, delta: int):
    """Miqdorni delta ga o'zgartiradi va yangi qiymatni qaytaradi."""
    return set_quantity(state_data, product,
                        quantity_of(state_data, product.id) + delta)


def clear(state_data):
    state_data["products"] = {}
    state_data.pop("product_id", None)
