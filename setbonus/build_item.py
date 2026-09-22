# -*- coding: utf-8 -*-
"""
Собирает предметы мода: восемь рунных камней комплектов — карточки, значки и подписи.

Камни объявляют себя КРАСКАМИ (ярлык mod_dye) — этим они бесплатно получают игровой
ход «использовать из сумки → выбрать надетую вещь». Ярлык SBT_Stone отличает их от
настоящих красок, а ярлык SBT_<школа> говорит, какой комплект раздаёт этот камень.

⚠️ wcc_lite запускать ИЗ ЕГО СОБСТВЕННОЙ ПАПКИ, иначе «Can't load the game config file».
⚠️ Набор, собранный medallion/bundles.py, wcc_lite не принимает — пакуем родным.
⚠️ Подписи ОБЯЗАНЫ лежать в .w3strings — сырой текст игра не рисует ничем.
"""
import os, shutil, subprocess, sys

import loc as loc_tables
from pathlib import Path

ROOT = Path(r"D:\Apps\w3ee-tweaks")
GAME = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")
MOD = GAME / "mods" / "modSetBonusTransfer"
WCC = GAME / "mods" / "Tools" / "wcc_lite" / "bin" / "x64" / "wcc_lite.exe"
ENC = ROOT / "tools" / "w3strings" / "w3strings.exe"
RAW = Path(os.environ["TEMP"]) / "sbt_raw"
STAGE = Path(os.environ["TEMP"]) / "sbt_stage"
WORK = Path(os.environ["TEMP"]) / "sbt_strings"

XML_NAME = "sbt_items.xml"

# --vanilla: собрать ТОЛЬКО подписи с ванильными текстами бонусов и положить их в
# общую dist_vanilla — ванильная сборка отличается от редуксовой не только классом
# окна, но и ОПИСАНИЯМИ КАМНЕЙ: Redux переписывает сетовые бонусы целиком, и одна
# таблица на обе сборки врала бы одной из них (пойман пользователем по скриншоту).
VANILLA = "--vanilla" in sys.argv
DIST_V = ROOT / "dist_vanilla" / "modSetBonusTransfer" / "content"

# 4471…4475 заняты пятью модами из split/spec.py — берём следующее свободное.
IDSPACE = 4476

# 17 локалей игры. Язык определяет ИМЯ файла; метка внутри нужна только кодировщику,
# и он не знает код cn, хотя игра такую локаль грузит.
LOCALES = ["ar", "br", "cn", "cz", "de", "en", "es", "esmx",
           "fr", "hu", "it", "jp", "kr", "pl", "ru", "tr", "zh"]
META_LANG = {"cn": "zh"}

RUNE = "icons/inventory/ingredients/runes/%s_64x64.png"

# Восемь камней. Значки — разные семейства ванильных рун, чтобы камни различались
# в сумке с первого взгляда; своей графики мод не несёт вовсе.
STONES = [
    # внутреннее имя,           ярлык,         ключ подписи,     значок,                 ru,          en
    ("SBT Runestone Feline",    "SBT_Lynx",    "sbt_st_feline",    "rune_devana_greater",  "Кот",       "Feline"),
    ("SBT Runestone Griffin",   "SBT_Gryphon", "sbt_st_griffin",   "rune_stribog_greater", "Грифон",    "Griffin"),
    ("SBT Runestone Ursine",    "SBT_Bear",    "sbt_st_ursine",    "rune_svarog_greater",  "Медведь",   "Ursine"),
    ("SBT Runestone Wolven",    "SBT_Wolf",    "sbt_st_wolven",    "rune_morana_greater",  "Волк",      "Wolven"),
    ("SBT Runestone Manticore", "SBT_RedWolf", "sbt_st_manticore", "rune_perun_greater",   "Мантикора", "Manticore"),
    ("SBT Runestone Vampire",   "SBT_Vampire", "sbt_st_vampire",   "rune_veles_greater",   "Вампир",    "Vampire"),
    ("SBT Runestone Viper",     "SBT_Viper",   "sbt_st_viper",     "rune_triglav_greater", "Змея",      "Viper"),
    ("SBT Runestone Netflix",   "SBT_Netflix", "sbt_st_netflix",   "rune_zoria_greater", "Netflix",   "Netflix"),
]

