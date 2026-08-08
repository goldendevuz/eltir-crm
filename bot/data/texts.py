# -*- coding: utf-8 -*-
"""Botning barcha o'zbekcha matnlari va pul formatlash yordamchilari.

Matnlar bir joyda turgani uchun so'zlashuv uslubini o'zgartirish yoki
keyinchalik boshqa tilni qo'shish oson bo'ladi.
"""
from decimal import Decimal

from bot.data.config import CURRENCY, SHOP_NAME, SHOP_PHONE, SHOP_TAGLINE


def money(value) -> str:
    """12000 -> "12 000 so'm". Narx kiritilmagan bo'lsa alohida matn."""
    amount = Decimal(str(value or 0))
    if amount <= 0:
        return "narx kelishiladi"
    return f"{int(amount):,}".replace(",", " ") + f" {CURRENCY}"


# --- tugmalar ---------------------------------------------------------------
BTN_PRODUCTS = "🛍 Mahsulotlar"
BTN_CART = "🛒 Savat"
BTN_SEARCH = "🔎 Qidiruv"
BTN_MY_ORDERS = "📦 Buyurtmalarim"
BTN_FAVOURITES = "💘 Saralanganlar"
BTN_BACK = "◀ Orqaga"
BTN_EDIT_CART = "✏ Tahrirlash"
BTN_CLEAR_CART = "❌ Tozalash"
BTN_CHECKOUT = "✅ Buyurtma berish"
BTN_FINISH_EDIT = "✅ Tahrirlashni yakunlash"
BTN_YES = "Ha"
BTN_NO = "Yo'q, bekor qilish"
BTN_PICKUP = "🏬 Olib ketaman"
BTN_COURIER = "🚚 Kuryer"
BTN_CASH = "💵 Naqd"
BTN_CARD = "💳 Karta"
BTN_MORE = "Yana "
BTN_BUY = "Sotib olish"

# --- xabarlar ---------------------------------------------------------------
WELCOME = (
    "Assalomu alaykum, {name}!\n\n"
    f"<b>{SHOP_NAME}</b> — {SHOP_TAGLINE}\n"
    "Azizon kolbasa va delikateslarini to'g'ridan-to'g'ri yetkazib beramiz.\n\n"
    "Buyurtma berish uchun <b>🛍 Mahsulotlar</b> tugmasini bosing."
)

HELP = (
    "<b>Buyruqlar ro'yxati</b>\n"
    "/start — botni qayta ishga tushirish\n"
    "/menu — asosiy menyu\n"
    "/help — yordam\n\n"
    f"Savollar bo'yicha: {SHOP_PHONE}"
)

MAIN_MENU = "Asosiy menyu:"
CATALOG_INTRO = "Mahsulotlarimiz bilan tanishing:"
SUBCATEGORY_INTRO = "Bo'limni tanlang:"
CART_EMPTY = "Savat bo'sh"
CART_TITLE = "🛒 <b>Savat</b>"
CART_TOTAL = "Jami"
CART_DELIVERY = "Yetkazib berish"
CART_CLEARED = "Savat tozalandi"

ASK_PHONE = (
    "Telefon raqamingizni yuboring.\n"
    "Pastdagi tugmani bosing yoki qo'lda yozing: <code>+998901234567</code>"
)
BTN_SEND_PHONE = "📱 Raqamni yuborish"
PHONE_INVALID = "Telefon raqam noto'g'ri. Masalan: +998901234567"

ASK_ADDRESS = "Yetkazib berish manzilini yozing:"
ASK_ADDRESS_CHOICE = "Manzilni tanlang yoki yangisini yozing:"
ASK_SHIPPING = "Buyurtmani qanday olasiz?"
ASK_PAYMENT = "To'lov turini tanlang:"
ASK_QUANTITY = "Nechta kerak? Raqam bilan yozing:"

QUANTITY_TOO_SMALL = "Soni 1 dan kam bo'lishi mumkin emas, qaytadan kiriting"
QUANTITY_NOT_INT = "Soni butun son bo'lishi kerak, qaytadan kiriting"

ORDER_CHECK = "Buyurtmani tasdiqlaysizmi?"
ORDER_CANCELLED = "Buyurtma bekor qilindi"
ORDER_ACCEPTED = (
    "✅ Buyurtmangiz qabul qilindi!\n\n"
    "Raqami: <b>{number}</b>\n"
    "Tez orada operatorimiz siz bilan bog'lanadi."
)
ORDER_PAID = (
    "✅ To'lov qabul qilindi. Rahmat!\n"
    "Buyurtma raqami: <b>{number}</b>"
)

PRICE_NOT_SET = (
    "Bu mahsulotning narxi hali kiritilmagan.\n"
    f"Iltimos, {SHOP_PHONE} raqamiga qo'ng'iroq qiling."
)

