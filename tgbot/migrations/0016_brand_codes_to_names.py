"""Brend endi erkin matn — eski `choices` kodlarini nomga aylantiradi.

Diler mebel va maishiy texnika bilan ham ishlagani uchun brendlar ro'yxati
qattiq yozilmaydi. Eski qatorlarda kod (`AZIZON`) turibdi, panelda esa
`get_brand_display()` o'rniga endi maydonning o'zi ko'rsatiladi — shuning
uchun qiymatlarni bir marta o'qiladigan holatga keltiramiz.
"""
from django.db import migrations

RENAMES = {
    "AZIZON": "Azizon",
    "AFSONA": "Afsona",
}


def codes_to_names(apps, schema_editor):
    Product = apps.get_model("tgbot", "Product")
    for code, name in RENAMES.items():
        Product.objects.filter(brand=code).update(brand=name)


def names_to_codes(apps, schema_editor):
    Product = apps.get_model("tgbot", "Product")
    for code, name in RENAMES.items():
        Product.objects.filter(brand=name).update(brand=code)


class Migration(migrations.Migration):

    dependencies = [
        ("tgbot", "0015_orders_customer_name_orders_delivery_fee_and_more"),
    ]

    operations = [
        migrations.RunPython(codes_to_names, names_to_codes),
    ]
