# -*- coding: utf-8 -*-
"""Карточки конструктора окна кузнеца (этап 4).

Окно крафта различает предметы ТОЛЬКО по именам карточек (доказано разведкой,
[[witcher3-forge-crafting-ui]]), поэтому каждый выбираемый вариант — отдельная
карточка:

  FRG Shape <донор>   жетон ОБЛИКА  тег FRG_ShapeTok   иконка донора
  FRG Dmg <донор>     жетон УРОНА   тег FRG_DmgTok     иконка донора
  frg_line_<1..26>    жетон СТРОКИ  тег FRG_LineTok    (имена frgl_* уже есть)
  frg_effect_<1..15>  жетон ЭФФЕКТА тег FRG_FxTok
  frg_slot_*          4 плейсхолдера осей якорной схемы
  FRG Forged Result   заглушка-результат с тегом FRG_Forge — по ней перехват

Якорная схема FRG ForgeBlade schematic: болванка + 4 плейсхолдера. Оси квадратиков
окно определяет по именам ингредиентов НЕТРОНУТОЙ копии схемы — плейсхолдеры и
есть эти имена.
"""
import io
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))

DONORS = json.load(io.open(os.path.join(_HERE, "donors.json"), encoding="utf-8"))

# 15 эффектов — порядок и коды дословно из FRG_FxTag (build_lab)
EFFECTS = [
    (1,  "SwordCritVigorEffect",        "Крит даёт энергию",     "Crit restores vigor"),
    (2,  "SwordRendBlastEffect",        "Взрывной размах",       "Rend blast"),
    (3,  "SwordInjuryHealEffect",       "Раны лечат",            "Injuries heal"),
    (4,  "SwordDancingEffect",          "Танцующий клинок",      "Dancing blade"),
    (5,  "SwordQuenEffect",             "Квен при ударе",        "Quen on strike"),
    (6,  "SwordWraithbaneEffect",       "Гроза призраков",       "Wraithbane"),
    (7,  "SwordBloodFrenzyEffect",      "Кровавое безумие",      "Blood frenzy"),
    (8,  "SwordKillBuffEffect",         "Удар после убийства",   "Kill momentum"),
    (9,  "SwordBeheadEffect",           "Обезглавливание",       "Beheading"),
    (10, "SwordGasEffect",              "Взрывное облако",       "Gas cloud"),
    (11, "SwordSignDancerEffect",       "Танцор знаков",         "Sign dancer"),
    (12, "SwordReachoftheDamnedEffect", "Длань проклятых",       "Reach of the damned"),
    (13, "SwordDarkCurseEffect",        "Тёмное проклятье",      "Dark curse"),
    (14, "SwordDesperateActEffect",     "Отчаянный шаг",         "Desperate act"),
    (15, "SwordRedTearEffect",          "Красная слеза",         "Red tear"),
]

# оси якорных схем: (имя плейсхолдера, тег кандидатов, ru, en)
from lines_data import FLAWS

AXES = [
    ("frg_slot_shape",  "FRG_ShapeTok", "— жетон облика —",  "- shape token -"),
    ("frg_slot_damage", "FRG_DmgTok",   "— жетон урона —",   "- damage token -"),
    ("frg_slot_line",   "FRG_LineTok",  "— свойство —",      "- property -"),
    ("frg_slot_effect", "FRG_FxTok",    "— чары —",          "- enchantment -"),
    ("frg_slot_blade",  "FRG_Blank",    "— клинок —",        "- blade -"),
    # чистая заготовка (не кованый клинок): прокрутка сталь/серебро в ковке
    ("frg_slot_blank",  "FRG_BlankRaw", "— заготовка —",     "- blank -"),
    # вспомогательное оружие: СВОЯ заготовка и СВОЙ облик (класс оружия
    # привязан к заготовке — решение пользователя 01.09)
    ("frg_slot_blank_s", "FRG_BlankRawS", "— заготовка: вспомогательное —",
     "- sidearm blank -"),
    ("frg_slot_shape_s", "FRG_ShapeTokS", "— облик вспомогательного —",
     "- sidearm shape -"),
    # ИЗУЧЕНИЕ: по оси на каждый род вещи (07.09) — в слоте перчаток
    # показываются только перчатки. Пул — ходок по СУМКЕ игрока.
    ("frg_slot_meas_w", "FRG_MeasTokW", "— клинок для изучения —",   "- blade to study -"),
    ("frg_slot_meas_a", "FRG_MeasTokA", "— доспех для изучения —",   "- armor to study -"),
    ("frg_slot_meas_p", "FRG_MeasTokP", "— штаны для изучения —",    "- trousers to study -"),
    ("frg_slot_meas_g", "FRG_MeasTokG", "— перчатки для изучения —", "- gloves to study -"),
    ("frg_slot_meas_b", "FRG_MeasTokB", "— сапоги для изучения —",   "- boots to study -"),
    # ПОРОК: необязательный четвёртый слот ковки. Лёгкая марка открывает
    # обычное место под свойство, тяжёлая — реликтовое (решение ГД 23.08)
    ("frg_slot_flaw",   "FRG_FlawTok",
     "— ПОРОК: даёт бонусный слот —", "- FLAW: buys a bonus slot -"),
    # штамп клейма: выбор одного из четырёх чистых плюсов прокруткой
    ("frg_slot_stamp",  "FRG_Stamp",    "— штамп клейма —",  "- mark stamp -"),
    # наречение: два слова имени
    ("frg_slot_word1",  "FRG_Word1",    "— первое слово —",  "- first word -"),
    ("frg_slot_word2",  "FRG_Word2",    "— второе слово —",  "- second word -"),
    # облики брони — по слоту тела (жетоны несут категорийный тег)
    ("frg_slot_shape_a", "FRG_ShapeTokA", "— облик доспеха —",   "- armor shape -"),
    ("frg_slot_shape_p", "FRG_ShapeTokP", "— облик штанов —",    "- trousers shape -"),
    ("frg_slot_shape_g", "FRG_ShapeTokG", "— облик перчаток —",  "- gloves shape -"),
    ("frg_slot_shape_b", "FRG_ShapeTokB", "— облик сапог —",     "- boots shape -"),
    # защита брони — отдельный жетон (решение пользователя: «облик от медведя,
    # броня и класс от кота»): несёт значение брони И вес-класс донора
    ("frg_slot_def_a", "FRG_DefTokA", "— защита доспеха —",   "- armor protection -"),
    ("frg_slot_def_p", "FRG_DefTokP", "— защита штанов —",    "- trousers protection -"),
    ("frg_slot_def_g", "FRG_DefTokG", "— защита перчаток —",  "- gloves protection -"),
    ("frg_slot_def_b", "FRG_DefTokB", "— защита сапог —",     "- boots protection -"),
    # ⛔ ось сопротивлений УБРАНА 15.09: в Redux резисты неотделимы от
    # показателя брони, оба едут жетоном защиты (frg_slot_def_*)
]

