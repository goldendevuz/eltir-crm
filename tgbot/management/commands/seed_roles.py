# -*- coding: utf-8 -*-
"""Create the three staff roles and grant each the permissions it needs.

Safe to re-run: permissions are reset to the definition below every time,
so this doubles as a way to repair a role someone edited by hand.

    python manage.py seed_roles
    python manage.py seed_roles --demo-users   # also create login accounts
"""
from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand
from django.db import transaction

OPERATOR = "Call operator"
COURIER = "Kuryer"

# (app_label, model, [codename suffixes])
OPERATOR_PERMS = [
    ("tgbot", "orders", ["add", "change", "view"]),
    ("tgbot", "orderproduct", ["add", "change", "delete", "view"]),
    ("tgbot", "tguser", ["change", "view"]),
    ("tgbot", "useraddresses", ["add", "change", "delete", "view"]),
    # Catalogue is reference-only for an operator; ProductAdmin also blocks
    # writes, this keeps the two in agreement.
    ("tgbot", "product", ["view"]),
    ("tgbot", "category", ["view"]),
    ("tgbot", "subcategory", ["view"]),
]

COURIER_PERMS = [
    # Couriers only ever move their own orders along; OrdersAdmin narrows the
    # queryset and the editable field set on top of this.
    ("tgbot", "orders", ["view", "change"]),
]

DEMO_USERS = [
    ("operator", OPERATOR, "Operator", "Azizon"),
    ("kuryer", COURIER, "Kuryer", "Azizon"),
]


class Command(BaseCommand):
    help = "Rollarni (Call operator, Kuryer) va ruxsatlarni yaratadi"

    def add_arguments(self, parser):
        parser.add_argument("--demo-users", action="store_true",
                            help="Har bir rol uchun sinov akkaunti yaratish")
        parser.add_argument("--password", default="azizon2025",
                            help="Sinov akkauntlari uchun parol")

    def _perms(self, spec):
        found = []
        for app_label, model, actions in spec:
            for action in actions:
                codename = f"{action}_{model}"
                try:
                    found.append(Permission.objects.get(
                        content_type__app_label=app_label,
                        content_type__model=model,
                        codename=codename,
                    ))
                except Permission.DoesNotExist:
                    self.stderr.write(f"  ! topilmadi: {app_label}.{codename}")
        return found

    @transaction.atomic
    def handle(self, *args, **options):
        for name, spec in ((OPERATOR, OPERATOR_PERMS), (COURIER, COURIER_PERMS)):
            group, made = Group.objects.get_or_create(name=name)
            perms = self._perms(spec)
            group.permissions.set(perms)
            verb = "yaratildi" if made else "yangilandi"
            self.stdout.write(self.style.SUCCESS(
                f"{name}: {verb}, {len(perms)} ta ruxsat"))

        if options["demo_users"]:
            password = options["password"]
            for username, group_name, first, last in DEMO_USERS:
                user, made = User.objects.get_or_create(
                    username=username,
                    defaults={"first_name": first, "last_name": last},
                )
                # is_staff is what lets them reach /admin/ at all.
                user.is_staff = True
                user.set_password(password)
                user.save()
                user.groups.set([Group.objects.get(name=group_name)])
                verb = "yaratildi" if made else "paroli yangilandi"
                self.stdout.write(self.style.SUCCESS(
                    f"  {username} ({group_name}) {verb} — parol: {password}"))
