"""KPI cards + charts for the Unfold admin index.

Everything here is scoped by role: a courier opening the panel should see
their own deliveries, not shop-wide revenue.
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from tgbot.models import OrderProduct, Orders, Product, TgUser

COURIER_GROUP = "Kuryer"
OPERATOR_GROUP = "Call operator"


def _money(value):
    """Format so'm with thin spaces: 1234567 -> '1 234 567 so'm'."""
    return f"{int(value or 0):,}".replace(",", " ") + " so'm"


def _in_group(user, name):
    return user.groups.filter(name=name).exists()


def _delta(current, previous):
    """Percent change vs the previous period, or None when there's no base."""
    if not previous:
        return None
    return round((current - previous) / previous * 100, 1)


def _card(title, value, footer="", icon=""):
    return {"title": title, "metric": value, "footer": footer, "icon": icon}


def _bars(rows):
    """Scale (label, value) pairs into bar heights the template can render.

    A flat 0-order week would divide by zero, and a single tall day would
    squash the rest, so the peak always maps to 100%.
    """
    peak = max((v for _, v in rows), default=0)
    return [
        {"label": label, "value": value,
         "height": round(value / peak * 100) if peak else 0}
        for label, value in rows
    ]


def dashboard_callback(request, context):
    now = timezone.localtime()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=6)
    prev_week_start = today - timedelta(days=13)
    user = request.user

    orders = Orders.objects.all()

    # --- courier: a personal view, nothing shop-wide -----------------------
    if not user.is_superuser and _in_group(user, COURIER_GROUP):
        mine = orders.filter(courier=user)
        active = mine.exclude(status__in=[Orders.DELIVERED, Orders.CANCELLED])
        done_today = mine.filter(status=Orders.DELIVERED,
                                 delivered_at__gte=today)
        context.update({
            "cards": [
                _card("Yetkazishim kerak", active.count(),
                      "Hozirgi faol buyurtmalar", "local_shipping"),
                _card("Bugun yetkazildi", done_today.count(),
                      today.strftime("%d.%m.%Y"), "task_alt"),
                _card("Bugungi summa",
                      _money(done_today.aggregate(s=Sum("total_price"))["s"]),
                      "Yetkazilgan buyurtmalar bo'yicha", "payments"),
            ],
            "is_courier": True,
        })
        return context

    # --- superadmin / operator --------------------------------------------
    paid = orders.filter(is_paid=True)
    today_orders = orders.filter(created_at__gte=today)
    week_orders = orders.filter(created_at__gte=week_ago)
    prev_week_orders = orders.filter(created_at__gte=prev_week_start,
                                     created_at__lt=week_ago)

    revenue_today = today_orders.filter(is_paid=True).aggregate(
        s=Sum("total_price"))["s"] or Decimal(0)
    revenue_week = week_orders.filter(is_paid=True).aggregate(
        s=Sum("total_price"))["s"] or Decimal(0)
    revenue_prev = prev_week_orders.filter(is_paid=True).aggregate(
        s=Sum("total_price"))["s"] or Decimal(0)

    pending = orders.filter(status__in=[Orders.NEW, Orders.CONFIRMED,
                                        Orders.PACKING, Orders.ON_WAY])
    week_delta = _delta(week_orders.count(), prev_week_orders.count())
    revenue_delta = _delta(revenue_week, revenue_prev)

    cards = [
        _card("Bugungi buyurtmalar", today_orders.count(),
              f"Kutilmoqda: {pending.count()} ta", "receipt_long"),
        _card("Bugungi tushum", _money(revenue_today),
              "To'langan buyurtmalar", "payments"),
        _card("7 kunlik buyurtma", week_orders.count(),
              _trend(week_delta), "trending_up"),
        _card("7 kunlik tushum", _money(revenue_week),
              _trend(revenue_delta), "savings"),
        _card("Mijozlar", TgUser.objects.count(),
              f"Bu hafta yangi: "
              f"{TgUser.objects.filter(created_at__gte=week_ago).count()}",
              "group"),
        _card("Sotuvdagi mahsulot", Product.objects.filter(available=True).count(),
              f"Narxi kiritilmagan: "
              f"{Product.objects.filter(price=0).count()} ta", "inventory_2"),
    ]

    # Orders per day for the last 7 days, zero-filled so the line has no gaps.
    per_day = {}
    for row in (week_orders
                .annotate(day=TruncDate("created_at"))
                .values("day").annotate(n=Count("id"))):
        per_day[str(row["day"])] = row["n"]
    days = []
    for i in range(7):
        d = (week_ago + timedelta(days=i)).date()
        days.append((d.strftime("%d.%m"), per_day.get(str(d), 0)))

    top_products = (OrderProduct.objects
                    .values("product__title")
                    .annotate(qty=Sum("quantity"),
                              total=Sum(F("quantity") * F("single_price")))
                    .order_by("-qty")[:8])

    status_rows = (orders.values("status")
                   .annotate(n=Count("id")).order_by("-n"))
    status_labels = dict(Orders.STATUS_CHOICES)

    context.update({
        "cards": cards,
        "chart_points": _bars(days),
        "top_products": [
            {"title": r["product__title"], "qty": r["qty"],
             "total": _money(r["total"])}
            for r in top_products
        ],
        "status_rows": [
            {"label": status_labels.get(r["status"], r["status"]),
             "count": r["n"], "code": r["status"]}
            for r in status_rows
        ],
        "recent_orders": (orders.select_related("tg_user")
                          .order_by("-created_at")[:8]),
        "is_courier": False,
    })
    return context


def _trend(delta):
    if delta is None:
        return "Taqqoslash uchun ma'lumot yo'q"
    sign = "+" if delta >= 0 else ""
    return f"O'tgan haftaga nisbatan {sign}{delta}%"
