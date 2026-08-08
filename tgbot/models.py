from django.db import models


class TimeModel(models.Model):
    created_at = models.DateTimeField("Yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan", auto_now=True)

    class Meta:
        abstract = True


class Category(models.Model):
    name = models.CharField("Nomi", max_length=200, db_index=True)
    tg_name = models.CharField("Botdagi nomi", max_length=200, blank=True)
    description = models.TextField("Tavsif", blank=True)
    slug = models.SlugField(max_length=160, unique=True)
    position = models.PositiveIntegerField("Tartib", default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ("position", "name")


class Subcategory(models.Model):
    name = models.CharField("Nomi", max_length=200, db_index=True)
    tg_name = models.CharField("Botdagi nomi", max_length=200, blank=True)
    description = models.TextField("Tavsif", blank=True)
    slug = models.SlugField(max_length=160, unique=True)
    category = models.ForeignKey(
        Category, verbose_name="Kategoriya",
        related_name="subcategories", on_delete=models.PROTECT,
    )
    position = models.PositiveIntegerField("Tartib", default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Subkategoriya"
        verbose_name_plural = "Subkategoriyalar"
        ordering = ("position", "name")


class Product(models.Model):
    BRAND_CHOICES = [
        ("AZIZON", "Azizon"),
        ("AFSONA", "Afsona"),
    ]

    title = models.CharField("Nomi", max_length=150, db_index=True)
    description = models.TextField("Tavsif", blank=True)
    price = models.DecimalField("Narxi (so'm)", max_digits=12, decimal_places=2,
                                default=0)
    available = models.BooleanField("Sotuvda", default=True)
    slug = models.SlugField(max_length=160, db_index=True)
    image = models.ImageField("Rasm", upload_to="products", blank=True)
    # Telegram file_id of `image`, filled in by the sync_photos command. Inline
    # query results can only reference already-uploaded media, so the bot needs
    # this cached rather than uploading the file mid-query.
    image_file_id = models.CharField(max_length=200, db_index=True, blank=True)
    subcategory = models.ForeignKey(
        Subcategory, verbose_name="Subkategoriya",
        related_name="products", on_delete=models.PROTECT,
    )

    # --- catalogue attributes, straight from the Azizon 2025 PDF ---
    brand = models.CharField("Brend", max_length=16, choices=BRAND_CHOICES,
                             default="AZIZON")
    kind = models.CharField("Turi", max_length=120, blank=True,
                            help_text="masalan: yarim dudlangan kolbasa")
    composition = models.TextField("Tarkibi", blank=True)
    flavour = models.TextField("Ta'm yo'nalishi", blank=True)
    storage = models.TextField("Saqlash sharoiti", blank=True)
    diameter = models.CharField("Diametri", max_length=40, blank=True)
    weight = models.CharField("Og'irligi", max_length=40, blank=True)
    is_new = models.BooleanField("Yangi mahsulot", default=False)
    position = models.PositiveIntegerField("Tartib", default=0)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ("position", "title")


class TgUser(TimeModel):
    # Telegram account ids passed 2^31 in 2024, so this must stay 64-bit.
    user_id = models.BigIntegerField("Telegram ID", db_index=True, unique=True)
    name = models.CharField("Ismi", max_length=100, blank=True)
    username = models.CharField("Username", max_length=64, blank=True)
    phone = models.CharField("Telefon", max_length=32, blank=True)
    is_blocked = models.BooleanField("Bloklangan", default=False)

    def __str__(self):
        return self.name or str(self.user_id)

    class Meta:
        verbose_name = "Mijoz"
        verbose_name_plural = "Mijozlar"
        ordering = ("-created_at",)


class Orders(TimeModel):
    NEW = "NEW"
    CONFIRMED = "CONFIRMED"
    PACKING = "PACKING"
    ON_WAY = "ON_WAY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    STATUS_CHOICES = [
        (NEW, "Yangi"),
        (CONFIRMED, "Tasdiqlangan"),
        (PACKING, "Yig'ilmoqda"),
        (ON_WAY, "Yo'lda"),
        (DELIVERED, "Yetkazildi"),
        (CANCELLED, "Bekor qilindi"),
    ]

    CASH = "CASH"
    CLICK = "CLICK"
    TRANSFER = "TRANSFER"
    PAYMENT_CHOICES = [
        (CASH, "Naqd"),
        (CLICK, "Click"),
        (TRANSFER, "O'tkazma"),
    ]

    is_paid = models.BooleanField("To'langan", default=False)
    tg_user = models.ForeignKey(TgUser, verbose_name="Mijoz",
                                related_name="orders", on_delete=models.PROTECT)
    order_number = models.CharField("Buyurtma raqami", max_length=25,
                                    db_index=True, unique=True)
    total_price = models.DecimalField("Jami summa", max_digits=12,
                                      decimal_places=2, default=0)
    status = models.CharField("Holati", max_length=16, choices=STATUS_CHOICES,
                              default=NEW, db_index=True)
    payment_method = models.CharField("To'lov turi", max_length=16,
                                      choices=PAYMENT_CHOICES, default=CASH)
    phone = models.CharField("Telefon", max_length=32, blank=True)
    address = models.TextField("Yetkazish manzili", blank=True)
    comment = models.TextField("Izoh", blank=True)
    courier = models.ForeignKey(
        "auth.User", verbose_name="Kuryer", null=True, blank=True,
        related_name="deliveries", on_delete=models.SET_NULL,
        limit_choices_to={"groups__name": "Kuryer"},
    )
    operator = models.ForeignKey(
        "auth.User", verbose_name="Qabul qilgan operator", null=True, blank=True,
        related_name="taken_orders", on_delete=models.SET_NULL,
    )
    delivered_at = models.DateTimeField("Yetkazilgan vaqt", null=True, blank=True)

    def __str__(self):
        return self.order_number

    def recalc_total(self):
        """Jami summani qatorlardan qayta hisoblaydi.

        Operator buyurtmani admin panelda qatorlab yig'sa, total_price o'zi
        yangilanmaydi va kassir noto'g'ri summa oladi. Qator bo'lmasa qo'lda
        kiritilgan summa saqlanadi — nolga tushirib yubormaslik uchun.
        """
        lines = self.order_product.all()
        if not lines:
            return self.total_price
        total = sum(line.quantity * line.single_price for line in lines)
        if total != self.total_price:
            # save() emas: save_related ichida chaqiriladi, qayta signal
            # va rekursiyani chaqirmasligi kerak.
            Orders.objects.filter(pk=self.pk).update(total_price=total)
            self.total_price = total
        return total

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ("-created_at",)


class OrderProduct(TimeModel):
    order = models.ForeignKey(Orders, verbose_name="Buyurtma",
                              related_name="order_product",
                              on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name="Mahsulot",
                                related_name="order_product",
                                on_delete=models.PROTECT)
    quantity = models.IntegerField("Soni", default=0)
    single_price = models.DecimalField("Dona narxi", max_digits=12,
                                       decimal_places=2)

    def __str__(self):
        return f"{self.product} x{self.quantity}"

    @property
    def line_total(self):
        return self.single_price * self.quantity

    class Meta:
        verbose_name = "Buyurtma mahsuloti"
        verbose_name_plural = "Buyurtma mahsulotlari"


class UserAddresses(TimeModel):
    user = models.ForeignKey(TgUser, verbose_name="Mijoz",
                             on_delete=models.CASCADE)
    address = models.TextField("Yetkazish manzili", max_length=150)

    def __str__(self):
        return self.address

    class Meta:
        verbose_name = "Manzil"
        verbose_name_plural = "Manzillar"