# ковка брони: 4 рецепта по слотам тела, ТРИ квадратика как у мечей —
# болванка + ОБЛИК (чей вид) + ЗАЩИТА (чья броня и вес-класс).
# (имя схемы, болванка, слот облика, слот защиты, заглушка, лок-ключ)
ARMOR_FORGE = [
    ("FRG ForgeArmor schematic",  "FRG Blank Armor",  "frg_slot_shape_a",
     "frg_slot_def_a", "FRG ForgeArmor Result",  "frgu_farmor", "frg_slot_res_a"),
    ("FRG ForgePants schematic",  "FRG Blank Pants",  "frg_slot_shape_p",
     "frg_slot_def_p", "FRG ForgePants Result",  "frgu_fpants", "frg_slot_res_p"),
    ("FRG ForgeGloves schematic", "FRG Blank Gloves", "frg_slot_shape_g",
     "frg_slot_def_g", "FRG ForgeGloves Result", "frgu_fgloves", "frg_slot_res_g"),
    ("FRG ForgeBoots schematic",  "FRG Blank Boots",  "frg_slot_shape_b",
     "frg_slot_def_b", "FRG ForgeBoots Result",  "frgu_fboots", "frg_slot_res_b"),
]

# категории вспомогательного оружия (копья, топоры, булавы, посохи, факелы):
# один общий класс «вспомогательное», куётся из своей заготовки
SIDE_CATS = ("secondary", "blunt1h", "staff2h", "spear2h", "axe1h", "axe2h",
             "cleaver1h", "hammer2h", "halberd2h")

# ковка вспомогательного оружия: как клинок (заготовка + облик + урон +
# необязательный порок), но заготовка и облик — своей оси
SIDE_FORGED_RESULT = "FRG ForgeSide Result"

# «Снять выкройку»: копия облика надетого снаряжения без жертвы (03.09)
COPYLOOK_RESULT = "FRG CopyLook Result"

# «Снять мерку»: все жетоны вещи без её уничтожения (07.09). Два рецепта —
# у кузнеца и у бронника, чтобы не таскать броню через полгорода.
# «Сменить облик»: тот же меч, другой вид (MVP-функция 07.09)
RESKIN_RESULT = "FRG Reskin Result"

# то же для БРОНИ — этап B (опыт 11.09 подтверждён): вещь НЕ подменяется,
# поверх неё монтируется карточка-носитель облика. Строка на каждую часть
# тела — у каждой своя ось облика.
# (схема, категория, ось облика, лок-ключ, предмет-результат, иконка)
# вечная указка «вернуть родной вид»: крутится в квадрате облика всех
# четырёх рецептов смены облика брони (пустого положения в кольце нет)
NATIVE_LOOK = "FRG Shape Native"

RESKIN_ARMOR = [
    ("FRG ReskinA schematic", "armor",  "frg_slot_shape_a", "frgu_reskin_a",
     "FRG Reskin Result A", "icons/inventory/armors/bear_armor_64x128.png"),
    ("FRG ReskinP schematic", "pants",  "frg_slot_shape_p", "frgu_reskin_p",
     "FRG Reskin Result P", "icons/inventory/armors/bear_pants_lvl5_64x128.png"),
    ("FRG ReskinG schematic", "gloves", "frg_slot_shape_g", "frgu_reskin_g",
     "FRG Reskin Result G", "icons/inventory/armors/bear_gloves_lvl5_64x128.png"),
    ("FRG ReskinB schematic", "boots",  "frg_slot_shape_b", "frgu_reskin_b",
     "FRG Reskin Result B", "icons/inventory/armors/bear_boots_lvl5_64x128.png"),
]

# ⚠️ Имя строки в витрине рецептов окно берёт у ПРЕДМЕТА-РЕЗУЛЬТАТА
# (craftingMenu.ws:1676 — loc(schematic.craftedItemName)), а НЕ у чертежа.
# Пока результат был один на все пять, игрок видел пять одинаковых
# «Снять мерку». Поэтому у каждого рецепта свой предмет-заглушка.
# (схема, ремесленник, слот, лок-ключ подписи, предмет-результат, иконка)
MEASURE_SCHEMS = [
    ("FRG Study W schematic", "Smith",   "frg_slot_meas_w", "frgu_study_w",
     "FRG Measure Result W", "icons/inventory/weapons/short_sword_lvl1_64x128.png"),
    ("FRG Study A schematic", "Armorer", "frg_slot_meas_a", "frgu_study_a",
     "FRG Measure Result A", "icons/inventory/armors/bear_armor_64x128.png"),
    ("FRG Study P schematic", "Armorer", "frg_slot_meas_p", "frgu_study_p",
     "FRG Measure Result P", "icons/inventory/armors/bear_pants_lvl5_64x128.png"),
    ("FRG Study G schematic", "Armorer", "frg_slot_meas_g", "frgu_study_g",
     "FRG Measure Result G", "icons/inventory/armors/bear_gloves_lvl5_64x128.png"),
    ("FRG Study B schematic", "Armorer", "frg_slot_meas_b", "frgu_study_b",
     "FRG Measure Result B", "icons/inventory/armors/bear_boots_lvl5_64x128.png"),
]

# штампы клейма: вечные предметы-указки, выдаются бесплатно при спавне;
# имена — лок-ключи клейм frgt_1..4 (уже локализованы)
STAMPS = [("FRG Stamp %d" % tid, "frgt_%d" % tid) for tid in (1, 2, 3, 4)]
ENCHANT_RESULT = "FRG Enchant Result"
MARK_RESULT = "FRG Mark Result"
NAME_RESULT = "FRG Name Result"

# «Наречение» — имя меча из двух слов (16 x 16 = 256 локализованных имён).
# Слова — вечные жетоны-указки; имя собирается локализацией в рантайме,
# так что русская игра видит русское имя. (id, ru, en)
WORDS1 = [
    (1,  "Гнев",     "Wrath"),    (2,  "Песнь",    "Song"),
    (3,  "Клык",     "Fang"),     (4,  "Шёпот",    "Whisper"),
    (5,  "Коготь",   "Claw"),     (6,  "Рассвет",  "Dawn"),
    (7,  "Сумрак",   "Dusk"),     (8,  "Пламя",    "Flame"),
    (9,  "Осколок",  "Shard"),    (10, "Клятва",   "Oath"),
    (11, "Жало",     "Sting"),    (12, "Эхо",      "Echo"),
    (13, "Приговор", "Verdict"),  (14, "Голод",    "Hunger"),
    (15, "Погибель", "Bane"),     (16, "Наследие", "Legacy"),
]
WORDS2 = [
    (1,  "Стрыги",          "of the Striga"),
    (2,  "Зимы",            "of Winter"),
    (3,  "Каэр Морхена",    "of Kaer Morhen"),
    (4,  "Дикой Охоты",     "of the Wild Hunt"),
    (5,  "Белого Волка",    "of the White Wolf"),
    (6,  "Полуночи",        "of Midnight"),
    (7,  "Туссента",        "of Toussaint"),
    (8,  "Скеллиге",        "of Skellige"),
    (9,  "Предвечного",     "of the Elder"),
    (10, "Лешего",          "of the Leshen"),
    (11, "Печали",          "of Sorrow"),
    (12, "Возмездия",       "of Vengeance"),
    (13, "Последнего пути", "of the Last Road"),
    (14, "Лунного серебра", "of Moonsilver"),
    (15, "Старой крови",    "of the Elder Blood"),
    (16, "Драконьих гор",   "of the Dragon Peaks"),
]