# Подписи раздела настроек. Живут в том же id-пространстве, что и имена камней —
# одна сборка подписей на весь мод, меньше мест, где можно рассинхронизироваться.
MENU = [
    ("sbt_menu",      "Перенос сетовых бонусов",          "Set Bonus Transfer"),
    ("sbt_consume",   "Камень тратится при использовании", "Runestone is consumed on use"),
    ("sbt_setpieces", "Разрешать на вещах из комплектов",  "Allow on genuine set pieces"),
    ("sbt_swords",    "Разрешать на мечах",                "Allow on swords"),
    ("sbt_messages",  "Показывать сообщения",              "Show messages"),
    ("sbt_grant",     "Выдавать чертежи камней",           "Grant runestone diagrams"),
    ("sbt_ownedpower", "Сила бонуса — по собранному комплекту", "Bonus strength from the set you own"),
]

DESC_KEY = "sbt_st_desc"
DESC_RU = ("Рунный камень школы. Применяется к надетому предмету и делает его частью "
           "этого комплекта — как если бы вещь была из него выкована. Камень не тратится.")
DESC_EN = ("A school runestone. Applied to a worn item, it makes that item count towards "
           "the school's set, as though it had been forged for it. The stone is not consumed.")

NAME_RU = "Рунный камень: %s"
NAME_EN = "Runestone: %s"

# ---- пустой камень: единственное, что рецепт РАСХОДУЕТ ------------------------
EMPTY_NAME = "SBT Empty Runestone"
EMPTY_KEY = "sbt_st_empty"
EMPTY_ICON = "rune_elemental_lesser"
EMPTY_RU = "Пустой рунный камень"
EMPTY_EN = "Empty Runestone"
EMPTY_DESC_KEY = "sbt_st_empty_desc"
EMPTY_DESC_RU = ("Заготовка без свойств. Сама по себе бесполезна, но служит основой "
                 "для рунного камня школы.")
EMPTY_DESC_EN = ("A blank with no properties of its own. Useless as it is, but it is "
                 "what a school runestone is made from.")

# Заготовка стоит средних материалов, а не грошей: она — вход во всю механику,
# и слишком дешёвый вход обесценивает то, что камень стоит целого комплекта.
# Все имена проверены в файлах игры.
EMPTY_INGREDIENTS = [
    (1, "Meteorite ingot"),
    (2, "Powdered pearl"),
    (1, "Ruby dust"),
    (2, "Infused dust"),
]

# ---- руна очищения: снимает перенесённый бонус --------------------------------
CLEAN_NAME = "SBT Cleansing Runestone"
CLEAN_TAG = "SBT_Clean"
CLEAN_KEY = "sbt_st_clean"
CLEAN_ICON = "rune_elemental_greater"
CLEAN_RU = "Рунный камень очищения"
CLEAN_EN = "Cleansing Runestone"
CLEAN_DESC_KEY = "sbt_st_clean_desc"
CLEAN_DESC_RU = ("Снимает с надетой вещи перенесённый сетовый бонус. Собственный комплект "
                 "вещи при этом возвращается к ней. Камень не тратится.")
CLEAN_DESC_EN = ("Strips a transferred set bonus from a worn item. The item's own set, if it "
                 "had one, comes back. The stone is not consumed.")
CLEAN_INGREDIENTS = [
    (1, EMPTY_NAME),
]

# ---- рецепты школьных камней --------------------------------------------------
#
# ⚠️ ЦЕНА КАМНЯ — НЕ В ЭТОМ СПИСКЕ. Расходуется только заготовка; настоящее
# требование — ВЛАДЕТЬ ПОЛНЫМ КОМПЛЕКТОМ школы (6 предметов), и оно проверяется
# скриптом, а не перечислено ингредиентами. Причина не в лени:
#
#   у каждой школы 30 вещей — 5 качеств на каждый из шести слотов, и улучшение
#   СЪЕДАЕТ предыдущее качество. Рецепт из шести конкретных имён описывал бы одну
#   комбинацию качеств из 15 625 возможных и почти никогда бы не собирался.
#
# Проверка по ярлыку школы принимает комплект ЛЮБОГО качества и вдобавок не трогает
# сами вещи — ровно как задумано: комплект нужно ИМЕТЬ, а не сжечь.
INGREDIENTS = [
    (1, EMPTY_NAME),
]
CRAFT_LEVEL = "Master"     # мастер-ремесленник
CRAFT_TYPE = "Crafter"     # тот же тип, что делает рунные камни
CRAFT_PRICE = "500"        # работа мастера; главная плата — сам комплект

