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