ENGRAVE_RESULT = "FRG Engrave Result"

FORGED_RESULT = "FRG Forged Result"
ANCHOR_ITEM = "FRG Blank Steel Sword"      # имя стальной болванки (превью-дефолт)

# «Путь клинка»: ВСЕ рецепты кузницы живут в СВОЕЙ группе списка. Окно
# группирует по категории craftedItem и подписывает группу локализацией
# item_category_<категория> (craftingMenu.ws:1674) — категория заглушек frgpath.
PATH_CATEGORY = "frgpath"

# ⛔ РАСПУЩЕНА 15.09: третья группа «изучение» только множила разнобой.
# Ключ и имя оставлены объявленными — выкидывать нельзя, id подписей
# считаются от ПОРЯДКА ключей, и сдвиг поедет по всему файлу строк.
STUDY_CATEGORY = "frgstudy"

# ВТОРОЙ РАЗДЕЛ СПИСКА (заказ ГД 15.09): всё, что делает БРОННИК.
# Правило простое и проверяемое: раздел = ремесленник. Кузнец -> клинки
# (PATH_CATEGORY), бронник -> доспехи (ARMOR_CATEGORY).
ARMOR_CATEGORY = "frgarmor"

# заглушки-результаты рецептов заготовок: настоящая болванка создаётся нашей
# веткой Craft, а заглушка даёт рецепту место в группе «Путь клинка»
BLANK_RESULTS = [
    ("FRG BlankSteel Result",  "FRG Blank Steel Sword",  "frgb_steel"),
    ("FRG BlankSilver Result", "FRG Blank Silver Sword", "frgb_silver"),
    ("FRG BlankSide Result",   "FRG Blank Secondary",    "frgb_side"),
    # у заготовок брони заглушек не было — и рецепты проваливались в
    # ванильные разделы «Доспехи»/«Штаны»/«Перчатки»/«Сапоги» (ГД 15.09:
    # «заготовки вообще в другом месте каком-то валяются»)
    ("FRG BlankArmor Result",  "FRG Blank Armor",        "frgb_armor"),
    ("FRG BlankPants Result",  "FRG Blank Pants",        "frgb_pants"),
    ("FRG BlankGloves Result", "FRG Blank Gloves",       "frgb_gloves"),
    ("FRG BlankBoots Result",  "FRG Blank Boots",        "frgb_boots"),
]

# ⚠️ Иконки берутся ТОЛЬКО из карточек игры (donors.json / donors_armor.json):
# выдуманный путь даёт в витрине пустой квадрат, и это не видно до запуска.
# Раньше у всех наших рецептов стоял короткий меч — сапоги и топоры выглядели
# мечами (замечено ГД 13.09).
ICON = {
    "sword":  "icons/inventory/weapons/short_sword_lvl1_64x128.png",
    "steel":  "icons/inventory/weapons/nomansland_sword_lvl4_64x128.png",
    "silver": "icons/inventory/weapons/silver_sword_lvl4_64x128.png",
    "side":   "icons/inventory/weapons/great_axe_01_64x128.png",
    "armor":  "icons/inventory/armors/bear_armor_64x128.png",
    "pants":  "icons/inventory/armors/bear_pants_lvl5_64x128.png",
    "gloves": "icons/inventory/armors/bear_gloves_lvl5_64x128.png",
    "boots":  "icons/inventory/armors/bear_boots_lvl5_64x128.png",
}

# заглушка рецепта -> род вещи, по которому берётся иконка
ICON_OF_STUB = {
    "FRG BlankSteel Result":  "steel",
    "FRG BlankSilver Result": "silver",
    "FRG BlankSide Result":   "side",
    "FRG BlankArmor Result":  "armor",
    "FRG BlankPants Result":  "pants",
    "FRG BlankGloves Result": "gloves",
    "FRG BlankBoots Result":  "boots",
    "FRG ForgeArmor Result":  "armor",
    "FRG ForgePants Result":  "pants",
    "FRG ForgeGloves Result": "gloves",
    "FRG ForgeBoots Result":  "boots",
}

# заглушки-результаты улучшений (тиры 2..4 из lines_data.TIERS)
def upgrade_result(tier):
    return "FRG Upgrade%d Result" % tier

def upgrade_schematic_name(tier):
    return "FRG Upgrade%d schematic" % tier

T = "\t"
P = T * 4


def _tok_card(name, loc_key, icon, tags):
    return (
        T * 3 + "<item\n"
        + P + 'name' + P + '="' + name + '"\n'
        + P + 'category' + P + '="misc"\n'
        + P + 'price' + P + '="25"\n'
        + P + 'weight' + P + '="0.01"\n'
        + P + 'stackable' + P + '="1"\n'
        + P + 'grid_size' + P + '="1"\n'
        + P + 'localisation_key_name' + P + '="' + loc_key + '"\n'
        + P + 'localisation_key_description' + P + '="frgu_tok_desc"\n'
        + P + 'icon_path' + P + '="' + icon + '"\n'
        + T * 3 + ">\n"
        + P + "<tags>" + P + tags + "\n"
        + P + "</tags>\n"
        + T * 3 + "</item>\n"
    )


def shape_name(donor):
    return "FRG Shape " + donor


def dmg_name(donor):
    return "FRG Dmg " + donor