SC_NAME_RU = "Чертёж рунного камня: %s"
SC_NAME_EN = "Runestone diagram: %s"
SC_DESC_KEY = "sbt_sc_desc"
SC_DESC_RU = ("Чертёж рунного камня, переносящего бонус ведьмачьего комплекта.\n"
              "Требует: пустой рунный камень и полный комплект этой школы "
              "(6 предметов любого качества). Сам комплект при этом не расходуется.")
SC_DESC_EN = ("A diagram for a runestone that transfers a witcher school's set bonus.\n"
              "Requires: an empty runestone and a complete set of that school "
              "(6 pieces, any tier). The set itself is not consumed.")

T = "\t"


# ⚠️ Свойство объявляем В СВОЁМ ЖЕ ФАЙЛЕ, а не ссылаемся на чужое.
# Раньше карточки ссылались на ванильное «Magic _Stats» из def_item_quality.xml —
# в сессии ссылка разрешалась и additem работал, но предмет НЕ ПЕРЕЖИВАЛ загрузку.
# Все рабочие образцы объявляют свойства рядом с предметами: и ванильные файлы
# (руны и их «_Stats» в одном def_item_upgrades.xml), и w3ee_items.xml, где
# 159 предметов из 168 опираются на свойства, объявленные тут же.
ABILITY = "SBT Runestone _Stats"

ABILITIES = (
    T * 2 + "<abilities>\n"
    + T * 3 + '<ability name="' + ABILITY + '">\n'
    + T * 4 + "<tags></tags>\n"
    # Качество 5 — «ведьмачье снаряжение», зелёная надпись в подсказке.
    # Проверено по коду: inventoryComponent.ws — «if ( quality == 5 ) isWitcherGear = true»,
    # 4 — реликт. У ванильной брони школы Грифона тоже 5.
    + T * 4 + '<quality type="add" min="5" max="5"/>\n'
    + T * 3 + "</ability>\n"
    + T * 2 + "</abilities>\n"
)

def schem_key(stone_key):
    """sbt_st_griffin -> sbt_sc_griffin: чертёж живёт рядом со своим камнем."""
    return stone_key.replace("sbt_st_", "sbt_sc_")


