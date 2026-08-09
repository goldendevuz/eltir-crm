"""Admin panel for the Qo'qon dealership, themed with django-unfold.

Three roles share this panel, so most ModelAdmins narrow what they expose
based on the caller's group — see `RoleScopedAdmin`:

* superadmin      — full access (Django superuser)
* Call operator   — takes orders by phone, edits them, marks them paid
                    (acts as cashier); read-only on the catalogue
* Kuryer          — sees only the orders assigned to them, and may only
                    move them along the delivery statuses
"""
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.utils import timezone
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (ChoicesDropdownFilter,
                                          RangeDateFilter)

from tgbot import models

COURIER_GROUP = "Kuryer"
OPERATOR_GROUP = "Call operator"

STATUS_COLORS = {
    models.Orders.NEW: ("#92400e", "#fef3c7"),
    models.Orders.CONFIRMED: ("#1e40af", "#dbeafe"),
    models.Orders.PACKING: ("#3730a3", "#e0e7ff"),
    models.Orders.ON_WAY: ("#5b21b6", "#ede9fe"),
    models.Orders.DELIVERED: ("#166534", "#dcfce7"),
    models.Orders.CANCELLED: ("#991b1b", "#fee2e2"),
}

admin.site.site_title = "Azizon Qo'qon"
admin.site.site_header = "Azizon Qo'qon"
admin.site.index_title = "Boshqaruv paneli"


def _pill(text, colors=("#374151", "#f3f4f6")):
    fg, bg = colors
    return format_html(
        '<span style="background:{};color:{};padding:3px 10px;'
        'border-radius:999px;font-size:11px;font-weight:600;'
        'white-space:nowrap;">{}</span>', bg, fg, text,
    )


def _in_group(request, name):
    return request.user.groups.filter(name=name).exists()


def is_courier(request):
    return not request.user.is_superuser and _in_group(request, COURIER_GROUP)


def is_operator(request):
    return not request.user.is_superuser and _in_group(request, OPERATOR_GROUP)


class RoleScopedAdmin(ModelAdmin):
    """Hides a model from couriers unless the subclass opts back in."""

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        if is_courier(request):
            return False
        return super().has_module_permission(request)


class ReadOnlyForOperatorAdmin(RoleScopedAdmin):
    """Catalogue models: operators may look, only superadmin may edit."""

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ------------------------------------------------------------------ katalog


class SubcategoryInline(TabularInline):
    model = models.Subcategory
    extra = 0
    fields = ("name", "tg_name", "slug", "position")
    prepopulated_fields = {"slug": ("name",)}
    tab = True


@admin.register(models.Category)
class CategoryAdmin(ReadOnlyForOperatorAdmin):
    list_display = ("name", "tg_name", "subcategory_count", "position")
    list_display_links = ("name",)
    list_editable = ("position",)
    search_fields = ("name", "tg_name")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [SubcategoryInline]

    @admin.display(description="Subkategoriyalar")
    def subcategory_count(self, obj):
        return obj.subcategories.count()


@admin.register(models.Subcategory)
class SubcategoryAdmin(ReadOnlyForOperatorAdmin):
    list_display = ("name", "category", "product_count", "position")
    list_display_links = ("name",)
    list_editable = ("position",)
    list_filter = ("category",)
    search_fields = ("name", "tg_name")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category",)

    @admin.display(description="Mahsulotlar")
    def product_count(self, obj):
        return obj.products.count()