def ui_cards(donor_icons):
    """Все карточки конструктора. donor_icons: имя донора -> icon_path."""
    out = []
    for d in DONORS:
        icon = donor_icons.get(d["name"], "icons/inventory/quests/ico_recipe.png")
        if d["cat"] in SIDE_CATS:
            # вспомогательное: облик своей оси; жетона урона нет — у копий
            # и булав NPC нет autogen-счётчиков, урон даёт мечевой жетон
            out.append(_tok_card(shape_name(d["name"]), "frgu_shape", icon,
                                 "mod_crafting, FRG_ShapeTokS"))
            continue
        out.append(_tok_card(shape_name(d["name"]), "frgu_shape", icon,
                             "mod_crafting, FRG_ShapeTok"))
        out.append(_tok_card(dmg_name(d["name"]), "frgu_dmg", icon,
                             "mod_crafting, FRG_DmgTok"))
    for lid in range(1, 27):
        out.append(_tok_card("frg_line_%d" % lid, "frgl_%d" % lid,
                             "icons/inventory/quests/ico_recipe.png",
                             "mod_crafting, FRG_LineTok"))
    # ПОРОКИ: своя ось (вкуются при ковке, лёгкий/тяжёлый вес).
    # Описание своё: жетон обязан объяснять себя без подсказок снаружи.
    for _f in FLAWS:
        out.append(_tok_card("frg_flaw_%d" % _f[0], "frgf_%d" % _f[0],
                             "icons/inventory/quests/ico_recipe.png",
                             "mod_crafting, FRG_FlawTok").replace(
            "frgu_tok_desc",
            "frgu_flaw_desc_light" if _f[5] == 1 else "frgu_flaw_desc_heavy", 1))
    for fid, _tag, _ru, _en in EFFECTS:
        out.append(_tok_card("frg_effect_%d" % fid, "frge_%d" % fid,
                             "icons/inventory/quests/ico_recipe.png",
                             "mod_crafting, FRG_FxTok"))
    for ph, _tag, _ru, _en in AXES:
        out.append(_tok_card(ph, "frgu_" + ph, "icons/inventory/quests/ico_recipe.png",
                             "mod_crafting"))
    # заглушка-результат ковки: по её тегу FRG_Forge перехватывается Craft.
    # Категория frgpath = группа «Путь клинка» в списке; предмет не выдаётся.
    out.append(_tok_card(FORGED_RESULT, "frgu_forged",
                         ICON["steel"],
                         "mod_crafting, FRG_Forge").replace(
        '"misc"', '"%s"' % PATH_CATEGORY, 1))
    # заглушка результата конструктора свойств: своё имя в списке рецептов
    out.append(_tok_card(ENGRAVE_RESULT, "frgu_engrave",
                         "icons/inventory/weapons/short_sword_lvl1_64x128.png",
                         "mod_crafting").replace(
        '"misc"', '"%s"' % PATH_CATEGORY, 1).replace(
        'frgu_tok_desc', 'frgu_engrave_desc', 1))
    # заглушки рецептов заготовок (болванку создаёт наша ветка Craft)
    for stub, _blank, key in BLANK_RESULTS:
        _cat = ARMOR_CATEGORY if ICON_OF_STUB[stub] in ("armor", "pants", "gloves", "boots") \
            else PATH_CATEGORY
        out.append(_tok_card(stub, key,
                             ICON[ICON_OF_STUB[stub]],
                             "mod_crafting").replace(
            '"misc"', '"%s"' % _cat, 1).replace(
            'frgu_tok_desc', 'frgb_desc', 1))
    # (заглушки улучшений убраны вместе со ступенями)
    # заглушки чар и клейма
    out.append(_tok_card(ENCHANT_RESULT, "frgu_enchant",
                         "icons/inventory/weapons/short_sword_lvl1_64x128.png",
                         "mod_crafting").replace(
        '"misc"', '"%s"' % PATH_CATEGORY, 1).replace(
        'frgu_tok_desc', 'frgu_enchant_desc', 1))
    # ⛔ КЛЕЙМО МАСТЕРА УБРАНО (требование ГД, повторное): карточки-результата
    # нет, значит рецепта в списке ремесла тоже нет.
    # штампы клейма: вечные указки с локализованными именами клейм
    for stamp, key in STAMPS:
        out.append(_tok_card(stamp, key,
                             "icons/inventory/quests/ico_recipe.png",
                             "mod_crafting, FRG_Stamp").replace(
            'frgu_tok_desc', 'frgu_stamp_desc', 1))
    # заглушка «Снять выкройку»: снимается с НАДЕТОГО, стоит у кузнеца
    out.append(_tok_card(COPYLOOK_RESULT, "frgu_copylook",
                         ICON["armor"],
                         "mod_crafting").replace(
        '"misc"', '"%s"' % PATH_CATEGORY, 1).replace(
        'frgu_tok_desc', 'frgu_copylook_desc', 1))
    # заглушка «Сменить облик»
    out.append(_tok_card(RESKIN_RESULT, "frgu_reskin",
                         "icons/inventory/weapons/short_sword_lvl1_64x128.png",
                         "mod_crafting").replace(
        '"misc"', '"%s"' % PATH_CATEGORY, 1).replace(
        'frgu_tok_desc', 'frgu_reskin_desc', 1))
    # указка «Вернуть исходный облик»: ярлыки всех четырёх осей облика
    # брони, поэтому крутится в квадрате облика любого из рецептов
    out.append(_tok_card(NATIVE_LOOK, "frgu_native",
                         "icons/inventory/quests/ico_recipe.png",
                         "mod_crafting, FRG_Native, FRG_ShapeTok, "
                         "FRG_ShapeTokA, FRG_ShapeTokP, FRG_ShapeTokG, "
                         "FRG_ShapeTokB").replace(
        'frgu_tok_desc', 'frgu_native_desc', 1))
    # заглушки «Сменить облик» для брони — своя на каждую часть тела
    for _sc, _ct, _slot, _key, _res, _icon in RESKIN_ARMOR:
        out.append(_tok_card(_res, _key, _icon, "mod_crafting").replace(
            '"misc"', '"%s"' % ARMOR_CATEGORY, 1).replace(
            'frgu_tok_desc', 'frgu_reskin_arm_desc', 1))
    # заглушки «Снять мерку» — своя на каждый род вещи: имя строки в
    # витрине берётся отсюда, иначе пять рецептов неотличимы
    for _sc, _ct, _slot, _key, _res, _icon in MEASURE_SCHEMS:
        out.append(_tok_card(_res, _key, _icon, "mod_crafting").replace(
            '"misc"', '"%s"' % (PATH_CATEGORY if _ct == "Smith"
                                else ARMOR_CATEGORY), 1).replace(
            'frgu_tok_desc', 'frgu_measure_desc', 1))
    # заглушка ковки вспомогательного оружия (категория «Путь клинка»)
    out.append(_tok_card(SIDE_FORGED_RESULT, "frgu_fside",
                         ICON["side"],
                         "mod_crafting").replace(
        '"misc"', '"%s"' % PATH_CATEGORY, 1).replace(
        'frgu_tok_desc', 'frgu_forged_desc', 1))
    # заглушки ковки брони — раздел доспехов
    for _sc, _blank, _ph, _dph, stub, key, _rph in ARMOR_FORGE:
        out.append(_tok_card(stub, key,
                             ICON[ICON_OF_STUB[stub]],
                             "mod_crafting").replace(
            '"misc"', '"%s"' % ARMOR_CATEGORY, 1).replace(
            'frgu_tok_desc', 'frgu_forged_desc', 1))
    # слова наречения: вечные указки, имя собирает локализация
    out.append(_tok_card(NAME_RESULT, "frgu_name",
                         "icons/inventory/weapons/short_sword_lvl1_64x128.png",
                         "mod_crafting").replace(
        '"misc"', '"%s"' % PATH_CATEGORY, 1).replace(
        'frgu_tok_desc', 'frgu_name_desc', 1))
    for wid, _ru, _en in WORDS1:
        out.append(_tok_card("frg_word1_%d" % wid, "frgn1_%d" % wid,
                             "icons/inventory/quests/ico_recipe.png",
                             "mod_crafting, FRG_Word1").replace(
            'frgu_tok_desc', 'frgu_word_desc', 1))
    for wid, _ru, _en in WORDS2:
        out.append(_tok_card("frg_word2_%d" % wid, "frgn2_%d" % wid,
                             "icons/inventory/quests/ico_recipe.png",
                             "mod_crafting, FRG_Word2").replace(
            'frgu_tok_desc', 'frgu_word_desc', 1))
    return "".join(out)


