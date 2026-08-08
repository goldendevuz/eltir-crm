# -*- coding: utf-8 -*-
"""Load the Azizon 2025 catalogue into the shop.

Product copy is transcribed from data/Азизон-каталог-25.pdf (the PDF has no
text layer, so this file *is* the machine-readable version of it). Photos
were cropped out of the same pages into media/products/<slug>.jpg.

Prices deliberately land at 0: the printed catalogue carries no prices, and
the dealership sets its own. Fill them in from the admin product list.

    python manage.py seed_catalog          # upsert, keeps existing prices
    python manage.py seed_catalog --wipe   # drop everything first
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from tgbot.models import (Category, OrderProduct, Orders, Product, Subcategory)

BOILED = "pishirilgan kolbasa"
SEMI = "yarim dudlangan kolbasa"
SAUSAGE = "sosiskalar"

# (slug, title, kind, brand, diameter, weight, is_new,
#  composition, flavour, storage)
CATALOGUE = [
    # ---------------------------------------------------- pishirilgan kolbasa
    ("pishirilgan-kolbasa", "Pishirilgan kolbasa", [
        ("nonushta-uchun", "Nonushta uchun", BOILED, "AZIZON", "65 mm", "0.8 kg", False,
         "Birinchi navli mol go'shti, tovuq go'shti, quruq sut, kraxmal, tuz, ziravorlar.",
         "Qalampir, garmdori, sarimsoq va muskat yong'og'ining o'tkir ta'mli aralashmasi.",
         "Poliamid qobiq, 0 dan +8°C gacha bo'lgan temperatura va havo namligi 75±3% bo'lganda 20 sutkadan ortiq emas."),
        ("lyubitelskaya-08", "Lyubitelskaya", BOILED, "AZIZON", "80 mm", "0.8 kg", False,
         "Birinchi navli mol go'shti, tovuq go'shti, sariyog', dumba, quruq sut, kraxmal, tuz, ziravorlar.",
         "Qalampirli muskat yong'og'i qo'shilgan go'sht mazasini ifodalovchi va sarimsoqning xushbo'y ta'mi bilan yakunlovchi to'yintirilgan aralashma.",
         "Poliamid qobiq, 0 dan +8°C gacha bo'lgan temperatura va havo namligi 75±3% bo'lganda 20 sutkadan ortiq emas."),
        ("lyubitelskaya-05", "Lyubitelskaya", BOILED, "AZIZON", "80 mm", "0.5 kg", False,
         "Birinchi navli mol go'shti, tovuq go'shti, sariyog', dumba, quruq sut, kraxmal, tuz, ziravorlar.",
         "Qalampirli muskat yong'og'i qo'shilgan go'sht mazasini ifodalovchi va sarimsoqning xushbo'y ta'mi bilan yakunlovchi to'yintirilgan aralashma.",
         "Poliamid qobiq, 0 dan +8°C gacha bo'lgan temperatura va havo namligi 75±3% bo'lganda 20 sutkadan ortiq emas."),
        ("doktorskaya-08", "Doktorskaya", BOILED, "AZIZON", "65 mm", "0.8 kg", False,
         "Birinchi navli mol go'shti, oliy sifatli tovuq go'shti, tuxum, soriyog', quruq sut, kraxmal, tuz, ziravorlar.",
         "Muskat yong'og'i va sutning nafis ta'mi bilan yakunlovchi yorqin xushbo'y aralashma.",
         "Poliamid qobiq, 0 dan +8°C gacha bo'lgan temperatura va havo namligi 75±3% bo'lganda 20 sutkadan ortiq emas."),
        ("doktorskaya-05", "Doktorskaya", BOILED, "AZIZON", "65 mm", "0.5 kg", False,
         "Birinchi navli mol go'shti, oliy sifatli tovuq go'shti, tuxum, soriyog', quruq sut, kraxmal, tuz, ziravorlar.",
         "Muskat yong'og'i va sutning nafis ta'mi bilan yakunlovchi yorqin xushbo'y aralashma.",
         "Poliamid qobiq, 0 dan +8°C gacha bo'lgan temperatura va havo namligi 75±3% bo'lganda 20 sutkadan ortiq emas."),
        ("prima-08", "Prima", BOILED, "AZIZON", "80 mm", "0.8 kg", False,
         "Oliy sifatli yuqori navli go'sht, birinchi navli go'sht, tovuq go'shti, tuxum, soriyog', quruq sut, kraxmal, tuz, ziravorlar.",
         "Xushbo'y qalampir, muskat yong'og'i va go'shtning xushbo'y hididan iborat ajoyib o'tkir ta'mli aralashma.",
         "Poliamid qobiq, 0 dan +8°C gacha bo'lgan temperatura va havo namligi 75±3% bo'lganda 20 sutkadan ortiq emas."),
        ("prima-05", "Prima", BOILED, "AZIZON", "80 mm", "0.5 kg", False,
         "Oliy sifatli yuqori navli go'sht, birinchi navli go'sht, tovuq go'shti, tuxum, soriyog', quruq sut, kraxmal, tuz, ziravorlar.",
         "Xushbo'y qalampir, muskat yong'og'i va go'shtning xushbo'y hididan iborat ajoyib o'tkir ta'mli aralashma.",
         "Poliamid qobiq, 0 dan +8°C gacha bo'lgan temperatura va havo namligi 75±3% bo'lganda 20 sutkadan ortiq emas."),
    ]),
    # ------------------------------------------------ sosiskalar / sardelkalar
    ("sosiska-sardelka", "Sosiska va sardelkalar", [
        ("tovuqli-sosiska", "Tovuqli sosiskalar", SAUSAGE, "AZIZON", "19 mm", "", False,
         "Tovuq go'shti, tovuq soni, tuxum, quruq sut, kraxmal, tuz, ziravorlar.",
         "Qalampir, sarimsoq va muskat yong'og'idan iborat o'tqir ta'mli aralashma.",
         "Poliamid qobiq, 0 dan +8°C gacha bo'lgan temperatura va havo namligi 75±3% bo'lganda 20 sutkadan ortiq emas."),
        ("sutli-sosiska", "Sutli sosiskalar", SAUSAGE, "AZIZON", "19 mm", "", False,
         "Birinchi navli mol go'shti, tovuq go'shti, tovuq tuxumi, soriyog', quruq sut, kraxmal, tuz, ziravorlar.",
         "Muskat yong'og'i, xushbo'y qalampir, zira va go'shtning ajoyib xushbo'y ta'midan iborat o'tkir aralashma.",
         "Poliamid qobiq, 0 dan +8°C gacha bo'lgan temperatura va havo namligi 75±3% bo'lganda 20 sutkadan ortiq emas."),
        ("pishloqli-sosiska", "Pishloqli sosiskalar", SAUSAGE, "AZIZON", "19 mm", "", False,
         "Oliy sifatli mol go'shti, tovuq go'shti, pishloq, quruq sut, kraxmal, tuz, ziravorlar.",
         "Muskat yong'og'i, garmdori, pishloqning to'yintirilgan ta'mi va go'shtning xushbo'y ta'mi bilan ziravorlarning nafis uyg'unlashuvi.",
         "Poliamid qobiq, 0 dan +8°C gacha bo'lgan temperatura va havo namligi 75±3% bo'lganda 20 sutkadan ortiq emas."),
        ("qaymoqli-sosiska", "Qaymoqli sosiskalar", SAUSAGE, "AZIZON", "19 mm", "", False,
         "Oliy navli mol go'shti, tovuq go'shti, tovuq terisi, o'simlik oqsili, tuz, ziravorlar.",
         "Xushbo'y qalampir va qaymoqning nafis ta'midan iborat xushbo'y hidli aralashma.",
         "Poliamid qobiq, 0 dan +8°C gacha bo'lgan temperatura va havo namligi 75±3% bo'lganda 20 sutkadan ortiq emas."),
        ("taram-taram", "Taram-taram sosiskalar", SAUSAGE, "AZIZON", "19 mm", "", False,
         "Oliy sifatli tovuq go'shti, birinchi navli tovuq go'shti, quruq sut, kraxmal, tuz, ziravorlar.",
         "Qalampir, sarimsoq va zira bilan yakunlanuvchi nafis hidli to'yintirilgan aralashma.",
         "Poliamid qobiq, 0 dan +8°C gacha bo'lgan temperatura va havo namligi 75±3% bo'lganda 20 sutkadan ortiq emas."),
        ("sardelka", "Sardelkalar", "sardelkalar", "AZIZON", "32 mm", "", False,
         "Oliy sifatli mol go'shti, tovuq go'shti, sariyog', tuxum, quruq sut, kraxmal, tuz, ziravorlar.",
         "Oq qalampir, chinnigullar va chilining nozik yakuniy tegishi bilan achchiq aralashmasi.",
         "Poliamid qobiq, 0 dan +8°C gacha bo'lgan temperatura va havo namligi 75±3% bo'lganda 20 sutkadan ortiq emas."),
        ("bolajon-sosiska", "Bolajon sosiskalar", SAUSAGE, "AZIZON", "19 mm", "0.5 kg", False,
         "Yuqori sifatli mol go'shti, tovuq go'shti, sariyog', sut kukuni, kraxmal, tuxum, ziravorlar.",
         "Sariyog' va sutning munosib uyg'unligi.",
         "2°C dan 8°C gacha bo'lgan haroratda, nisbiy havo namligi 73-75%, 15 kundan ortiq emas."),
    ]),
    # ------------------------------------------------ yarim dudlangan kolbasa
    ("yarim-dudlangan", "Yarim dudlangan kolbasa", [
        ("bogi-baland", "Bog'i-baland", SEMI, "AZIZON", "32 mm", "0.3 kg", False,
         "Oliy va birinchi navli mol go'shti, tovuq go'shti, tovuq terisi, o'simlik oqsili, tuz, ziravorlar.",
         "Sarimsoq, qalampir va zanjabil bilan to'yintirilgan aralashma.",
         "Aypel qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("zernistaya", "Zernistaya", SEMI, "AZIZON", "65 mm", "1.0 kg", False,
         "Oliy va birinchi navli mol go'shti, tovuq go'shti, tovuq terisi, dumba, o'simlik oqsili, archa, tuz, ziravorlar.",
         "Qora murch, sarimsoq va garmdorining nafis bilan dudlangan yorqin xushbo'y hidli aralashma.",
         "Fibrosmog qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("afzal", "Afzal", SEMI, "AZIZON", "45 mm", "0.4 kg", False,
         "Oliy va birinchi navli mol go'shti, tovuq go'shti, tovuq terisi, dumba, o'simlik oqsili, archa, tuz, ziravorlar.",
         "Sarimsoq, xushbo'y qalampir va garmdoridan iborat o'tkir ta'mli aralashma.",
         "Amismog qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("servelat-04", "Servelat", SEMI, "AZIZON", "45 mm", "0.4 kg", False,
         "Oliy va birinchi navli mol go'shti, tovuq go'shti, tovuq terisi, o'simlik oqsili, archa, tuz, ziravorlar.",
         "Qora va qizil qalampir, zira va sarimsoq bilan to'yintirilgan aralashma.",
         "Amismog qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("servelat-08", "Servelat", SEMI, "AZIZON", "50 / 65 mm", "0.8 / 1.3 kg", False,
         "Oliy va birinchi navli mol go'shti, tovuq go'shti, tovuq terisi, dumba, o'simlik oqsili, tuz, ziravorlar.",
         "Qora va qizil qalampirning nafis xushbo'y hidli aralashmasi va sarimsoqning to'yintirilgan yorqin ta'mi.",
         "Amismog qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("sherdor", "Sherdor", SEMI, "AZIZON", "50 mm", "0.8 kg", False,
         "Oliy navli mol qo'shti, tovuq qo'shti, tovuq terisi, o'simlik oqsili, tuz, ziravorlar.",
         "Xushbo'y hidli qalampir, murch va sarimsoqning yorqin rangli xushbo'y aralashmasi.",
         "Amismog qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("luqma", "Luqma", SEMI, "AZIZON", "40 mm", "0.4 kg", False,
         "Oliy va birinchi navli mol go'shti, tovuq go'shti, tovuq terisi, dumba, o'simlik oqsili, archa, tuz, ziravorlar.",
         "Sarimsoq, xushbo'y qalampir va butun, yanchilmagan garmdori bilan o'tkir ta'mli aralashma.",
         "Amismog qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("tillo", "Tillo", SEMI, "AZIZON", "45 mm", "0.4 kg", False,
         "Oliy va birinchi navli mol go'shti, tovuq go'shti, tovuq terisi, o'simlik oqsili, tuz, ziravorlar.",
         "Zira, sarimsoq va chili qalampirining nafit ta'mi bilan yakunlanuvchi to'yintirilgan aralashma.",
         "Aytsel qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("shohona", "Shohona", SEMI, "AZIZON", "55 mm", "0.8 kg", False,
         "Oliy va birinchi navli mol go'shti, tovuq go'shti, tovuq terisi, dumba, o'simlik.",
         "Qora murch, sarimsoqning va nafis dudlangan hidli garmdoridan iborat yorqin rangli xushbo'y aralashma.",
         "Oqsilli qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("mingchinor", "Mingchinor", SEMI, "AZIZON", "46 mm", "0.4 kg", False,
         "Oliy va birinchi navli mol go'shti, tovuq go'shti, tovuq terisi, tandir go'shtning eritilgan yog'i, o'simlik oqsili, tuz, ziravorlar.",
         "Qizil va qora qalampirni eritilgan tandir yog'ida tabiiy ravishda dudlash bilan ajoyib o'tkir ta'mli aralashma.",
         "Amismog qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("ramazon", "Ramazon", SEMI, "AZIZON", "45 mm", "0.4 kg", False,
         "Oliy va birinchi navli mol go'shti, tovuq go'shti, tovuq terisi, o'simlik oqsili, tuz, ziravorlar.",
         "Zira, sarimsoq va chili qalampirining nafit ta'mi bilan yakunlanuvchi to'yintirilgan aralashma.",
         "Amismog qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("samarkand", "Samarkand", SEMI, "AZIZON", "50 mm", "0.8 kg", False,
         "Oliy va birinchi navli mol go'shti, tovuq go'shti, tovuq terisi, o'simlik oqsili, tuz, ziravorlar.",
         "Go'sht ta'mini kashnich, zira va sarimsoq bilan birgalikda ifodalovchi rustikal - oddiy aralashma.",
         "Amismog qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("osobaya", "Osobaya", SEMI, "AZIZON", "50 mm", "0.8 kg", False,
         "Oliy navli mol go'shti, tovuq go'shti, tovuq terisi, o'simlik oqsili, tuz, ziravorlar.",
         "Zanjabil ta'mli, kashnich, kardamonning nafis hidlarini ifodalovchi hushbo'y hidga to'yintirilgan aralashma.",
         "Fibrosmog qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("armavir", "Armavir", SEMI, "AZIZON", "50 / 85 mm", "0.8 / 1.5 kg", False,
         "Oliy sifatli tovuq go'shti, tovuq terisi, o'simlik oqsili, dumba, tuz, ziravorlar.",
         "Qizil qalampir, sarimsoq va rapz yog'ida tabiiy ravishda dudlash bilan ajoyib o'tkir ta'mli aralashma.",
         "Sinyuga qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("milliy", "Milliy", SEMI, "AZIZON", "75 mm", "1.8 kg", False,
         "Tovuq go'shti, tovuq terisi, dumba yog'i, o'simlik oqsili, tuz, ziravorlar.",
         "Kashnich, qalampir va zira hididan iborat o'tkir aralashma.",
         "Oqsilli qobiq, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("tillakori", "Tillakori", SEMI, "AZIZON", "45 mm", "0.4 kg", False,
         "Oliy sifatli mol go'shti, tovuq go'shti, tovuq oyog'i, o'simlik oqsili, tuz, ziravorlar.",
         "Go'shtning ta'mini yorqinroq qiluvchi qalampir, koriander, zira va sarimsoq bilan ta'minlaydigan rustik aralashmasi.",
         "Aytsel qobig'i, +2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("qorasuv", "Qorasuv", SEMI, "AZIZON", "50 mm", "0.5 kg", False,
         "Yuqori sifatli mol go'shti, tovuq go'shti, tovuq terisi, o'simlik oqsili, tuz, ziravorlar.",
         "Tabiiy qizil qalampir, sarimsoq, koriander va zira uyg'unligi.",
         "0° dan +8°C gacha bo'lgan harorat, nisbiy namlik 73-75% 20 kundan ortiq."),
        ("krakovckaya", "Krakovckaya", SEMI, "AZIZON", "32 mm", "", False,
         "Oliy va birinchi navli mol go'shti, tovuq go'shti, tovuq terisi, dumba, o'simlik oqsili, tuz, ziravorlar.",
         "Qora va qizil qalampirning eritilgan yog'i va tabiiy ravishda dudlangan ajoib aralashmasi.",
         "Aypel qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
    ]),
    # ------------------------------------------------------------- salyami
    ("salyami", "Salyami", [
        ("salyami-07", "Salyami", SEMI, "AZIZON", "50 / 65 mm", "0.7 kg", True,
         "Saralangan birinchi navli mol go'shti, saralangan birinchi navli tovuq go'shti, tovuq terisi va ziravorlar.",
         "Chili, garmdori, tminning ajoyib buketi, koriander va sarimsoqning nafis uyg'unligi bilan.",
         "Fibrosmog qobig'i, +2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("salyami-10", "Salyami", SEMI, "AZIZON", "50 / 65 mm", "1.0 kg", True,
         "Saralangan birinchi navli mol go'shti, saralangan birinchi navli tovuq go'shti, tovuq terisi va ziravorlar.",
         "Chili, garmdori, tminning ajoyib buketi, koriander va sarimsoqning nafis uyg'unligi bilan.",
         "Fibrosmog qobig'i, +2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("salyami-15", "Salyami", SEMI, "AZIZON", "50 / 65 mm", "1.5 kg", True,
         "Saralangan birinchi navli mol go'shti, saralangan birinchi navli tovuq go'shti, tovuq terisi va ziravorlar.",
         "Chili, garmdori, tminning ajoyib buketi, koriander va sarimsoqning nafis uyg'unligi bilan.",
         "Fibrosmog qobig'i, +2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
    ]),
    # ------------------------------------------------------- Afsona brendi
    ("afsona", "Afsona", [
        ("afsona-tovuqli", "Tovuqli qaynatilgan", BOILED, "AFSONA", "65 mm", "0.8 kg", False,
         "Oliy sifatli tovuq go'shti, birinchi navli tovuq go'shti, mol go'shti, tuxum, quruq sut, kraxmal, tuz, ziravorlar.",
         "Muskat yong'og'i qalampir, qalampir murchoqning dolchibibg hushbo'y ta'mi bilan ajoiyb aralashmasi.",
         "Poliamid qobiq, 0° dan +8°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("afsona-ukraincha", "Ukraincha", SEMI, "AFSONA", "50 mm", "0.5 / 0.8 / 1.1 kg", False,
         "Oliy sifatli birinchi navli tovuq go'shti, tovuq terisi, o'simlik, oqsili, tuz, ziravorlar.",
         "Kashnich, muskat yong'og'i va zanjabilning xushbo'y hididan iborat o'tkir ta'mli aralashma.",
         "Amismog qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("afsona-mol-goshtli", "Mol go'shtli", BOILED, "AFSONA", "65 mm", "0.8 kg", False,
         "Birinchi navli mol go'shti, tovuq go'shti, mol yog'i, tuxum, quruq sut, kraxmal, tuz, ziravorlar.",
         "Qalampir, sarimsoq bilan to'yintirilgan va ziraning xushbo'y hidi bilan yakunlangan aralashma.",
         "Poliamid qobiq, 0° dan +8°C gacha bo'lgan temperatura va havo namligi 75±3% bo'lganda 20 sutkadan ortiq emas."),
        ("afsona", "Afsona", SEMI, "AFSONA", "50 / 65 mm", "0.8 / 1.3 kg", False,
         "Tovuq go'shti, mol yog'i, tovuq terisi, o'simlik oqsili, tuz, ziravorlar.",
         "Qalampir, sarimsoq va piyoz bilan intensiv aralashma.",
         "Amismog qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("afsona-maxsus", "Afsona maxsus", SEMI, "AFSONA", "67 mm", "1.3 kg", False,
         "Tovuq go'shti, tovuq terisi, o'simlik oqsili, tuz, ziravorlar.",
         "Sarimsoq, muskat, zira va kashnich yordamida tabiiy xushbo'ylantirish.",
         "Aytsel qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("afsona-derevenskaya", "Derevenskaya", SEMI, "AFSONA", "50 / 85 mm", "0.8 / 1.5 kg", False,
         "Tovuq filesi, tovuq terisi, o'simlik oqsili, hayvon yog'i, tuz, ziravorlar.",
         "Go'shtning sarimsoq bilan mazasini ifodalovchi va chili (butun yanchilmagan) qalampir bilan yoqimli ta'mini yakunlovchi o'tkir ta'mini aralashma.",
         "Sinuvga qobig'i, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
    ]),
    # --------------------------------------------------------- delikateslar
    ("delikateslar", "Delikateslar", [
        ("qarta-zira", "Qarta - zira", SEMI, "AZIZON", "65 mm", "0.8 kg", False,
         "Oliy sifatli buqa go'shti, qo'y dumbasi, zira, tuz, qora murch.",
         "Qizil qalampir va ziravorlar bilan to'yintirilgan, muskat yong'og'idan iborat va ziraning xushbo'y hidi bilan yakunlanuvchi qiymalangan go'sht.",
         "Oqsilli qobiq, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("kurka-zira", "Kurka go'shti - zira", SEMI, "AZIZON", "65 mm", "0.5 kg", False,
         "Parranda go'shti, tuz, zira, qora murch.",
         "Tovuq go'shtibibg yumshoq ta'mi va ziraning nafis xushbo'y hidlari bilan to'yintirilgan aralashma.",
         "Oqsillli qobiq, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("rulet", "Rulet", "delikates", "AZIZON", "150x250 mm", "", False,
         "Tovuq filesi, tuz, zira, qora murch.",
         "Tovuq go'shtining yorqin to'yintirilgan ta'mi va xushbo'y qalampir bilan ziraning yakunlovchi hidlaridan iborat ta'mli aralashma.",
         "Polietilen qobiq, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("vetchina-rublennaya", "Vetchina rublennaya", BOILED, "AZIZON", "50 / 65 mm", "1.3 kg", True,
         "Saralangan oliy navli mol go'shti, saralangan tovuq go'shti, tovuq terisi, qo'y dumbasi va ziravorlar.",
         "Muskat, chili, mojevelnik uyg'unligi, sarimsoq va garmdorining betakror ta'mi.",
         "Palyamit qobig'i, +2° dan +6°C gacha bo'lgan temperatura va havo namligi 75% dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("tovuq-oyoqlari", "Tovuq oyoqlari", "delikates", "AZIZON", "150x250 mm", "", False,
         "Butun tovuq oyoqlari, tuz.",
         "Tovuq go'shtining haqiqiy ta'mi va tabiiy usulda nafis dudlanishi.",
         "Polietilen qobiq, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("dudlangan-dumba", "Dudlangan dumba", "delikates", "AZIZON", "150x250 mm", "", False,
         "Dumba, qora va qizil qalampir, garmdori, kashnich, tuz.",
         "Qalampir, kashnich, butun (yanchilmagan) garmdori va chili qalampirining to'yintirilgan ta'mi.",
         "Polietilen qobiq, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75 dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("tovuqli-qazi", "Tovuqli qazi", "delikates", "AZIZON", "50 mm", "0.5 kg", False,
         "Suyaksiz va terisiz tovuq oyoqlari, kungaboqar yog'i, kraxmal, tuz, ziravorlar.",
         "Tabiiy dudlangan tovuq oyoqchalari, zira va qora qalampirning nozik va xushbo'y ta'mi.",
         "0° dan +8°C gacha bo'lgan haroratda, nisbiy havo namligi 73-75% 15 kundan ortiq."),
    ]),
    # ------------------------------------------------------------- premium
    ("premium", "Premium yarim dudlangan", [
        ("premium-mol-goshtli", "Mol go'shtli premium", SEMI, "AZIZON", "45 mm", "0.4 kg", False,
         "Buqa go'shti, a'lo sifatli mol go'shti, sariyog', qo'y yoq'i, tuz, ziravorlar.",
         "Kashnich, chili qalampir, qora archa va muskatning nafis xushbo'y aralashmasi.",
         "Oqsil qobiq, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75% dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("premium-qoy-goshti", "Qo'y go'shti premium", SEMI, "AZIZON", "40 mm", "0.4 kg", False,
         "Oliy navli mol go'shti, tovuq soni, qo'y go'shti, dumba, sarimsoq, tuz, ziravorlar.",
         "Qalampirli va muskat yong'og'i qo'shilgan go'sht mazasini ifodalovchi yorqin xushbo'y hidli aralashma.",
         "Oqsilli qobiq, 2° dan +6°C gacha bo'lgan temperatura va havo namligi 75% dan 78% bo'lganda 20 sutkadan ortiq emas."),
        ("aristokrat", "Aristokrat", SEMI, "AZIZON", "40 mm", "0.4 kg", False,
         "Oliy sifatli buqa go'shti, a'lo sifatli tovuq go'shti, mol yoq'i, ot yoq'i, sarimsoq, tuz, ziravorlar.",
         "Sarimsoq, xantal va qarmdorining tutun hidi bilan rustikal - oddiy aralashmasi.",
         "Oqsilli qobiq, 0 dan +6°C gacha bo'lgan temperatura va havo namligi 75% dan 78% bo'lganda 20 sutkadan ortiq emas."),
    ]),
]


class Command(BaseCommand):
    help = "Azizon 2025 katalogini bazaga yuklaydi"

    def add_arguments(self, parser):
        parser.add_argument(
            "--wipe", action="store_true",
            help="Avval barcha mahsulot/kategoriyalarni o'chirish",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # Manba rasmlar repoda turadi; Django ularning nusxasini MEDIA_ROOT
        # ichiga o'zi joylaydi, shuning uchun ikki papka alohida.
        media = Path(settings.BASE_DIR) / "data" / "product_photos"

        if options["wipe"]:
            OrderProduct.objects.all().delete()
            Orders.objects.all().delete()
            Product.objects.all().delete()
            Subcategory.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Eski ma'lumotlar o'chirildi"))

        created = updated = with_photo = 0

        for cat_pos, (cat_slug, cat_name, items) in enumerate(CATALOGUE):
            category, _ = Category.objects.update_or_create(
                slug=cat_slug,
                defaults={"name": cat_name, "tg_name": cat_name,
                          "position": cat_pos},
            )
            # One subcategory per category: the bot's menu is
            # category -> subcategory -> inline product list, and the
            # catalogue is only two levels deep.
            subcategory, _ = Subcategory.objects.update_or_create(
                slug=f"{cat_slug}-all",
                defaults={"name": cat_name, "tg_name": cat_name,
                          "category": category, "position": cat_pos},
            )

            for pos, row in enumerate(items):
                (slug, title, kind, brand, diameter, weight, is_new,
                 composition, flavour, storage) = row

                label = title
                if weight:
                    label = f"{title} · {weight}"

                product, made = Product.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "title": label,
                        "subcategory": subcategory,
                        "brand": brand,
                        "kind": kind,
                        "composition": composition,
                        "flavour": flavour,
                        "storage": storage,
                        "diameter": diameter,
                        "weight": weight,
                        "is_new": is_new,
                        "available": True,
                        "position": pos,
                        "description": flavour,
                    },
                )
                created += made
                updated += not made

                photo = media / f"{slug}.jpg"
                if photo.exists() and not product.image:
                    with photo.open("rb") as fh:
                        product.image.save(f"{slug}.jpg", File(fh), save=True)
                    with_photo += 1

        self.stdout.write(self.style.SUCCESS(
            f"Kategoriya: {Category.objects.count()}, "
            f"subkategoriya: {Subcategory.objects.count()}, "
            f"mahsulot: {Product.objects.count()} "
            f"(yangi {created}, yangilandi {updated}, rasm {with_photo})"
        ))