def card(name, tag, key, icon, desc=None):
    # Категория «улучшение» кладёт камень на вкладку оружия и доспехов, рядом с
    # рунами и глифами — там ему и место. Раньше стояла «краска», и камни лежали
    # среди красок: категория решает ВКЛАДКУ (IsItemUpgrade = category=='upgrade'),
    # а ход «использовать» даёт ЯРЛЫК mod_dye, и он остаётся.
    #
    # Вставить камень в гнездо руны игра при этом не предложит: в разборе действий
    # (inventoryContext.ws:416) ярлык краски проверяется РАНЬШЕ ярлыка улучшения,
    # и своего ярлыка Upgrade мы намеренно не ставим.
    p = T * 4
    return (
        T * 3 + "<item\n"
        + p + "name" + p + '="' + name + '"\n'
        # ⚠️ НЕ "upgrade". Установлено лесенкой в игре: новый предмет категории
        # "upgrade" появляется, работает — и ИСЧЕЗАЕТ ИЗ СУМКИ после перезапуска.
        # Две карточки, отличавшиеся ровно этим словом: "armor" пережила, "upgrade"
        # нет. Вторая лесенка: misc, usable, crafting_ingredient, alchemy_ingredient,
        # dye, quest — выжили ВСЕ ШЕСТЬ.
        # Из них выбран "usable": вкладка снаряжения не отсеивает предметы с ярлыком
        # mod_dye (а он нужен для действия «использовать»), и раздел красок не
        # засоряется — из-за этого раньше пропал рецепт чёрной краски.
        + p + "category" + p + '="usable"\n'
        + p + "price" + p + '="500"\n'
        + p + "weight" + p + '="0.1"\n'
        + p + "stackable" + p + '="1"\n'
        + p + "grid_size" + p + '="1"\n'
        + p + "localisation_key_name" + p + '="' + key + '"\n'
        + p + "localisation_key_description" + p + '="' + (desc or DESC_KEY) + '"\n'
        + p + "icon_path" + p + '="' + (RUNE % icon) + '"\n'
        + T * 3 + ">\n"
        # mod_upgrade — тот же ярлык раздела, что у ванильных рун, чтобы камни
        # лежали рядом с ними. Ярлык Upgrade НЕ ставим: он включает «вставить в гнездо».
        + p + "<tags>" + p + "mod_upgrade, mod_dye, SBT_Stone, " + tag + "\n"
        + p + "</tags>\n"
        # ⚠️ Блок свойств ОБЯЗАТЕЛЕН для предметов категории «улучшение».
        # Без него предмет создаётся и работает в сессии, но ПРОПАДАЕТ ИЗ СУМКИ
        # после перезапуска игры. Сверка: из 48 ванильных предметов этой категории
        # блок есть у ВСЕХ 48, без него — ни одного. «Magic _Stats» — просто уровень
        # качества, без боевого эффекта и без ярлыков, включающих гнездо руны.
        + p + "<base_abilities>" + p + "<a>" + ABILITY + "</a>\n"
        + p + "</base_abilities>\n"
        + T * 3 + "</item>\n"
    )


def schem_card(name, key):
    """Предмет-чертёж: то, что лежит в сумке и читается."""
    p = T * 4
    return (
        T * 3 + "<item\n"
        + p + "name" + p + '="' + name + ' schematic"\n'
        + p + "category" + p + '="crafting_schematic"\n'
        + p + "price" + p + '="600"\n'
        + p + "weight" + p + '="0.1"\n'
        + p + "stackable" + p + '="100"\n'
        + p + "grid_size" + p + '="1"\n'
        + p + "localisation_key_name" + p + '="' + key + '"\n'
        + p + "localisation_key_description" + p + '="' + SC_DESC_KEY + '"\n'
        + p + "icon_path" + p + '="icons/inventory/quests/ico_recipe.png"\n'
        + T * 3 + ">\n"
        # SBT_Schem — по нему основной мод находит ВСЕ свои чертежи, включая
        # чертежи из дополнения, не зная их имён. Склеивать имя из строки нельзя:
        # StringToName в этой сборке нет (проверено компилятором).
        + p + "<tags>" + p + "ReadableItem, mod_crafting, mod_precious, SBT_Schem\n"
        + p + "</tags>\n"
        # ⚠️ Блок свойств ОБЯЗАТЕЛЕН для предметов категории «улучшение».
        # Без него предмет создаётся и работает в сессии, но ПРОПАДАЕТ ИЗ СУМКИ
        # после перезапуска игры. Сверка: из 48 ванильных предметов этой категории
        # блок есть у ВСЕХ 48, без него — ни одного. «Magic _Stats» — просто уровень
        # качества, без боевого эффекта и без ярлыков, включающих гнездо руны.
        + p + "<base_abilities>" + p + "<a>" + ABILITY + "</a>\n"
        + p + "</base_abilities>\n"
        + T * 3 + "</item>\n"
    )


def schematic(name):
    """Сама схема: что из чего делается и у какого ремесленника."""
    p = T * 4
    ing = "".join(
        T * 5 + '<ingredient quantity="%d" item_name="%s"/>\n' % (q, it)
        for q, it in INGREDIENTS)
    return (
        T * 2 + "<schematic\n"
        + T * 3 + "name_name" + p + '="' + name + ' schematic"\n'
        + T * 3 + "craftedItem_name" + p + '="' + name + '"\n'
        + T * 3 + "craftsmanLevel_name" + p + '="' + CRAFT_LEVEL + '"\n'
        + T * 3 + "craftsmanType_name" + p + '="' + CRAFT_TYPE + '"\n'
        + T * 3 + "price" + p + '="' + CRAFT_PRICE + '"\n'
        + T * 2 + ">\n"
        + T * 3 + "<ingredients>\n" + ing + T * 3 + "</ingredients>\n"
        + T * 2 + "</schematic>\n"
    )


def empty_card():
    """Заготовка. Без ярлыков mod_dye и SBT_Stone — использовать её не на что."""
    p = T * 4
    return (
        T * 3 + "<item\n"
        + p + "name" + p + '="' + EMPTY_NAME + '"\n'
        # ⚠️ НЕ "upgrade". Установлено лесенкой в игре: новый предмет категории
        # "upgrade" появляется, работает — и ИСЧЕЗАЕТ ИЗ СУМКИ после перезапуска.
        # Две карточки, отличавшиеся ровно этим словом: "armor" пережила, "upgrade"
        # нет. Вторая лесенка: misc, usable, crafting_ingredient, alchemy_ingredient,
        # dye, quest — выжили ВСЕ ШЕСТЬ.
        # Из них выбран "usable": вкладка снаряжения не отсеивает предметы с ярлыком
        # mod_dye (а он нужен для действия «использовать»), и раздел красок не
        # засоряется — из-за этого раньше пропал рецепт чёрной краски.
        + p + "category" + p + '="usable"\n'
        + p + "price" + p + '="120"\n'
        + p + "weight" + p + '="0.1"\n'
        + p + "stackable" + p + '="20"\n'
        + p + "grid_size" + p + '="1"\n'
        + p + "localisation_key_name" + p + '="' + EMPTY_KEY + '"\n'
        + p + "localisation_key_description" + p + '="' + EMPTY_DESC_KEY + '"\n'
        + p + "icon_path" + p + '="' + (RUNE % EMPTY_ICON) + '"\n'
        + T * 3 + ">\n"
        # Ярлык Upgrade НЕ ставим: он даёт действие «вставить в гнездо руны»,
        # а заготовка — только материал для крафта.
        + p + "<tags>" + p + "mod_upgrade, CraftingIngredient\n"
        + p + "</tags>\n"
        # ⚠️ Блок свойств ОБЯЗАТЕЛЕН для предметов категории «улучшение».
        # Без него предмет создаётся и работает в сессии, но ПРОПАДАЕТ ИЗ СУМКИ
        # после перезапуска игры. Сверка: из 48 ванильных предметов этой категории
        # блок есть у ВСЕХ 48, без него — ни одного. «Magic _Stats» — просто уровень
        # качества, без боевого эффекта и без ярлыков, включающих гнездо руны.
        + p + "<base_abilities>" + p + "<a>" + ABILITY + "</a>\n"
        + p + "</base_abilities>\n"
        + T * 3 + "</item>\n"
    )


def schematic_for(name, ingredients, level, ctype, price):
    p = T * 4
    ing = "".join(
        T * 5 + '<ingredient quantity="%d" item_name="%s"/>\n' % (q, it)
        for q, it in ingredients)
    return (
        T * 2 + "<schematic\n"
        + T * 3 + "name_name" + p + '="' + name + ' schematic"\n'
        + T * 3 + "craftedItem_name" + p + '="' + name + '"\n'
        + T * 3 + "craftsmanLevel_name" + p + '="' + level + '"\n'
        + T * 3 + "craftsmanType_name" + p + '="' + ctype + '"\n'
        + T * 3 + "price" + p + '="' + price + '"\n'
        + T * 2 + ">\n"
        + T * 3 + "<ingredients>\n" + ing + T * 3 + "</ingredients>\n"
        + T * 2 + "</schematic>\n"
    )


# ---- ОПЫТ: точная копия ванильной руны, отличается ТОЛЬКО именем ---------------
#
# Три моих версии подряд («новое имя файла», «нужна папка дополнений», «нет блока
# свойств») оказались верными по механике, но болезнь не вылечили. Значит я лечу
# по догадкам. Этот опыт разделяет две возможности за один заход:
#
#   копия ВЫЖИЛА, а наши камни нет  -> дело в полях НАШЕЙ карточки, бисектим дальше
#   копия ТОЖЕ НЕ ВЫЖИЛА            -> новый предмет из мода не выживает в принципе,
#                                       и надо не чинить карточку, а менять подход
#
# Карточка скопирована из def_item_upgrades.xml дословно; изменено одно имя.
CLONE_NAME = "SBT Clone Test"
CLONE_CARD = (
    T * 3 + "<item\n"
    + T * 4 + 'name' + T * 4 + '="' + CLONE_NAME + '"\n'
    + T * 4 + 'category' + T * 4 + '="upgrade"\n'
    + T * 4 + 'price' + T * 4 + '="155"\n'
    + T * 4 + 'weight' + T * 4 + '="0.06"\n'
    + T * 4 + 'stackable' + T * 4 + '="100"\n'
    + T * 4 + 'grid_size' + T * 4 + '="1"\n'
    + T * 4 + 'localisation_key_name' + T * 4 + '="item_name_rune_stribog_lesser"\n'
    + T * 4 + 'localisation_key_description' + T * 4 + '="item_category_runes_desc"\n'
    + T * 4 + 'icon_path' + T * 4 + '="icons/inventory/ingredients/runes/rune_stribog_lesser_64x64.png"\n'
    + T * 3 + ">\n"
    + T * 4 + "<tags>" + T * 4 + "Upgrade, WeaponUpgrade, mod_upgrade\n"
    + T * 4 + "</tags>\n"
    + T * 4 + "<base_abilities>" + T * 4 + "<a>Rune stribog lesser _Stats</a>\n"
    + T * 4 + "</base_abilities>\n"
    + T * 4 + "<recycling_parts>" + T * 4 + '<parts count="2">Infused dust</parts>\n'
    + T * 4 + "</recycling_parts>\n"
    + T * 3 + "</item>\n"
)

ITEMXML = (
    '<?xml version="1.0" encoding="UTF-16"?>\n<redxml>\n'
    + T + "<definitions>\n"
    + ABILITIES
    + T * 2 + "<items>\n"
    # У КАЖДОЙ школы своё описание: к общей строке подклеивается её
    # гроссмейстерский бонус. Отсюда и отдельный ключ описания на камень.
    + "".join(card(nm, tg, ky, ic, ky + "_d") for nm, tg, ky, ic, _ru, _en in STONES)
    + empty_card()
    + card(CLEAN_NAME, CLEAN_TAG, CLEAN_KEY, CLEAN_ICON, CLEAN_DESC_KEY)
    + "".join(schem_card(nm, schem_key(ky)) for nm, _tg, ky, _ic, _ru, _en in STONES)
    + schem_card(EMPTY_NAME, schem_key(EMPTY_KEY))
    + schem_card(CLEAN_NAME, schem_key(CLEAN_KEY))
    + T * 2 + "</items>\n" + T + "</definitions>\n"
    # Схемы лежат ОТДЕЛЬНО от предметов — в <custom>, ровно как в ванильном
    # def_item_crafting_recipes.xml.
    + T + "<custom>\n" + T * 2 + "<crafting_schematics>\n"
    + "".join(schematic_for(nm, INGREDIENTS, CRAFT_LEVEL, CRAFT_TYPE, CRAFT_PRICE)
              for nm, _tg, _ky, _ic, _ru, _en in STONES)
    + schematic_for(EMPTY_NAME, EMPTY_INGREDIENTS, "Journeyman", "Crafter", "120")
    + schematic_for(CLEAN_NAME, CLEAN_INGREDIENTS, "Master", "Crafter", "300")
    + T * 2 + "</crafting_schematics>\n" + T + "</custom>\n</redxml>\n"
)


def say(s=""):
    print(s, flush=True)


def head(s):
    say(); say("=" * 68); say("  " + s); say("=" * 68)


def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq witcher3.exe"],
                             capture_output=True, text=True, timeout=25).stdout
        return "witcher3.exe" in out.lower()
    except Exception:
        return False