def _schem(name, crafted, price, ing_rows):
    ing = "".join(T * 5 + '<ingredient quantity="%d" item_name="%s"/>\n' % (q, it)
                  for q, it in ing_rows)
    return (
        T * 2 + "<schematic\n"
        + T * 3 + 'name_name' + P + '="' + name + '"\n'
        + T * 3 + 'craftedItem_name' + P + '="' + crafted + '"\n'
        # ВСЁ у подмастерья (решение старшего ГД): гейт мастерства уже зашит
        # в доноров — гроссмейстерский меч сначала куётся у гроссмейстера
        + T * 3 + 'craftsmanLevel_name' + P + '="Journeyman"\n'
        + T * 3 + 'craftsmanType_name' + P + '="Smith"\n'
        + T * 3 + 'price' + P + '="%d"\n' % price
        + T * 2 + ">\n"
        + T * 3 + "<ingredients>\n" + ing + T * 3 + "</ingredients>\n"
        + T * 2 + "</schematic>\n"
    )


def anchor_schematic():
    from lines_data import TIERS, TIER_PRICES
    # ковка: три обязательных квадратика + ЧЕТВЁРТЫЙ, необязательный — ПОРОК
    # (решение ГД 23.08): лёгкая марка открывает клинку одно обычное место под
    # свойство, тяжёлая — реликтовое. Одна марка на клинок, выбор при рождении.
    out = _schem("FRG ForgeBlade schematic", FORGED_RESULT, 50,
                 [(1, "frg_slot_blank"), (1, "frg_slot_shape"),
                  (1, "frg_slot_damage"), (1, "frg_slot_flaw")])
    # ковка вспомогательного оружия: класс задаёт заготовка — своя ось
    # заготовки и облика, урон и порок общие с клинком
    out += _schem("FRG ForgeSide schematic", SIDE_FORGED_RESULT, 50,
                  [(1, "frg_slot_blank_s"), (1, "frg_slot_shape_s"),
                   (1, "frg_slot_damage"), (1, "frg_slot_flaw")])
    # «Сменить облик»: меч + жетон облика. Свойства остаются, меняется вид
    # ЦЕНА 0 (решение ГД 13.09): облик — это косметика и знание, а не работа
    # кузнеца; платным этапом остаётся сама ковка. Заодно возврат родного вида
    # доступен при пустом кошельке — иначе ванильный гейт не пустил бы.
    out += _schem("FRG Reskin schematic", RESKIN_RESULT, 0,
                  [(1, "frg_slot_blade"), (1, "frg_slot_shape")])
    # броня: вещь + жетон облика её части тела (у бронника). Метка
    # «Вернуть исходный облик» в том же квадрате снимает облик.
    # ⚠️ Носитель вешается ПОВЕРХ вещи, сама вещь остаётся смонтированной —
    # иначе слетает скрытие частей тела (13.09, голый торс сквозь броню).
    for _sc, _ct, _slot, _k, _res, _ic in RESKIN_ARMOR:
        out += _schem(_sc, _res, 0,
                      [(1, "frg_slot_blade"), (1, _slot)]).replace(
            '"Smith"', '"Armorer"', 1)
    # «Снять мерку»: один квадратик — вещь из сумки. Цена 0: плата за
    # знание убрана совсем, дорогой этап теперь сама ковка (решение 07.09)
    for _sc, _ct, _slot, _k, _res, _ic in MEASURE_SCHEMS:
        out += _schem(_sc, _res, 0, [(1, _slot)]).replace(
            '"Smith"', '"%s"' % _ct, 1)
    # «Снять выкройку»: без плейсхолдеров — только материалы портного;
    # жетоны облика чеканит Craft-ветка по надетому снаряжению
    out += _schem("FRG CopyLook schematic", COPYLOOK_RESULT, 50,
                  [(1, "Linen"), (1, "Leather straps")])
    # улучшения УБРАНЫ (решение пользователя 22.08.2026): «никто не гоняет
    # с недоделанным мечом» — ковка сразу выдаёт реликтовое качество
    # «Свойства клинка» — КОНСТРУКТОР НАБОРОМ (решение пользователя: «вковывать
    # одновременно, видеть какой меч собираю, менять на ходу»): клинок + ПЯТЬ
    # слотов свойств; крафт пересобирает набор целиком, жетоны вечны
    out += _schem("FRG Engrave schematic", ENGRAVE_RESULT, 20,
                  [(1, "frg_slot_blade"), (1, "frg_slot_line"),
                   (1, "frg_slot_line"), (1, "frg_slot_line"),
                   (1, "frg_slot_line"), (1, "frg_slot_line")])
    # «Чары»: реликтовый эффект на реликтовый клинок; Тёмное проклятье —
    # анти-чара: занимает слот, вредит, но открывает +1 место под строку
    out += _schem("FRG Enchant schematic", ENCHANT_RESULT, 30,
                  [(1, "frg_slot_blade"), (1, "frg_slot_effect")])
    # ⛔ схема «Клеймо мастера» убрана по требованию ГД
    # «Наречение»: имя из двух слов; переименование свободно
    out += _schem("FRG Name schematic", NAME_RESULT, 10,
                  [(1, "frg_slot_blade"), (1, "frg_slot_word1"),
                   (1, "frg_slot_word2")])
    # ковка брони: у БРОННИКА, ЧЕТЫРЕ квадратика — заготовка + ОБЛИК +
    # КОСТЯК (защита, сопротивления и вес-класс одним жетоном) +
    # УНИКАЛЬНЫЙ БОНУС (последний необязателен)
    for sc, blank, ph, dph, stub, _key, _rph in ARMOR_FORGE:
        out += _schem(sc, stub, 50, [(1, blank), (1, ph), (1, dph),
                                     (1, "frg_slot_line")]).replace(
            '"Smith"', '"Armorer"', 1)
    return out