@admin.register(models.Product)
class ProductAdmin(ReadOnlyForOperatorAdmin):
    # price is list-editable on purpose: the catalogue was imported without
    # prices, so filling them in is a bulk job done straight from this table.
    list_display = ("thumb", "title", "subcategory", "price_display", "price",
                    "unit", "stock_pill", "stock", "available", "badges")
    list_display_links = ("title",)
    # price/stock jadvaldan turib tahrirlanadi: katalog narxsiz import
    # qilingan va qoldiqni har kuni yangilab turish kerak.
    list_editable = ("price", "stock", "unit", "available")
    list_filter = ("subcategory__category", "subcategory", "brand",
                   "available", "is_new")
    search_fields = ("title", "slug", "brand", "model_code", "composition")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("subcategory",)
    readonly_fields = ("preview", "image_file_id")
    list_per_page = 50
    # Oziq-ovqat va texnika xususiyatlari alohida yig'ilgan: bitta mahsulotga
    # ikkalasi ham kerak bo'lmaydi, shuning uchun ikkalasi ham yopiq turadi.
    fieldsets = (
        ("Asosiy", {
            "fields": ("title", "slug", "subcategory", "brand", "kind",
                       "available", "is_new", "position"),
        }),
        ("Narx va ombor", {
            "fields": ("price", "old_price", "unit", "stock"),
        }),
        ("Rasm", {"fields": ("image", "preview", "image_file_id")}),
        ("Mebel va maishiy texnika", {
            "fields": ("model_code", "dimensions", "material", "power",
                       "warranty_months", "country"),
            "classes": ("collapse",),
        }),
        ("Oziq-ovqat xususiyatlari", {
            "fields": ("description", "composition", "flavour", "storage",
                       "diameter", "weight"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="")
    def thumb(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" style="height:42px;width:42px;object-fit:contain;'
            'border-radius:6px;background:#fff;" />', obj.image.url,
        )

    @admin.display(description="Ko'rinishi")
    def preview(self, obj):
        if not obj.image:
            return "Rasm yuklanmagan"
        return format_html(
            '<img src="{}" style="max-height:260px;border-radius:10px;'
            'background:#fff;" />', obj.image.url,
        )

    @admin.display(description="Narxi", ordering="price")
    def price_display(self, obj):
        if obj.has_discount:
            return format_html(
                '<span style="white-space:nowrap;">{} '
                '<s style="opacity:.55;">{}</s></span>',
                f"{int(obj.price):,}".replace(",", " "),
                f"{int(obj.old_price):,}".replace(",", " "),
            )
        return f"{int(obj.price):,}".replace(",", " ")

    @admin.display(description="Ombor", ordering="stock")
    def stock_pill(self, obj):
        """Qoldiq holatini rangli ko'rsatadi — tugayotganini darrov ko'rish uchun."""
        stock = int(obj.stock or 0)
        if stock <= 0:
            return _pill("tugagan", ("#991b1b", "#fee2e2"))
        if stock <= 20:
            return _pill(f"oz: {stock}", ("#92400e", "#fef3c7"))
        return _pill(str(stock), ("#166534", "#dcfce7"))

    @admin.display(description="Belgilar")
    def badges(self, obj):
        out = []
        if obj.brand:
            out.append(_pill(obj.brand, ("#7a1f19", "#fee2e2")))
        if obj.is_new:
            out.append(_pill("YANGI", ("#166534", "#dcfce7")))
        if obj.price == 0:
            out.append(_pill("narx yo'q", ("#92400e", "#fef3c7")))
        if obj.has_discount:
            out.append(_pill("chegirma", ("#1e40af", "#dbeafe")))
        return format_html(" ".join(["{}"] * len(out)), *out)


# --------------------------------------------------------------- buyurtmalar


class OrderProductInline(TabularInline):
    model = models.OrderProduct
    extra = 0
    fields = ("product", "quantity", "single_price", "line_total_display")
    readonly_fields = ("line_total_display",)
    autocomplete_fields = ("product",)
    tab = True

    @admin.display(description="Summa")
    def line_total_display(self, obj):
        if not obj.pk:
            return "—"
        return f"{int(obj.line_total):,}".replace(",", " ") + " so'm"

    def has_add_permission(self, request, obj=None):
        return not is_courier(request)

    def has_change_permission(self, request, obj=None):
        return not is_courier(request)

    def has_delete_permission(self, request, obj=None):
        return not is_courier(request)


@admin.register(models.Orders)
class OrdersAdmin(ModelAdmin):
    list_display = ("order_number", "customer", "source_pill", "status_pill",
                    "delivery_cell", "total_display", "paid_pill", "courier",
                    "created_at")
    list_display_links = ("order_number",)
    list_filter = (("source", ChoicesDropdownFilter),
                   ("status", ChoicesDropdownFilter), "is_paid",
                   ("delivery_type", ChoicesDropdownFilter),
                   ("payment_method", ChoicesDropdownFilter),
                   ("created_at", RangeDateFilter), "courier")
    search_fields = ("order_number", "phone", "customer_name", "tg_user__name",
                     "tg_user__user_id")
    autocomplete_fields = ("tg_user",)
    readonly_fields = ("order_number", "created_at", "updated_at",
                       "delivered_at")
    inlines = [OrderProductInline]
    date_hierarchy = "created_at"
    list_per_page = 40
    actions = ("mark_delivered", "mark_on_way", "mark_paid")

    # Couriers get a stripped form: they may only push the delivery status.
    courier_fields = ("order_number", "status", "phone", "delivery_type",
                      "address", "scheduled_at", "comment", "total_price",
                      "delivery_fee", "delivered_at")

    fieldsets = (
        ("Buyurtma", {
            "fields": ("order_number", "source", "status", "operator"),
        }),
        ("Mijoz", {
            "fields": ("tg_user", "customer_name", "phone"),
            "description": "Do'kon sotuvida Telegram mijozi bo'lmaydi — "
                           "shunda mijoz ismini yozing.",
        }),
        ("Yetkazish", {
            "fields": ("delivery_type", "address", "courier", "scheduled_at",
                       "delivery_fee", "delivered_at"),
        }),
        ("To'lov", {
            "fields": ("total_price", "payment_method", "is_paid"),
        }),
        ("Qo'shimcha", {
            "fields": ("comment", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Mijoz", ordering="customer_name")
    def customer(self, obj):
        return obj.customer_label

    @admin.display(description="Kanal", ordering="source")
    def source_pill(self, obj):
        colors = {
            models.Orders.TELEGRAM: ("#1e40af", "#dbeafe"),
            models.Orders.SHOP: ("#166534", "#dcfce7"),
            models.Orders.PHONE_CALL: ("#92400e", "#fef3c7"),
        }
        return _pill(obj.get_source_display(),
                     colors.get(obj.source, ("#374151", "#f3f4f6")))

    @admin.display(description="Yetkazish")
    def delivery_cell(self, obj):
        """Turi + kuryer narxi bitta ustunda — ro'yxatni kengaytirmaslik uchun."""
        if obj.delivery_type == models.Orders.PICKUP:
            return _pill("olib ketish", ("#374151", "#f3f4f6"))
        if obj.delivery_fee:
            fee = f"{int(obj.delivery_fee):,}".replace(",", " ")
            return _pill(f"yetkazish · {fee}", ("#5b21b6", "#ede9fe"))
        return _pill("yetkazish", ("#5b21b6", "#ede9fe"))

    @admin.display(description="Holati", ordering="status")
    def status_pill(self, obj):
        return _pill(obj.get_status_display(),
                     STATUS_COLORS.get(obj.status, ("#374151", "#f3f4f6")))

    @admin.display(description="To'lov", ordering="is_paid")
    def paid_pill(self, obj):
        if obj.is_paid:
            return _pill("to'langan", ("#166534", "#dcfce7"))
        return _pill("kutilmoqda", ("#92400e", "#fef3c7"))

    @admin.display(description="Summa", ordering="total_price")
    def total_display(self, obj):
        return f"{int(obj.total_price):,}".replace(",", " ") + " so'm"

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("tg_user", "courier")
        if is_courier(request):
            return qs.filter(courier=request.user)
        return qs

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if is_courier(request):
            # Everything except `status` — the one thing a courier changes.
            ro += [f for f in self.courier_fields if f != "status"]
        return tuple(dict.fromkeys(ro))

    def get_fieldsets(self, request, obj=None):
        # `fieldsets` o'rnatilgani uchun Django get_fields() ni chaqirmaydi —
        # kuryerning qisqartirilgan formasi shu yerdan berilishi shart.
        if is_courier(request):
            return ((None, {"fields": self.courier_fields}),)
        if obj is None:
            # Yangi buyurtmada raqam hali yo'q, yetkazilgan vaqt ham.
            return tuple(
                (name, {**opts, "fields": tuple(
                    f for f in opts["fields"]
                    if f not in ("order_number", "delivered_at",
                                 "created_at", "updated_at")
                )})
                for name, opts in self.fieldsets
            )
        return super().get_fieldsets(request, obj)

    def has_add_permission(self, request):
        return not is_courier(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        if not change and not obj.operator_id:
            obj.operator = request.user
        if obj.status == models.Orders.DELIVERED and not obj.delivered_at:
            obj.delivered_at = timezone.now()
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        # Qatorlar shu yerda saqlanadi, shuning uchun jamini save_model emas,
        # aynan shu yerdan qayta hisoblaymiz.
        super().save_related(request, form, formsets, change)
        form.instance.recalc_total()

    @admin.action(description="Yetkazildi deb belgilash")
    def mark_delivered(self, request, queryset):
        n = queryset.update(status=models.Orders.DELIVERED,
                            delivered_at=timezone.now())
        self.message_user(request, f"{n} ta buyurtma yetkazildi deb belgilandi")

    @admin.action(description="Yo'lda deb belgilash")
    def mark_on_way(self, request, queryset):
        n = queryset.exclude(status=models.Orders.DELIVERED).update(
            status=models.Orders.ON_WAY)
        self.message_user(request, f"{n} ta buyurtma yo'lda deb belgilandi")

    @admin.action(description="To'landi deb belgilash")
    def mark_paid(self, request, queryset):
        if is_courier(request):
            self.message_user(request, "Sizda bu amal uchun ruxsat yo'q",
                              level="error")
            return
        n = queryset.update(is_paid=True)
        self.message_user(request, f"{n} ta buyurtma to'landi deb belgilandi")


@admin.register(models.OrderProduct)
class OrderProductAdmin(RoleScopedAdmin):
    list_display = ("order", "product", "quantity", "single_price")
    list_display_links = ("order", "product")
    search_fields = ("order__order_number", "product__title")
    autocomplete_fields = ("order", "product")

    # Qator shu ekrandan alohida o'zgartirilsa ham buyurtma jami summasi
    # eskirib qolmasligi kerak.
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.order.recalc_total()

    def delete_model(self, request, obj):
        order = obj.order
        super().delete_model(request, obj)
        order.recalc_total()

    def delete_queryset(self, request, queryset):
        orders = {line.order for line in queryset.select_related("order")}
        super().delete_queryset(request, queryset)
        for order in orders:
            order.recalc_total()


# -------------------------------------------------------------------- mijoz


class UserAddressInline(TabularInline):
    model = models.UserAddresses
    extra = 0
    fields = ("address",)
    tab = True


@admin.register(models.TgUser)
class TgUserAdmin(RoleScopedAdmin):
    list_display = ("name", "user_id", "username", "phone", "order_count",
                    "is_blocked", "created_at")
    list_display_links = ("name", "user_id")
    list_filter = ("is_blocked", ("created_at", RangeDateFilter))
    search_fields = ("name", "username", "phone", "user_id")
    readonly_fields = ("user_id", "created_at", "updated_at")
    inlines = [UserAddressInline]
    date_hierarchy = "created_at"

    @admin.display(description="Buyurtmalar")
    def order_count(self, obj):
        return obj.orders.count()


@admin.register(models.UserAddresses)
class UserAddressesAdmin(RoleScopedAdmin):
    list_display = ("user", "address")
    list_display_links = ("user", "address")
    search_fields = ("address", "user__name")
    autocomplete_fields = ("user",)


# ------------------------------------------------------------------ xodimlar
# Re-register Django's auth models so they pick up the Unfold styling.

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class StaffAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ("username", "full_name", "role_pills", "is_active",
                    "last_login")

    @admin.display(description="Ism")
    def full_name(self, obj):
        return obj.get_full_name() or "—"

    @admin.display(description="Rol")
    def role_pills(self, obj):
        if obj.is_superuser:
            return _pill("Superadmin", ("#7a1f19", "#fee2e2"))
        names = list(obj.groups.values_list("name", flat=True))
        if not names:
            return "—"
        return format_html(" ".join(["{}"] * len(names)),
                           *[_pill(n) for n in names])

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(Group)
class RoleAdmin(BaseGroupAdmin, ModelAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser
