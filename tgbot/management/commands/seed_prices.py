"""Katalogga taxminiy narx va ombor qoldig'ini qo'yadi.

Azizon katalogi (PDF) narxlarsiz chiqadi — u tarqatuvchilar uchun, narx esa
shartnoma bo'yicha belgilanadi. Do'kon ishga tushguncha bot va panelni
sinash uchun real ko'rinishdagi qiymatlar kerak.

Narxlar tasodifiy emas: 1 kg uchun bazaviy narx mahsulot turiga qarab
olinadi (sosiska arzonroq, delikates qimmatroq) va og'irlikka ko'paytiriladi,
shuning uchun ular o'zaro mantiqiy bo'lib chiqadi.

    python manage.py seed_prices           # bo'sh narxlarni to'ldiradi
    python manage.py seed_prices --force   # mavjudlarini ham qayta yozadi
"""
import random
import re
from decimal import Decimal

from django.core.management.base import BaseCommand

from tgbot.models import Product

MAX_PRICE = Decimal("100000")
MAX_STOCK = Decimal("250")

# 1 kg uchun taxminiy narx (so'm). Kalit mahsulot nomi/turida qidiriladi.
KG_PRICE = {
    "sosiska": 52000, "sardelka": 55000,
    "pishirilgan": 58000, "qaynatilgan": 58000,
    "yarim dudlangan": 72000, "dudlangan": 78000,
    "salyami": 88000, "delikates": 92000, "qazi": 95000,
    "rulet": 85000, "dumba": 80000, "oyoq": 45000,
}
DEFAULT_KG_PRICE = 65000


def _kg_price_for(product):
    haystack = " ".join([
        product.kind or "", product.title or "",
        product.subcategory.tg_name or "",
    ]).lower()
    for key, value in KG_PRICE.items():
        if key in haystack:
            return value
    return DEFAULT_KG_PRICE


def _weight_kg(product):
    """"0.8 kg" -> 0.8. Og'irligi ko'rsatilmagan bo'lsa None."""
    match = re.search(r"([\d.,]+)\s*kg", (product.weight or "").lower())
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def _round_to(value, step=500):
    return Decimal(int(round(float(value) / step)) * step)


class Command(BaseCommand):
    help = "Mahsulotlarga taxminiy narx va ombor qoldig'ini qo'yadi"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true",
            help="Narxi allaqachon kiritilgan mahsulotlarni ham qayta yozadi",
        )

    def handle(self, *args, **options):
        # Takrorlanadigan natija: buyruqni qayta ishlatganda narxlar
        # sakrab ketmasin.
        random.seed(2025)
        force = options["force"]
        updated = skipped = 0

        for product in Product.objects.select_related("subcategory").order_by("id"):
            if product.price > 0 and not force:
                skipped += 1
                continue

            kilograms = _weight_kg(product)
            base = _kg_price_for(product)

            if kilograms:
                # Belgilangan og'irlikdagi batonchа — dona bilan sotiladi.
                product.unit = Product.DONA
                price = _round_to(base * kilograms)
            else:
                # Og'irligi yozilmagan (rulet, tovuq oyoqlari, dumba) —
                # kilo bilan sotiladi.
                product.unit = Product.KG
                price = _round_to(base)

            product.price = min(price, MAX_PRICE)
            product.stock = min(Decimal(random.randint(15, 250)), MAX_STOCK)

            # Har oltinchi mahsulotda chegirma bo'lsin: eski narx 10-20%
            # yuqori qilib ko'rsatiladi.
            if product.id % 6 == 0:
                old = _round_to(float(product.price) * random.uniform(1.10, 1.20))
                product.old_price = min(old, MAX_PRICE) if old > product.price \
                    else Decimal(0)
            else:
                product.old_price = Decimal(0)

            product.save(update_fields=["price", "old_price", "unit", "stock"])
            updated += 1

        self.stdout.write(f"Yangilandi: {updated} ta, o'tkazib yuborildi: {skipped} ta")
        products = list(Product.objects.all())
        if products:
            self.stdout.write(
                f"Narx  : {min(p.price for p in products):,.0f} — "
                f"{max(p.price for p in products):,.0f} so'm")
            self.stdout.write(
                f"Ombor : {min(p.stock for p in products):,.0f} — "
                f"{max(p.stock for p in products):,.0f}")
            self.stdout.write(
                f"Chegirmali: {sum(1 for p in products if p.has_discount)} ta")