def ui_loc_keys():
    keys = ["frgu_shape", "frgu_dmg", "frgu_tok_desc", "frgu_forged",
            "frgu_forged_sc", "frgu_forged_desc", "frgu_engrave",
            "frgu_engrave_sc", "frgu_up2", "frgu_up3", "frgu_up4",
            "frgu_up2_sc", "frgu_up3_sc", "frgu_up4_sc",
            "frgu_up_desc", "item_category_" + PATH_CATEGORY,
            "item_category_" + ARMOR_CATEGORY,
            "frgu_enchant", "frgu_enchant_sc", "frgu_enchant_desc",
            "frgu_mark", "frgu_mark_sc", "frgu_mark_desc", "frgu_stamp_desc",
            "frgu_name", "frgu_name_sc", "frgu_name_desc", "frgu_word_desc",
            "frgu_mark_hint", "frgu_engrave_desc", "frgu_dup_deny",
            "frgu_full_deny", "frgu_s_flaw", "frgu_s_flaw_light",
            "frgu_s_flaw_heavy", "frgu_flaw_desc",
            "frgu_flaw_desc_light", "frgu_flaw_desc_heavy",
            "frgu_kind_deny", "frgu_axis_deny", "frgu_cap_deny",
            "frgu_slot_deny",
            "frgu_s_head", "frgu_s_target", "frgu_s_slots", "frgu_s_price",
            "frgu_s_look", "frgu_s_metal", "frgu_s_dmg", "frgu_s_def",
            "frgu_s_name", "frgu_s_pickmore", "frgu_s_steel", "frgu_s_silver",
            "frgu_s_result",
            "frgu_rl_forged", "frgu_rl_home", "frgu_rl_metal", "frgu_rl_same",
            "frgu_rl_sheathe", "frgu_rl_fail", "frgu_rl_done", "frgu_rl_to",
            "frgu_rl_pick", "frgu_rl_bag", "frgu_rl_done_v",
            "frgu_curse_vamp", "frgu_curse_done", "frgu_dlc_stale",
            "frgu_farmor", "frgu_farmor_sc", "frgu_fpants", "frgu_fpants_sc",
            "frgu_fgloves", "frgu_fgloves_sc", "frgu_fboots", "frgu_fboots_sc",
            "frgu_fside", "frgu_fside_sc",
            "frgu_copylook", "frgu_copylook_sc", "frgu_copylook_desc",
            "frgu_measure", "frgu_measure_sc", "frgu_measure_desc",
            "frgu_reskin", "frgu_reskin_sc", "frgu_reskin_desc",
            "frgu_reskin_arm_desc", "frgu_native", "frgu_native_desc",
            "frgu_reskin_a", "frgu_reskin_p", "frgu_reskin_g", "frgu_reskin_b",
            "frgu_reskin_a_sc", "frgu_reskin_p_sc",
            "frgu_reskin_g_sc", "frgu_reskin_b_sc",
            "item_category_" + STUDY_CATEGORY,
            "frgu_study_w", "frgu_study_a",
            "frgu_study_p", "frgu_study_g", "frgu_study_b",
            "frgu_study_w_sc", "frgu_study_a_sc",
            "frgu_study_p_sc", "frgu_study_g_sc", "frgu_study_b_sc",
            "frgu_def_desc", "frgu_res_desc", "frgu_w1", "frgu_w2", "frgu_w3"]
    keys += ["frge_%d" % fid for fid, _t, _r, _e in EFFECTS]
    keys += ["frgu_" + ph for ph, _t, _r, _e in AXES]
    keys += ["frgn1_%d" % wid for wid, _r, _e in WORDS1]
    keys += ["frgn2_%d" % wid for wid, _r, _e in WORDS2]
    return keys


