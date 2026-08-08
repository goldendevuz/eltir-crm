from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")
ADMINS = env.list("ADMINS")
IP = env.str("ip")

PGUSER = env.str("POSTGRES_USER")
PGPASSWORD = env.str("POSTGRES_PASSWORD")
Database = env.str("POSTGRES_DB")

db_host = IP

POSTGRES_URI = f"postgresql://{PGUSER}:{PGPASSWORD}@{db_host}/{Database}"

PROVIDER_TOKEN = env.str("PROVIDER_TOKEN")

# --- do'kon sozlamalari -----------------------------------------------------
# Biz Azizon mahsulotlarini Qo'qonda sotuvchi dilermiz; ishlab chiqaruvchi
# korxonaning o'zi Samarqandda joylashgan va bu bot ularning rasmiy boti emas.
SHOP_NAME = env.str("SHOP_NAME", "") or "Azizon Qo'qon"
SHOP_TAGLINE = env.str("SHOP_TAGLINE", "") or "Rasmiy diler · Qo'qon shahri"
SHOP_PHONE = env.str("SHOP_PHONE", "") or "+998 90 000 00 00"
CURRENCY = "so'm"
# Telegram to'lov API summani eng kichik birlikda (tiyin) qabul qiladi.
CURRENCY_CODE = "UZS"
CURRENCY_MULTIPLIER = 100
DELIVERY_FEE = env.int("DELIVERY_FEE", 0) or 15000

