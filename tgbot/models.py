from django.db import IntegrityError, models, transaction
from django.utils import timezone


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
    DONA = "DONA"
    KG = "KG"
    UNIT_CHOICES = [(DONA, "dona"), (KG, "kg")]

    title = models.CharField("Nomi", max_length=150, db_index=True)
    description = models.TextField("Tavsif", blank=True)
    price = models.DecimalField("Narxi (so'm)", max_digits=12, decimal_places=2,
                                default=0)
    # Chegirma ko'rsatish uchun: to'ldirilgan va price'dan katta bo'lsa,
    # mijozga eski narx chizilgan holda ko'rsatiladi.
    old_price = models.DecimalField("Eski narxi (so'm)", max_digits=12,
                                    decimal_places=2, default=0,
                                    help_text="Chegirma bo'lmasa 0 qoldiring")
    unit = models.CharField("O'lchov birligi", max_length=8,
                            choices=UNIT_CHOICES, default=DONA)
    stock = models.DecimalField("Ombordagi miqdor", max_digits=10,
                                decimal_places=2, default=0)
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

    # Diler bir nechta ishlab chiqaruvchi bilan ishlaydi (mebel, maishiy
    # texnika, oziq-ovqat), shuning uchun brend ro'yxati qattiq yozilmaydi.
    brand = models.CharField("Brend", max_length=64, blank=True, default="")
    kind = models.CharField("Turi", max_length=120, blank=True,
                            help_text="masalan: yarim dudlangan kolbasa")
    is_new = models.BooleanField("Yangi mahsulot", default=False)
    position = models.PositiveIntegerField("Tartib", default=0)

    # --- oziq-ovqat xususiyatlari ---
    composition = models.TextField("Tarkibi", blank=True)
    flavour = models.TextField("Ta'm yo'nalishi", blank=True)
    storage = models.TextField("Saqlash sharoiti", blank=True)
    diameter = models.CharField("Diametri", max_length=40, blank=True)
    weight = models.CharField("Og'irligi", max_length=40, blank=True)

    # --- mebel va maishiy texnika xususiyatlari ---
    model_code = models.CharField("Model raqami", max_length=64, blank=True,
                                  default="")
    dimensions = models.CharField("O'lchami", max_length=80, blank=True,
                                  default="",
                                  help_text="masalan: 200x90x75 sm")
    material = models.CharField("Material", max_length=120, blank=True,
                                default="",
                                help_text="masalan: MDF, teri, metall")
    power = models.CharField("Quvvati", max_length=40, blank=True, default="",
                             help_text="masalan: 1800 Vt")
    warranty_months = models.PositiveIntegerField("Kafolat (oy)", default=0)
    country = models.CharField("Ishlab chiqarilgan davlat", max_length=60,
                               blank=True, default="")

    def __str__(self):
        return self.title

    @property
    def has_discount(self):
        return self.old_price > 0 and self.old_price > self.price

    @property
    def in_stock(self):
        """Sotuvda va omborda qolgan bo'lsa.

        Bot savatga qo'shishdan oldin shuni tekshiradi — aks holda mijoz
        omborda yo'q mahsulotni buyurtma qilib qo'yadi.
        """
        return self.available and self.stock > 0

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

    TELEGRAM = "TELEGRAM"
    SHOP = "SHOP"
    PHONE_CALL = "PHONE"
    SOURCE_CHOICES = [
        (TELEGRAM, "Telegram bot"),
        (SHOP, "Do'kondan"),
        (PHONE_CALL, "Telefon orqali"),
    ]

    DELIVERY = "DELIVERY"
    PICKUP = "PICKUP"
    DELIVERY_CHOICES = [
        (DELIVERY, "Yetkazib berish"),
        (PICKUP, "Olib ketish"),
    ]

    is_paid = models.BooleanField("To'langan", default=False)
    # Do'konga kelgan mijozda Telegram akkaunti bo'lmaydi, shuning uchun
    # bo'sh qolishi mumkin — o'shanda `customer_name` to'ldiriladi.
    tg_user = models.ForeignKey(TgUser, verbose_name="Mijoz",
                                related_name="orders", on_delete=models.PROTECT,
                                null=True, blank=True)
    customer_name = models.CharField("Mijoz ismi", max_length=120, blank=True,
                                     default="",
                                     help_text="Telegramsiz mijoz uchun")
    # Panelda ochilgan buyurtma odatda do'kon sotuvi, shuning uchun default
    # SHOP. Bot esa `quick_commands.create_order` da TELEGRAM'ni aniq beradi.
    source = models.CharField("Sotuv kanali", max_length=16,
                              choices=SOURCE_CHOICES, default=SHOP,
                              db_index=True)
    order_number = models.CharField("Buyurtma raqami", max_length=25,
                                    db_index=True, unique=True)
    total_price = models.DecimalField("Jami summa", max_digits=12,
                                      decimal_places=2, default=0)
    status = models.CharField("Holati", max_length=16, choices=STATUS_CHOICES,
                              default=NEW, db_index=True)
    payment_method = models.CharField("To'lov turi", max_length=16,
                                      choices=PAYMENT_CHOICES, default=CASH)
    phone = models.CharField("Telefon", max_length=32, blank=True)
    delivery_type = models.CharField("Yetkazish turi", max_length=16,
                                     choices=DELIVERY_CHOICES, default=DELIVERY)
    delivery_fee = models.DecimalField("Yetkazish narxi", max_digits=12,
                                       decimal_places=2, default=0)
    scheduled_at = models.DateTimeField("Rejalashtirilgan vaqt", null=True,
                                        blank=True,
                                        help_text="Mijoz so'ragan yetkazish vaqti")
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

    @property
    def customer_label(self):
        """Telegram mijozi ham, do'kon mijozi ham bir xil ko'rsatiladi."""
        if self.tg_user_id:
            return str(self.tg_user)
        return self.customer_name or "Nomsiz mijoz"

    @property
    def grand_total(self):
        """Mahsulotlar jami + yetkazish narxi — kassir oladigan summa."""
        return self.total_price + self.delivery_fee

    # Panelda ochilgan buyurtmalar shu prefiks bilan raqamlanadi. Bot o'z
    # hisoblagichini `db.txt` pickle faylida yuritadi va paneldagi qatorlarni
    # ko'rmaydi, shuning uchun ikkala oqim bir xil formatda raqam bersa
    # to'qnashadi. Alohida prefiks buni butunlay yo'q qiladi.
    PANEL_PREFIX = "P"

    @classmethod
    def generate_order_number(cls):
        """Shu kunning oxirgi panel raqamidan davom ettiradi."""
        today = timezone.localtime().strftime("%d-%m-%Y")
        prefix = f"{cls.PANEL_PREFIX}-{today}-"
        last = (cls.objects
                .filter(order_number__startswith=prefix)
                .order_by("-id")
                .values_list("order_number", flat=True)
                .first())
        seq = 1
        if last:
            tail = last.rsplit("-", 1)[-1]
            if tail.isdigit():
                seq = int(tail) + 1
        return f"{prefix}{seq}"

    def save(self, *args, **kwargs):
        # Ikki operator bir vaqtda saqlasa bir xil raqam chiqishi mumkin;
        # unique cheklovi ushlaydi, biz keyingi raqam bilan qayta urinamiz.
        if not self.order_number:
            for _ in range(5):
                self.order_number = self.generate_order_number()
                try:
                    with transaction.atomic():
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    continue
        return super().save(*args, **kwargs)

    def clean(self):
        """Buyurtma kimniki ekani nomamlum qolmasligi kerak.

        Bot doim `tg_user` beradi; panelda ochilgan do'kon sotuvida esa
        hech bo'lmasa mijoz ismi yozilishi shart.
        """
        from django.core.exceptions import ValidationError

        if not self.tg_user_id and not self.customer_name.strip():
            raise ValidationError({
                "customer_name": "Telegram mijozi tanlanmagan bo'lsa, "
                                 "mijoz ismini yozing.",
            })

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