def text_for(key, loc):
    # Описание камня школы: общая строка + её гроссмейстерский бонус.
    for _nm, _tg, ky, _ic, _ru, _en in STONES:
        if key == ky + "_d":
            base = loc_tables.pick(loc_tables.DESC, loc)
            bonus = loc_tables.bonus_line(ky, loc, VANILLA)
            if bonus:
                return base + " " + bonus
            return base

    """Подписи берутся из loc.py — все 17 языков. Названия комплектов остаются
    английскими намеренно: чистого названия школы в файлах игры не существует,
    а выдуманное разойдётся с тем, как комплект зовётся в самой игре."""
    if key == DESC_KEY:
        return loc_tables.pick(loc_tables.DESC, loc)
    if key == SC_DESC_KEY:
        return loc_tables.pick(loc_tables.SC_DESC, loc)
    if key == CLEAN_KEY:
        return loc_tables.pick(loc_tables.CLEAN_NAME, loc)
    if key == CLEAN_DESC_KEY:
        return loc_tables.pick(loc_tables.CLEAN_DESC, loc)
    if key == schem_key(CLEAN_KEY):
        return loc_tables.pick(loc_tables.SC_SIMPLE, loc) % loc_tables.pick(loc_tables.CLEAN_NAME, loc)
    if key == EMPTY_KEY:
        return loc_tables.pick(loc_tables.EMPTY_NAME, loc)
    if key == EMPTY_DESC_KEY:
        return loc_tables.pick(loc_tables.EMPTY_DESC, loc)
    if key == schem_key(EMPTY_KEY):
        return loc_tables.pick(loc_tables.SC_SIMPLE, loc) % loc_tables.pick(loc_tables.EMPTY_NAME, loc)
    for _nm, _tg, ky, _ic, ru, en in STONES:
        name = ru if loc == "ru" else en
        if ky == key:
            return loc_tables.pick(loc_tables.NAME, loc) % name
        if schem_key(ky) == key:
            return loc_tables.pick(loc_tables.SC_NAME, loc) % name
    for ky, ru, en in MENU:
        if ky == key:
            table = loc_tables.MENU.get(ky)
            if table:
                return loc_tables.pick(table, loc)
            return ru if loc == "ru" else en
    return key

head("Восемь рунных камней: карточки, значки, подписи")

if not WCC.exists():
    say("   [!!] wcc_lite не найден: %s" % WCC)
    sys.exit(1)
if not ENC.exists():
    say("   [!!] кодировщик подписей не найден: %s" % ENC)
    sys.exit(1)

for nm, tg, ky, ic, ru, en in STONES:
    say("   %-26s %-13s %-17s %s" % (ru, tg, ky, ic))

# ---- карточки ----------------------------------------------------------------
if RAW.exists():
    shutil.rmtree(RAW)
payload = ITEMXML.replace("\n", "\r\n").encode("utf-16")
for branch in ("items", "items_plus"):
    d = RAW / "gameplay" / branch
    d.mkdir(parents=True, exist_ok=True)
    (d / XML_NAME).write_bytes(payload)
say()
say("   [ok] карточки: %d предметов, %d Б" % (len(STONES), len(payload)))

# ---- набор файлов ------------------------------------------------------------
if STAGE.exists():
    shutil.rmtree(STAGE)
STAGE.mkdir(parents=True)

r = subprocess.run([str(WCC), "pack", "-dir=" + str(RAW), "-outdir=" + str(STAGE)],
                   capture_output=True, text=True, timeout=300, cwd=str(WCC.parent))
if not (STAGE / "blob0.bundle").exists():
    say("   [!!] pack не собрал набор (код %d)" % r.returncode)
    for line in ((r.stdout or "") + (r.stderr or "")).splitlines()[-8:]:
        say("      " + line.strip()[:110])
    sys.exit(1)
say("   [ok] blob0.bundle %d Б" % (STAGE / "blob0.bundle").stat().st_size)

subprocess.run([str(WCC), "metadatastore", "-path=" + str(STAGE)],
               capture_output=True, text=True, timeout=300, cwd=str(WCC.parent))
say("   [ok] metadata.store %s" % ("есть" if (STAGE / "metadata.store").exists() else "НЕТ"))

