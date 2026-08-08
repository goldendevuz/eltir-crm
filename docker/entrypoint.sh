#!/usr/bin/env bash
# Konteyner ishga tushganda bajariladigan tayyorgarlik.
#
# Ilgari konteyner to'g'ridan-to'g'ri runserver va start_bot.py ga o'tardi.
# Yangi serverda baza bo'sh bo'ladi va bot har bir xabarda
# `relation "tgbot_tguser" does not exist` bilan yiqilardi — chunki hech kim
# qo'lda `migrate` ishlatmagan. Endi migratsiya har safar avtomatik
# qo'llanadi: allaqachon qo'llangan bo'lsa hech narsa o'zgarmaydi.
set -euo pipefail

echo "→ Migratsiyalar qo'llanmoqda…"
python manage.py migrate --noinput

# DEBUG=0 da WhiteNoise manifest talab qiladi: staticfiles yig'ilmagan bo'lsa
# admin panel CSS'siz ochiladi.
if [ "${DEBUG:-1}" != "1" ]; then
    echo "→ Statik fayllar yig'ilmoqda…"
    python manage.py collectstatic --noinput >/dev/null
fi

# Rollar (Call operator, Kuryer) va ularning ruxsatlari. get_or_create
# ishlatgani uchun qayta ishga tushirish xavfsiz.
echo "→ Rollar tekshirilmoqda…"
python manage.py seed_roles

# Bot alohida nazorat ostida ishlaydi. Uni Django bilan bir qatorga qo'yib
# "biri tugasa ikkalasi ham tugasin" desak, BOT_TOKEN bekor qilinganda
# (Unauthorized) konteyner cheksiz qayta ishga tushib, admin panel ham
# ishlamay qoladi. Do'kon uchun bu qabul qilib bo'lmaydi: buyurtmalarni
# ko'rish bot ishlashidan muhimroq.
(
    while true; do
        echo "→ Bot ishga tushmoqda…"
        python start_bot.py || echo "⚠ Bot to'xtadi. 15 soniyadan keyin qayta urinaman."
        sleep 15
    done
) &

echo "→ Django ishga tushmoqda…"
exec python manage.py runserver 0.0.0.0:8000