NOTHING_FOUND = "Hech narsa topilmadi"
FAVOURITES_EMPTY = "Saralanganlar ro'yxati bo'sh"

BOT_STARTED = f"{SHOP_NAME} boti ishga tushdi"

ADMIN_NEW_ORDER = (
    "🆕 <b>Yangi buyurtma</b>\n\n"
    "Raqami: <b>{number}</b>\n"
    "{cart}\n"
    "Yetkazish: {shipping}\n"
    "Manzil: {address}\n"
    "Telefon: {phone}"
)


def unit_label(product) -> str:
    return "kg" if getattr(product, "unit", "DONA") == "KG" else "dona"


def price_line(product) -> str:
    """Narx qatori. Chegirma bo'lsa eski narx chizilgan holda ko'rsatiladi."""
    unit = unit_label(product)
    current = f"{money(product.price)} / {unit}"
    old = getattr(product, "old_price", 0) or 0
    if old and old > product.price:
        return f"{current}   <s>{money(old)}</s>"
    return current


def stock_line(product) -> str:
    """Ombor holati. Aniq son o'rniga holat — qoldiq savdo siri."""
    stock = getattr(product, "stock", 0) or 0
    if not getattr(product, "available", True) or stock <= 0:
        return "\u274c Hozircha tugagan"
    if stock <= 20:
        return f"\u26a0 Oz qoldi: {int(stock)} {unit_label(product)}"
    return "\u2705 Sotuvda bor"


def product_card(product) -> str:
    """Mahsulot kartochkasi matni: nomi, narxi va katalog ma'lumotlari."""
    lines = [f"<b>{product.title}</b>", price_line(product),
             stock_line(product)]
    if getattr(product, "weight", ""):
        lines.append(f"\u2696 {product.weight}")
    if getattr(product, "diameter", ""):
        lines.append(f"\u2300 {product.diameter}")
    if getattr(product, "composition", ""):
        lines.append(f"\n<b>Tarkibi:</b> {product.composition}")
    if getattr(product, "storage", ""):
        lines.append(f"<b>Saqlash:</b> {product.storage}")
    return "\n".join(lines)


def out_of_stock(stock: int) -> str:
    """Savatga qo'shishda ombor yetmaganida chiqadigan ogohlantirish."""
    if stock <= 0:
        return "Kechirasiz, bu mahsulot hozircha tugagan."
    return f"Omborda faqat {stock} ta qoldi."


SEARCH_ASK = "Mahsulot nomini yozing (masalan: salyami, sosiska):"
SEARCH_TOO_SHORT = "Kamida 2 ta harf yozing."
NOTHING_HERE = "Bu yerda hozircha mahsulot yo'q."


def search_empty(query: str) -> str:
    return (f"\u00ab{query}\u00bb bo'yicha hech narsa topilmadi.\n"
            "Boshqacha yozib ko'ring yoki katalogdan tanlang.")


def search_found(query: str, count: int) -> str:
    return f"\u00ab{query}\u00bb bo'yicha {count} ta mahsulot topildi:"


BTN_REORDER = "🔁 Yana buyurtma qilish"
NO_ORDERS = "Sizda hali buyurtma yo'q. Katalogdan tanlashni boshlang."
REORDER_EMPTY = "Bu buyurtmada mahsulot qolmagan."

ORDER_STATUS_LABELS = {
    "NEW": "🆕 Yangi",
    "CONFIRMED": "✅ Tasdiqlangan",
    "PACKING": "📦 Yig'ilmoqda",
    "ON_WAY": "🚚 Yo'lda",
    "DELIVERED": "🏁 Yetkazildi",
    "CANCELLED": "❌ Bekor qilindi",
}


def order_history_card(order, lines) -> str:
    """Buyurtmalar tarixidagi bitta karta."""
    status = ORDER_STATUS_LABELS.get(order.status, order.status)
    when = order.created_at.strftime("%d.%m.%Y %H:%M") if order.created_at else ""
    out = [f"<b>{order.order_number}</b> · {status}", when]
    for line in lines:
        title = line.parent.title if line.parent else "(o'chirilgan mahsulot)"
        out.append(f"  • {title} × {line.quantity}")
    out.append(f"<b>Jami:</b> {money(order.total_price)}")
    if not order.is_paid:
        out.append("To'lov: kutilmoqda")
    return "\n".join(x for x in out if x)


def reorder_result(added: int, skipped: list) -> str:
    if not added:
        return "Afsuski, bu buyurtmadagi mahsulotlar hozir omborda yo'q."
    text = f"✅ {added} ta mahsulot savatga qo'shildi."
    if skipped:
        text += "\n\nOmborda yetmagani uchun qo'shilmadi:\n" + \
                "\n".join(f"  • {t}" for t in skipped)
    return text