# ---- подписи -----------------------------------------------------------------
keys = ([ky for _nm, _tg, ky, _ic, _ru, _en in STONES]
        + [ky + "_d" for _nm, _tg, ky, _ic, _ru, _en in STONES]
        + [schem_key(ky) for _nm, _tg, ky, _ic, _ru, _en in STONES]
        + [DESC_KEY, SC_DESC_KEY,
           EMPTY_KEY, EMPTY_DESC_KEY, schem_key(EMPTY_KEY),
           CLEAN_KEY, CLEAN_DESC_KEY, schem_key(CLEAN_KEY)]
        + [ky for ky, _ru, _en in MENU])
base = int("211%04d000" % IDSPACE)
if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir(parents=True)

ok, failed = 0, []
for loc in LOCALES:
    rows = [";meta[language=%s]" % META_LANG.get(loc, loc),
            "; id      |key(hex)|key(str)| text"]
    for i, k in enumerate(keys):
        txt = text_for(k, loc)
        # Таблица подписей ПОСТРОЧНАЯ: перевод строки внутри текста молча рушит
        # сборку всех локалей разом. Наступали — заменяем на пробел.
        txt = " ".join(txt.split())
        rows.append("%d|        |%s|%s" % (base + i, k, txt))

    csv = WORK / ("sbt_%s.csv" % loc)
    csv.write_bytes(("\r\n".join(rows) + "\r\n").encode("utf-8"))   # UTF-8 без BOM

    subprocess.run([str(ENC), "--encode", str(csv), "--id-space", str(IDSPACE)],
                   capture_output=True, cwd=str(WORK))
    produced = Path(str(csv) + ".w3strings")
    if produced.exists():
        shutil.copyfile(produced, STAGE / ("%s.w3strings" % loc))
        ok += 1
    else:
        failed.append(loc)

say("   [%s] подписи: собрано %d локалей из %d%s"
    % ("ok" if not failed else "!!", ok, len(LOCALES),
       (", не вышло: " + ", ".join(failed)) if failed else ""))

if VANILLA:
    DIST_V.mkdir(parents=True, exist_ok=True)
    n = 0
    for loc in LOCALES:
        srcp = WORK / ("sbt_%s.csv.w3strings" % loc)
        if srcp.exists():
            shutil.copyfile(srcp, DIST_V / ("%s.w3strings" % loc))
            n += 1
    say("   [ok] ВАНИЛЬНЫЕ подписи: %d локалей -> %s" % (n, DIST_V))
    say("   в игру ничего не ставилось (--vanilla)")
    sys.exit(0)

# ---- установка ---------------------------------------------------------------
content = MOD / "content"
content.mkdir(parents=True, exist_ok=True)
installed, blocked = 0, 0
for src in sorted(STAGE.iterdir()):
    try:
        shutil.copyfile(src, content / src.name)
        installed += 1
    except PermissionError:
        blocked += 1

say()
if blocked:
    say("   [!] игра запущена, %d файлов заняты — установка отложена" % blocked)
    say("       готовое лежит тут: %s" % STAGE)
    bat = Path(__file__).parent / "install_stones.bat"
    bat.write_text(
        "@echo off\r\n"
        'tasklist /FI "IMAGENAME eq witcher3.exe" | find /I "witcher3.exe" >nul\r\n'
        "if not errorlevel 1 (\r\n"
        "  echo The game is still running. Close it first, then run this again.\r\n"
        "  pause\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        'xcopy /Y /Q "%s\\*" "%s\\" >nul\r\n' % (STAGE, content) +
        "echo Runestones installed. Start the game.\r\n"
        "pause\r\n", encoding="ascii")
    say("       установщик: %s" % bat)
else:
    say("   [ok] УСТАНОВЛЕНО в мод — файлов %d" % installed)

head("ГОТОВО")
say("   В игре:")
for nm, _tg, _ky, _ic, ru, _en in STONES:
    say("     additem('%s')%s// %s" % (nm, " " * max(1, 32 - len(nm)), ru))
say()
say("   Имена и описания теперь свои, значки — восемь разных рун.")
say("   Русский и английский написаны; прочие локали получают английский.")