def ui_text_for(key, ru):
    if key == "frgu_shape":
        return "Жетон облика" if ru else "Shape token"
    if key == "frgu_dmg":
        return "Жетон урона" if ru else "Damage token"
    if key == "frgu_tok_desc":
        return ("Деталь, снятая с пожертвованной вещи. Ставится в кованый клинок "
                "в окне кузнеца-мастера.") if ru else \
               ("A part struck off a sacrificed item. Forged into a blade at a "
                "master blacksmith.")
    if key == "frgu_forged" or key == "frgu_forged_sc":
        return "Кованый клинок" if ru else "Forged blade"
    # конструктор свойств принимает и броню, но стоит у кузнеца —
    # имя нейтральное, чтобы у бронника его не искали (15.09)
    if key == "frgu_engrave" or key == "frgu_engrave_sc":
        return "Свойства клинка" if ru else "Blade properties"
    if key == "frgu_engrave_desc":
        return ("Собери набор свойств целиком: два жетона (три, если при "
                "ковке вкован тяжёлый порок) — клинок пересоберётся под них. "
                "Прежние свойства снимаются, жетоны вечны, менять можно "
                "сколько угодно.") if ru else \
               ("Assemble the property set as a whole: two tokens (three if a "
                "heavy flaw was forged in) - the blade is rebuilt around them. "
                "Old properties come off, tokens are eternal, rearrange at will.")
    if key == "frgu_native_desc":
        return ("Прокрути квадрат облика до этой метки и выкуй — вещь вернётся "
                "к своему родному виду. Метка вечная и не тратится.") if ru else \
               ("Scroll the look square to this mark and forge - the piece goes "
                "back to its own native shape. The mark is eternal and is never "
                "spent.")
    if key == "frgu_reskin_arm_desc":
        return ("Та же вещь — другой вид. Сам доспех не трогается вовсе: имя, "
                "качество, зачарование, руны, комплект и улучшения остаются при "
                "нём, поверх надевается только облик. Краски ложатся и на него. "
                "Оставь квадрат облика пустым — вернётся родной вид.") if ru else \
               ("The same piece in another shape. The piece itself is never "
                "touched: name, quality, enchantment, runes, set and upgrades "
                "all stay; only the look is worn over it. Dyes take on it too. "
                "Leave the look square empty to get the native look back.")
    if key == "frgu_reskin_desc":
        return ("Меняет вид меча. Обычный меч остаётся собой — имя, качество, "
                "зачарование, руны и путь улучшения при нём, меняется только "
                "облик. Кованый клинок переезжает в новый облик со всем, что на "
                "нём есть. Метка «родной облик» или пустой квадрат облика вернут "
                "прежний вид.") if ru else                ("Changes how a sword looks. A regular sword stays itself - name, "
                "quality, enchantment, runes and upgrade path all stay, only the "
                "look changes. A forged blade moves into the new look with "
                "everything it carries. The native-look mark or an empty look "
                "square brings the old look back.")
    if key == "frgu_measure_desc":
        return ("Изучить вещь целиком, не ломая её: облик, урон, свойства, "
                "а у брони ещё защиту и сопротивления. Вещь остаётся у тебя, "
                "знание остаётся навсегда. Платишь потом — за ковку.") if ru else \
               ("Study an item whole without breaking it: look, damage, "
                "properties - and for armour its protection and resistances "
                "too. The item stays with you, the knowledge stays forever. "
                "You pay later, at the forge.")
    if key == "frgu_copylook_desc":
        return ("Скопировать облик надетого снаряжения, не жертвуя им: "
                "жетоны облика всего, что надето, включая клинки за спиной. "
                "Вещи остаются целы; уже изученное не тратит материалы.") if ru else \
               ("Copy the look of your worn gear without sacrificing it: "
                "shape tokens of everything equipped, blades on the back "
                "included. The items stay whole; nothing is spent on looks "
                "already studied.")
    if key == "frgu_axis_deny":
        return ("Эта ось уже вкована: одно свойство на ось, как рунное "
                "слово") if ru else \
               ("That axis is already forged in: one property per axis, "
                "like a runeword")
    if key == "frgu_slot_deny":
        return ("Этот бонус снят с другой части тела. В Редуксе один и тот же "
                "бафф на нагруднике вдвое сильнее, чем на штанах, перчатках и "
                "сапогах, — поэтому он остаётся при своём слоте.") if ru else \
               ("This bonus came off another body slot. In Redux the same buff "
                "is twice as strong on the chest as on trousers, gloves and "
                "boots - so it stays with the slot it was cut from.")
    if key == "frgu_cap_deny":
        return ("Так не куёт даже мир: сумма по оси превысит самую щедрую "
                "вещь игры") if ru else \
               ("Not even the world forges like that: the axis would exceed "
                "the most generous item in the game")
    if key == "frgu_kind_deny":
        return ("Это свойство доспеха — на клинок оно не ляжет") if ru else                ("That is an armour property - it will not sit on a blade")
    if key == "frgu_s_flaw":
        return ("Порок") if ru else ("Flaw")
    if key == "frgu_s_flaw_light":
        return ("  -> лёгкий порок места не даёт") if ru else \
               ("  -> a light flaw gives no slot")
    if key == "frgu_s_flaw_heavy":
        return ("  -> откроет ТРЕТЬЕ место под свойство") if ru else \
               ("  -> opens a THIRD property slot")
    if key == "frgu_flaw_desc_light":
        return ("ПОРОК КЛИНКА (лёгкий). Обычных свойств больше нет, поэтому "
                "лёгкая марка места не даёт — это просто минус. Место под третье "
                "свойство открывает только тяжёлый порок.") if ru else \
               ("A BLADE'S FLAW (light). There are no ordinary properties any "
                "more, so a light mark gives no slot - it is just a minus. Only a "
                "heavy flaw opens the third property slot.")
    if key == "frgu_flaw_desc_heavy":
        return ("ПОРОК КЛИНКА (тяжёлый). Вкуй его в четвёртый слот при ковке — "
                "и клинок получит ТРЕТЬЕ место под свойство (обычно их два). "
                "Порок — чистый минус: это плата за место. Одна марка на клинок, "
                "выбор делается при ковке.") if ru else \
               ("A BLADE'S FLAW (heavy). Forge it into the fourth slot and the "
                "blade gains a THIRD property slot (normally there are two). A "
                "flaw is a pure minus - the price of the slot. One mark per "
                "blade, chosen at the forge.")
    if key == "frgu_flaw_desc":
        return ("Порок клинка. Тяжёлая марка, вкованная при ковке, открывает "
                "третье место под свойство. Одна марка на клинок.") if ru else \
               ("A blade's flaw. A heavy mark forged in at the forge opens a "
                "third property slot. One mark per blade.")
    if key == "frgu_full_deny":
        return ("Мест под свойства не осталось: на клинок ложится два "
                "свойства, тяжёлый порок при ковке открывает третье") if ru else \
               ("No property slot left: a blade holds two properties, a heavy "
                "flaw at the forge opens a third")
    if key == "frgu_dup_deny":
        return ("Это знание уже вложено в другое место набора") if ru else \
               ("That knowledge already fills another slot of the set")
    if key == "frgu_mark_hint":
        return ("(чистый плюс, места под свойства не занимает)") if ru else \
               ("(a pure plus, takes no property slot)")
    if key == "frgu_forged_desc":
        return ("Воссоздан в кузнице из пожертвованных вещей: урон, строки, "
                "эффект и облик выбраны мастером.") if ru else \
               ("Recreated at the forge from sacrificed items: damage, lines, "
                "effect and look were the maker's choices.")
    if key == "item_category_" + STUDY_CATEGORY:
        return "Изучение свойств" if ru else "Studying properties"
    # Порядок разделов W3EE считает по СТРОКЕ подписи и сам клеит
    # неванильным категориям невидимый префикс (craftingMenu.ws:1718).
    # Свой невидимый префикс держит «клинки» выше «доспехов» — иначе
    # алфавит поставил бы доспехи первыми. Поле в окне HTML-ное.
    if key == "item_category_" + PATH_CATEGORY:
        return ('<font color="#000000"></font>Путь клинка: клинки' if ru
                else '<font color="#000000"></font>The Blade\'s Path: Blades')
    if key == "item_category_" + ARMOR_CATEGORY:
        return ('<font color="#000001"></font>Путь клинка: доспехи' if ru
                else '<font color="#000001"></font>The Blade\'s Path: Armour')
    if key == "frgu_up_desc":
        return ("Клинок растёт ступенями: качество, базовый урон и число мест "
                "под строки. Реликтовая ступень пробуждает полный урон донора "
                "и открывает чары и клеймо.") if ru else \
               ("The blade grows in tiers: quality, base damage and line "
                "slots. The relic tier awakens the donor's full damage and "
                "unlocks enchanting and the maker's mark.")
    if key == "frgu_enchant" or key == "frgu_enchant_sc":
        return "Чары клинка" if ru else "Blade enchanting"
    if key == "frgu_enchant_desc":
        return ("Реликтовый эффект — красная строка — ложится на клинок "
                "реликтовой ступени. Тёмное проклятье — особый случай: если "
                "клинок в руке 5 секунд не бьёт врага, оно тянет по 1% здоровья "
                "в секунду и может убить; зато даёт +10% к вампиризму.") if ru else \
               ("A relic effect - the red line - goes onto a relic-tier blade. "
                "The Dark Curse is special: when the drawn blade lands no hit "
                "for 5 seconds it drains 1% of your health per second and can "
                "kill; in return it gives +10% vampirism.")
    if key == "frgu_mark" or key == "frgu_mark_sc":
        return "Клеймо мастера" if ru else "Maker's mark"
    if key == "frgu_mark_desc":
        return ("Мастер подписывает работу: один маленький чистый плюс по "
                "выбору штампа, вне мест под строки. Второе клеймо — только "
                "на полностью сгравированный клинок.") if ru else \
               ("The maker signs the work: one small pure plus by stamp, "
                "outside line slots. A second mark - only on a fully "
                "engraved blade.")
    if key == "frgu_stamp_desc":
        return ("Штамп клейма. Вечная указка: выбирает, какое клеймо выжечь, "
                "и никогда не тратится.") if ru else \
               ("A mark stamp. An eternal pointer: picks which mark to burn "
                "in, never spent.")
    _farmor = {"frgu_farmor": ("Кованый доспех", "Forged armor"),
               "frgu_fpants": ("Кованые штаны", "Forged trousers"),
               "frgu_fgloves": ("Кованые перчатки", "Forged gauntlets"),
               "frgu_fboots": ("Кованые сапоги", "Forged boots"),
               "frgu_fside": ("Кованое вспомогательное оружие",
                              "Forged sidearm"),
               "frgu_copylook": ("Снять выкройку", "Take a pattern"),
               "frgu_measure": ("Снять мерку", "Take measurements"),
               "frgu_reskin": ("Сменить облик", "Change the look"),
               "frgu_native": ("Вернуть исходный облик",
                               "Restore the native look"),
               "frgu_reskin_a": ("Сменить облик: доспех",
                                 "Change the look: armor"),
               "frgu_reskin_p": ("Сменить облик: штаны",
                                 "Change the look: trousers"),
               "frgu_reskin_g": ("Сменить облик: перчатки",
                                 "Change the look: gloves"),
               "frgu_reskin_b": ("Сменить облик: сапоги",
                                 "Change the look: boots"),
               "frgu_study_w": ("Изучить оружие", "Study a weapon"),
               "frgu_study_a": ("Изучить доспех", "Study an armor"),
               "frgu_study_p": ("Изучить штаны", "Study trousers"),
               "frgu_study_g": ("Изучить перчатки", "Study gloves"),
               "frgu_study_b": ("Изучить сапоги", "Study boots")}
    for _k, (_r, _e) in _farmor.items():
        if key == _k or key == _k + "_sc":
            return _r if ru else _e
    _summ = {
        "frgu_s_head": ("— Сборка —", "- The build -"),
        "frgu_s_target": ("Цель", "Target"),
        "frgu_s_slots": ("Мест занято", "Slots used"),
        "frgu_s_price": ("Цена", "Price"),
        "frgu_s_look": ("Облик", "Look"),
        "frgu_s_metal": ("Металл", "Metal"),
        "frgu_s_dmg": ("Урон донора", "Donor damage"),
        "frgu_s_def": ("Защита", "Protection"),
        "frgu_s_name": ("Имя", "Name"),
        "frgu_s_pickmore": ("(прокрути слоты, чтобы выбрать)",
                            "(scroll the slots to pick)"),
        "frgu_s_steel": ("стальной клинок", "steel blade"),
        "frgu_s_silver": ("серебряный клинок", "silver blade"),
        "frgu_s_result": ("Итог: реликтовое качество, 2 места свойств (3 с тяжёлым пороком), 3 гнезда рун",
                          "Result: relic quality, 2 property slots (3 with a heavy flaw), 3 rune sockets"),
        # смена облика меча (карточная пересадка, 23.09)
        "frgu_rl_forged": ("Облик меняется только у меча — не у заготовки, топора или булавы",
                           "Only a sword changes its look - not a blank, an axe or a mace"),
        "frgu_rl_done_v": ("Меч сменил облик. Сам меч не тронут: имя, качество, зачарование и руны при нём.",
                           "The sword wears a new look. The sword itself is untouched: name, quality, enchantment and runes stay."),
        "frgu_rl_home": ("Клинок и так в родном облике — выбери другой облик",
                         "The blade already wears its own look - pick another one"),
        "frgu_rl_metal": ("Для этого облика нет клинка такого металла",
                          "No blade of this metal for that look"),
        "frgu_rl_same": ("Клинок уже в этом облике — прокрути квадрат облика",
                         "The blade already wears this look - scroll the look square"),
        "frgu_rl_sheathe": ("Сначала убери клинок в ножны",
                            "Sheathe the blade first"),
        "frgu_rl_fail": ("Облик не сменился, клинок не тронут",
                         "The look did not change, the blade is untouched"),
        "frgu_rl_done": ("Клинок сменил облик. Урон, стихийный урон, свойства, "
                         "чары, руны, зачарование, износ и масло перешли вместе с ним.",
                         "The blade takes the new look. Damage, elemental damage, "
                         "properties, charm, runes, enchantment, wear and oil came along."),
        "frgu_rl_to": ("Станет", "Becomes"),
        # «Тёмное проклятье» несёт вампиризм в самих чарах (ГД 24.09)
        "frgu_curse_vamp": ("+10% к вампиризму", "+10% vampirism"),
        "frgu_dlc_stale": ("Кузница: пакет предметов устарел — закрой игру и пересобери его. "
                           "До этого жетоны свойств не меняются, а разбор кузницей отложен.",
                           "Forge: the items package is out of date - close the game and rebuild it. "
                           "Until then property tokens are not traded and forge dismantling waits."),
        "frgu_curse_done": ("ПРОКЛЯТАЯ КОВКА: Тёмное проклятье легло на клинок. Пока он в "
                            "руке и 5 секунд не бьёт врага, проклятье тянет из тебя здоровье; "
                            "зато клинок пьёт кровь: +10% к вампиризму.",
                            "CURSED FORGING: the Dark Curse settles onto the blade. While it "
                            "is drawn and lands no hit for 5 seconds, the curse feeds on you; "
                            "but the blade drinks blood: +10% vampirism."),
        "frgu_rl_pick": ("Сначала выбери клинок — прокрути первый квадрат",
                         "Pick the blade first - scroll the first square"),
        "frgu_rl_bag": ("Клинок должен быть на Геральте или в сумке, не в седельных сумках",
                        "The blade must be on Geralt or in his bag, not in the saddlebags"),
    }
    if key in _summ:
        r, e = _summ[key]
        return r if ru else e
    if key == "frgu_res_desc":
        return ("Сопротивления и повадки веса, снятые с пожертвованной брони: "
                "рубящие, колющие, ударные, эфирные — и то, как доспех давит "
                "на выносливость. Ставится отдельно от показателя брони.") if ru else \
               ("Resistances and weight manners struck off sacrificed armour: "
                "slashing, piercing, bludgeoning, elemental - and how the "
                "piece taxes stamina. Fitted apart from the armour value.")
    if key == "frgu_def_desc":
        return ("Костяк доспеха, снятый с пожертвованной вещи: показатель "
                "брони, сопротивления и вес-класс — одним куском, как оно и "
                "устроено. Облик и уникальный бонус ставятся отдельно.") if ru else \
               ("The backbone struck off a sacrificed piece: armour value, "
                "resistances and weight class in one - the way they belong "
                "together. Look and the unique bonus are set separately.")
    if key == "frgu_w1":
        return "лёгкая" if ru else "light"
    if key == "frgu_w2":
        return "средняя" if ru else "medium"
    if key == "frgu_w3":
        return "тяжёлая" if ru else "heavy"
    if key == "frgu_name" or key == "frgu_name_sc":
        return "Наречение клинка" if ru else "Blade naming"
    if key == "frgu_name_desc":
        return ("Клинок получает имя из двух слов — оно встанет вместо "
                "названия в сумке и подсказке. Переименовать можно всегда; "
                "слова вечны.") if ru else \
               ("The blade takes a two-word name - shown in the bag and the "
                "tooltip. Rename any time; the words are eternal.")
    if key == "frgu_word_desc":
        return ("Слово для наречения клинка. Вечная указка.") if ru else \
               ("A word for naming a blade. An eternal pointer.")
    if key.startswith("frgn1_"):
        for wid, r, e in WORDS1:
            if key == "frgn1_%d" % wid:
                return r if ru else e
    if key.startswith("frgn2_"):
        for wid, r, e in WORDS2:
            if key == "frgn2_%d" % wid:
                return r if ru else e
    if key.startswith("frgu_up") and (key[7:8].isdigit()):
        from lines_data import TIERS
        tier = int(key[7])
        for t, _ab, _d, _m, r, e in TIERS:
            if t == tier:
                if key.endswith("_sc"):
                    return ("Чертёж: " + r) if ru else ("Diagram: " + e)
                return r if ru else e
    for fid, _tag, r, e in EFFECTS:
        if key == "frge_%d" % fid:
            return ("Жетон эффекта: " + r) if ru else ("Effect token: " + e)
    for ph, _tag, r, e in AXES:
        if key == "frgu_" + ph:
            return r if ru else e
    return None
