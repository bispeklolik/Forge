# -*- coding: utf-8 -*-
"""
БОЛВАНКИ КУЗНИЦЫ — dlc\\dlcFRGBlanks: шесть заготовок с ПУСТОЙ карточкой статов.

Зачем: проверкой этапа 2 найден предел движка — свойства из XML-карточки скриптом
не снимаются. Значит «собрать свою вещь с нуля» можно только на носителе, которому
нечего снимать. Болванка = экипируемый предмет без единого свойства в карточке
(кроме безвредного качества «обычное»): урон, проценты, эффект и облик ложатся на
неё заменой.

Иммерсивность (решение пользователя): болванка стоит денег И ресурсов — куётся у
мастеров. Мечи — у КУЗНЕЦА (Smith), броня — у БРОННИКА (Armorer).

Устройство карточек: поля экипировки (equip_template, слоты, анимации, звук)
СПИСЫВАЮТСЯ С ЖИВЫХ ОБРАЗЦОВ прямо из бандлов при сборке — руками их не набрать,
а промах в любом поле = ненадеваемый или крашащий предмет:

    сталь    <- Short sword 1_crafted      (простой меч, полный набор полей)
    серебро  <- Silver sword 1_crafted
    броня    <- DLC1 Temerian Armor        (обычная надеваемая броня)
    штаны    <- DLC1 Temerian Pants
    перчатки <- DLC1 Temerian Gloves
    сапоги   <- DLC1 Temerian Boots

Паспорт дополнения — правка копии «Бродяги» (строки той же длины), как у камней.
"""
import os, re, shutil, struct, subprocess, sys, zlib
from pathlib import Path

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from medallion import bundles as B

GAME = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")
DOCS = Path(os.environ["USERPROFILE"]) / "Documents" / "The Witcher 3"
WCC = GAME / "mods" / "Tools" / "wcc_lite" / "bin" / "x64" / "wcc_lite.exe"
ENC = Path(r"D:\Apps\w3ee-tweaks") / "tools" / "w3strings" / "w3strings.exe"
TPL = Path(os.environ["TEMP"]) / "vagabond.reddlc"

DLC = GAME / "dlc" / "dlcFRGBlanks"
RAW = Path(os.environ["TEMP"]) / "frgb_raw"
WORK = Path(os.environ["TEMP"]) / "frgb_strings"

MOUNT = "frgblank"                        # 8, как vagabond
ITEMS = "frgblank_items.xml"              # 18, как vagabond_items.xml
SHOP = "frgblank_shop.xml"                # 17, как vagabond_shop.xml
EXTS = "frgblank_item_extensions.xml"     # 28, как vagabond_item_extensions.xml
DLC_ID = "dlc_frg_001"                    # 11, как dlc_005_001

PATCH = [
    (b"vagabond_item_extensions.xml", EXTS.encode()),
    (b"vagabondarmor_desc",           b"frgblankitems_desc"),
    (b"vagabond_items.xml",           ITEMS.encode()),
    (b"vagabond_shop.xml",            SHOP.encode()),
    (b"vagabondarmor",                b"frgblankitems"),
    (b"dlc_005_001",                  DLC_ID.encode()),
    (b"vagabond",                     MOUNT.encode()),
]

# 4471..4479 заняты (проверено research\scan_idspaces.py) — берём следующее.
IDSPACE = 4480
LOCALES = ["ar", "br", "cn", "cz", "de", "en", "es", "esmx",
           "fr", "hu", "it", "jp", "kr", "pl", "ru", "tr", "zh"]
META_LANG = {"cn": "zh"}

ABILITY = "FRG Blank _Stats"

# Реестр строк конструктора — общий с build_lab.py
sys.path.insert(0, str(Path(__file__).parent))
from lines_data import (LINES, CUT, TOKEN_ITEM, TEMPER, BLANK_DURABILITY, FLAWS,
                        DMG_MARKS, TIERS, FLAT, flat_ability,
                        ARMOR, armor_ability, armor_res_ability,
                        ARMOR_LINES, ARMOR_TIER_PENALTY,
                        stat_short)

# статы строк/клейм/флэтов уходят в ЛОКАЛИЗАЦИЮ (компактно, кириллицей):
# ключ -> attrs; собирается по всему реестру
_STAT_KEYS = {}
for _lid, _rx, _o, _junk, _attrs, _ru, _en in LINES:
    _STAT_KEYS["frgls_%d" % _lid] = _attrs
for _c in CUT:
    _STAT_KEYS["frgls_%d" % _c["id"]] = [tuple(s) for s in _c["stats"]]
for _lid, _rx, _o, _w, _attrs, _ru, _en in ARMOR_LINES:
    _STAT_KEYS["frgls_%d" % _lid] = _attrs
for _tid, _o, _attrs, _ru, _en in TEMPER:
    _STAT_KEYS["frgts_%d" % _tid] = _attrs
for _f in FLAWS:
    _STAT_KEYS["frgfs_%d" % _f[0]] = _f[4]
for _dn, _rec in FLAT.items():
    _STAT_KEYS["frgfd_%d" % _rec["num"]] = [tuple(s) for s in _rec["rows"]]
import ui_data
import io as _io
import json as _json

# ── двойники кросс-обликов (ножны) ────────────────────────────────────────────
# У кросс-меча ножны гейтятся свойством swordType в сущности .w2ent, поэтому
# equip_template кросс-карточки перенаправляем на ДВОЙНИКА (оболочка целевого
# металла + геометрия донора). Подробно — forge_twins.py.
_TWINS = {}
_TWIN_MAKER_INST = None
def _twin_maker():
    global _TWIN_MAKER_INST
    if _TWIN_MAKER_INST is None:
        import forge_twins
        _TWIN_MAKER_INST = forge_twins.TwinMaker()
    return _TWIN_MAKER_INST

# доноры-броня (этап Б): 337 предметов armor/pants/gloves/boots
try:
    ARMOR_DONORS = _json.load(_io.open(
        str(Path(__file__).parent / "donors_armor.json"), encoding="utf-8"))
except Exception:
    ARMOR_DONORS = []

_SHAPE_TAG = {"armor": "FRG_ShapeTokA", "pants": "FRG_ShapeTokP",
              "gloves": "FRG_ShapeTokG", "boots": "FRG_ShapeTokB"}
_DEF_TAG = {"armor": "FRG_DefTokA", "pants": "FRG_DefTokP",
            "gloves": "FRG_DefTokG", "boots": "FRG_DefTokB"}
# сопротивления и повадки веса — своя ось (решение 05.09)
_RES_TAG = {"armor": "FRG_ResTokA", "pants": "FRG_ResTokP",
            "gloves": "FRG_ResTokG", "boots": "FRG_ResTokB"}
_BLANK_OF = {"armor": "FRG Blank Armor", "pants": "FRG Blank Pants",
             "gloves": "FRG Blank Gloves", "boots": "FRG Blank Boots"}

# модовые облики (заказ 03.09): ТОЛЬКО жетон облика, без защиты и строк.
# Жетоны продаёт Элихаль; сами вещи скрыты из магазинов глушителем витрины.
SKIN_ONLY_NAMES = {"Frayed Armor", "Frayed Gloves", "Raven Armor",
                   "Raven Pants", "Raven Gloves", "Raven Boots",
                   "vagabondarmor",
                   # перенесённый вид модов Весемира (15.09): свой предмет
                   # в dlcFRGVesemir, ваниль Змеи не тронута
                   "Vesemir KM Armor"}
# облики TW2 Gear (18.09): свои предметы в dlcFRGTW2 по путям-двойникам,
# ваниль не тронута. Тоже ТОЛЬКО жетон облика — и через _ARMOR_LOOKS
# сами уходят в обе лавки (Элихаль + гроссмейстер Туссента). Список
# пишет build_tw2looks.py; читаем его, а не копию имён.
_TW2_DONORS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "tw2", "tw2_donors.json")
if os.path.exists(_TW2_DONORS):
    SKIN_ONLY_NAMES |= {_d["name"] for _d in _json.load(
        _io.open(_TW2_DONORS, encoding="utf-8"))}
# облики Змеи (dlcFRGZmeya, 18.09): свои предметы по путям-двойникам,
# ваниль не тронута; моды-замены гасятся при build_zmeya --install. Тоже
# только жетон облика — через _ARMOR_LOOKS сами идут в обе лавки.
_ZMEYA_DONORS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "zmeya_donors.json")
if os.path.exists(_ZMEYA_DONORS):
    SKIN_ONLY_NAMES |= {_d["name"] for _d in _json.load(
        _io.open(_ZMEYA_DONORS, encoding="utf-8"))}
# ВСЕ уникальные облики брони идут в лавку Элихаля (заказ 05.09): список
# строит gen_elihal.py (generic-одежда вон, дубли по модели схлопнуты)
ELIHAL_LOOKS = _json.load(_io.open(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "elihal_looks.json"), encoding="utf-8"))

# Облики ОРУЖИЯ — у кузнеца-гроссмейстера в Туссенте (заказ 15.09). Список
# строит gen_gmlooks.py: массовый ширпотреб и мёртвые облики отсеяны.
_GM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "gm_looks.json")
GM_LOOKS = (_json.load(_io.open(_GM_PATH, encoding="utf-8"))
            if os.path.exists(_GM_PATH) else [])
# Лут-имя лавки ГРОССМЕЙСТЕРА Туссента (Лазарь Лафарг). Внутри игры этот тир
# зовётся archmaster, и лавка висит ровно на одной сущности — slavko_atimstein,
# которая несёт роли и Blacksmith, и Armorer: один торговец на оружие и броню.
# ⛔ Ловушка: "_EP2_store_grandmaster" (без arch) — это ТРИ РЯДОВЫХ мастера
# Боклера, они лишь подсказывают, где искать гроссмейстера.
# Записи <loot_entry> из разных файлов СКЛАДЫВАЮТСЯ (прецеденты: dlc__raven_armor
# и сам W3EE дописывают эту же лавку) — чужой ассортимент не затирается.
GM_SHOP = "_EP2_store_archmaster"

# Зеркало прилавка под скриптовый долив (кузница зовёт его сама).
# Нужно потому, что из общего пула игра берёт лишь quantity позиций —
# у гроссмейстера это 100 при 128 чужих гарантированных записях, и наши
# жетоны в выборку не попадают НИКОГДА. Плюс витрина раскатывается один
# раз при первом спавне торговца и живёт в сейве: данные, добавленные
# позже, уже встреченный торговец не увидит.
MIRROR = {"_store__Elihal_Apparel_Shop": "_FRG_stock_elihal",
          GM_SHOP: "_FRG_stock_gm"}

# у Frayed/Vagabond локализация en-only — кованая вещь и жетон берут наш ключ
_LOOK_LOCKEY = {"Frayed Armor": "frgv_frayed", "Frayed Gloves": "frgv_frayedg",
                "vagabondarmor": "frgv_vagabond",
                "Vesemir KM Armor": "frgv_vesemir"}
FRGZ_TEXT = {
    'frgz_vsmkm_boots': ('Сапоги Весемира (Каэр-Морхен)', "Vesemir's KM Boots"),
    'frgz_vsmkm_gloves': ('Перчатки Весемира (Каэр-Морхен)', "Vesemir's KM Gloves"),
    'frgz_vsmkm_pants': ('Штаны Весемира (Каэр-Морхен)', "Vesemir's KM Trousers"),
    'frgz_prfkm_armor': ('Доспех «Идеальный Каэр-Морхен»', 'Perfect Kaer Morhen Armour'),
    'frgz_prfkm_gloves': ('Перчатки «Идеальный Каэр-Морхен»', 'Perfect KM Gloves'),
    'frgz_prfkm_pants': ('Штаны «Идеальный Каэр-Морхен»', 'Perfect KM Trousers'),
    'frgz_prfkm_boots': ('Сапоги «Идеальный Каэр-Морхен»', 'Perfect KM Boots'),
}

# теги комплектов W3EE: ни один не содержит "SetBonus"/"set_", поэтому
# прежний фильтр их пропускал и кованая вещь вписывалась в ЧУЖОЙ комплект
SET_TAGS = {
    "TemerianSet", "BearSet", "WolfSet", "GryphonSet", "LynxSet",
    "RedWolfSet", "ViperSet", "VampireSet", "VampireSetAlt", "NilfgaardSet",
    "SkelligeSet", "OfieriSet", "NewMoonSet", "NetflixSet", "ElvenSet",
    "TigerSet", "GothicSetTag", "DimeritiumSetTag", "MeteoriteSetTag",
    "SetBonusPiece",
}


def is_set_tag(tag):
    t = tag.strip()
    return (t in SET_TAGS or "SetBonus" in t or "set_" in t.lower()
            or t.endswith("Set") or t.endswith("SetTag"))


TOKEN_KEY = "frgl_token"
TOKEN_DESC_KEY = "frgl_token_desc"
TOKEN_RU = "Жетон свойства"
TOKEN_EN = "Property token"
TOKEN_DESC_RU = ("Свойство, изученное с пожертвованной вещи. Мастер вковывает его "
                 "в клинок: сильное свойство несёт свой минус в самой паре, а метка "
                 "хлама открывает лишнее место. Знание вечно — жетон не тратится.")
TOKEN_DESC_EN = ("A property studied off a sacrificed item. A craftsman forges it "
                 "into a blade: a strong property carries its own minus inside the "
                 "pair, a junk mark opens an extra slot. Knowledge is eternal - "
                 "the token is never spent.")

# имя болванки, образец, ключ, кузнец/бронник, ингредиенты, ru, en
# ОДНА болванка на категорию (решение пользователя: классы-карточки — лишняя
# возня). Урон-штраф и слоты задаются ЖЕЛОБАМИ (FRG_D_*) на экземпляре.
BLANKS = [
    ("FRG Blank Steel Sword",  "Short sword 1_crafted",  "frgb_steel",  "Smith",
     [(3, "Steel ingot"), (1, "Leather straps"), (1, "Timber")],
     "Кованая заготовка: стальной клинок", "Forged blank: steel blade"),
    ("FRG Blank Silver Sword", "Silver sword 1_crafted", "frgb_silver", "Smith",
     [(2, "Silver ingot"), (1, "Steel ingot"), (1, "Leather straps")],
     "Кованая заготовка: серебряный клинок", "Forged blank: silver blade"),
    # вспомогательное оружие: класс задаёт заготовка (решение 01.09) —
    # копья, топоры, булавы, посохи куются из этой болванки
    ("FRG Blank Secondary", "Short sword 1_crafted", "frgb_side", "Smith",
     [(2, "Steel ingot"), (1, "Timber"), (1, "Leather straps")],
     "Кованая заготовка: вспомогательное оружие", "Forged blank: a sidearm"),
    ("FRG Blank Armor",        "Light armor 01_crafted", "frgb_armor",  "Armorer",
     [(2, "Hardened leather"), (2, "Linen"), (1, "Iron ingot")],
     "Кованая заготовка: доспех", "Forged blank: armor"),
    ("FRG Blank Pants",        "Pants 01_crafted",       "frgb_pants",  "Armorer",
     [(1, "Hardened leather"), (2, "Linen")],
     "Кованая заготовка: штаны", "Forged blank: trousers"),
    ("FRG Blank Gloves",       "Gloves 01_crafted",      "frgb_gloves", "Armorer",
     [(1, "Hardened leather"), (1, "Linen")],
     "Кованая заготовка: перчатки", "Forged blank: gloves"),
    ("FRG Blank Boots",        "Boots 01_crafted",       "frgb_boots",  "Armorer",
     [(1, "Hardened leather"), (1, "Leather straps")],
     "Кованая заготовка: сапоги", "Forged blank: boots"),
]

DESC_KEY = "frgb_desc"
DESC_RU = ("Заготовка без единого свойства. Кузница кладёт на неё урон, проценты, "
           "эффект и облик пожертвованных вещей — заменой, а не поверх: заменять "
           "здесь нечего.")
DESC_EN = ("A blank with not a single property of its own. The forge lays a donor's "
           "damage, percents, effect and look onto it as a replacement — there is "
           "nothing here to replace.")
SC_DESC_KEY = "frgb_sc_desc"
SC_DESC_RU = "Чертёж кованой заготовки. Мечи куёт кузнец, броню — бронник."
SC_DESC_EN = "Diagram for a forged blank. Swords by the blacksmith, armour by the armorer."

T = "\t"
P = T * 4


def say(s=""):
    print(s, flush=True)


def head(s):
    say(); say("=" * 70); say("  " + s); say("=" * 70)


def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq witcher3.exe"],
                             capture_output=True, text=True, timeout=25).stdout
        return "witcher3.exe" in out.lower()
    except Exception:
        return False


def dec(b):
    for e in ("utf-16", "utf-8"):
        try:
            t = b.decode(e)
            if "<" in t[:400]:
                return t
        except Exception:
            pass
    return None


_SCAB_SET = None


def all_scabbards():
    """Имена всех ножен игры (scabbard_steel_* / scabbard_silver_*). Нужно,
    чтобы при кросс-облике подменить ножны на нужный металл ТОЙ ЖЕ ступени и не
    промахнуться в несуществующий предмет (стальные и серебряные наборы НЕ
    симметричны). Скан один раз, результат кешируется."""
    global _SCAB_SET
    if _SCAB_SET is not None:
        return _SCAB_SET
    s = set()
    for r in ("content", "dlc"):
        base = GAME / r
        for f in sorted(base.rglob("*.bundle")):
            if "~" in str(f) or "Tools" in f.parts:
                continue
            try:
                idx = B.read_index(f)
            except Exception:
                continue
            for e in idx:
                n = str(getattr(e, "name", "")).replace("\\", "/")
                if not n.endswith(".xml") or "items_plus" in n or not B.can_extract(e):
                    continue
                try:
                    t = dec(B.extract(f, e))
                except Exception:
                    continue
                if not t:
                    continue
                for m in re.finditer(r'name="(scabbard_(?:steel|silver)_[A-Za-z0-9_]+)"', t):
                    s.add(m.group(1))
    _SCAB_SET = s
    return s


def live_templates():
    """Имена всех .w2ent сборки. Карточка, чей equip_template сюда не
    попал, надевается НЕВИДИМКОЙ: движку нечего показать (жалоба 15.09 —
    грудник Ворона). Читаются только оглавления бандлов, без распаковки."""
    names = set()
    for r in ("content", "mods", "dlc"):
        for f in sorted((GAME / r).rglob("*.bundle")):
            if ("Tools" in f.parts or "WitcherScriptMerger" in str(f)
                    or f.parent.parent.name.startswith("~")):
                continue
            try:
                idx = B.read_index(f)
            except Exception:
                continue
            for e in idx:
                n = str(getattr(e, "name", "")).replace("\\", "/").lower()
                if n.endswith(".w2ent"):
                    names.add(n.rsplit("/", 1)[-1][:-6])
    return names


LIVE_TPL = set()


def look_alive(card):
    """Есть ли у карточки живой облик. Пустой equip_template не судим —
    такие карточки (жетоны, ингредиенты) ничего и не показывают."""
    m = re.search(r'equip_template\s*=\s*"([^"]*)"', card)
    if not m or not m.group(1).strip():
        return True
    return m.group(1).strip().lower() in LIVE_TPL


def harvest(sample_names):
    """Достаёт карточки-образцы из бандлов: имя -> текст <item>...</item>.

    Одно имя может быть занято НЕСКОЛЬКО раз (у «Raven Armor» — настоящий
    мод и кунтушевый набор внутри W3EE). Берётся не первая попавшаяся, а
    первая С ЖИВЫМ ОБЛИКОМ; карточки-призраки собираются отдельно и
    возвращаются вторым словарём, чтобы вызывающий их выкинул."""
    left = set(sample_names)
    found, ghost = {}, {}
    for r in ("content", "mods", "dlc"):
        base = GAME / r
        for f in sorted(base.rglob("*.bundle")):
            src = f.parent.parent.name
            if "Tools" in f.parts or "WitcherScriptMerger" in str(f) or src.startswith("~"):
                continue
            if not left:
                return found, ghost
            try:
                idx = B.read_index(f)
            except Exception:
                continue
            for e in idx:
                n = str(getattr(e, "name", "")).replace("\\", "/")
                if not n.endswith(".xml") or "items_plus" in n or not B.can_extract(e):
                    continue
                try:
                    t = dec(B.extract(f, e))
                except Exception:
                    continue
                if not t:
                    continue
                for nm in list(left):
                    card = cut_card(t, nm)
                    if not card:
                        continue
                    if look_alive(card):
                        found[nm] = card
                        left.discard(nm)
                    elif nm not in ghost:
                        ghost[nm] = card
    return found, ghost


def cut_card(text, item_name):
    """Вырезает карточку ЦЕЛИКОМ, считая вложенность настоящих тегов <item>.

    Грабли, на которых уже подорвались:
      1. нежадный поиск до первого </item> рвёт карточку пополам — внутри
         попадаются вложенные <item>Geralt Shirt</item> (в bound_items);
      2. простой счёт подстроки "<item" считает и <items> — обёртку списка,
         которая никогда не закроется как </item>;
      3. бывают самозакрывающиеся <item .../> — их считать нельзя вовсе.
    Обрубок ломает ВЕСЬ файл определений, а игра молча не выдаёт ни одного
    предмета мода: ни ошибки, ни строчки в логе. Потому здесь честный разбор.
    """
    m = re.search(r'<item\b[^>]*?name\s*=\s*"%s"' % re.escape(item_name), text)
    if not m:
        return None

    tok = re.compile(r'<item\b|</item\s*>')
    start = m.start()
    depth = 0
    i = start
    while True:
        m2 = tok.search(text, i)
        if not m2:
            return None
        if m2.group(0).startswith("</"):
            depth -= 1
            i = m2.end()
            if depth == 0:
                return text[start:i]
            if depth < 0:
                return None
            continue
        gt = text.find(">", m2.end())          # конец открывающего тега
        if gt < 0:
            return None
        if text[gt - 1] != "/":                # самозакрывающийся не углубляет
            depth += 1
        i = gt + 1


def ability_for(blank_name):
    """Все болванки на одной базовой абилке (классы упразднены желобами)."""
    return ABILITY


def make_card(blank_name, sample_xml, key):
    """Карточка болванки = образец с заменёнными именем, подписями и ПУСТЫМИ статами."""
    c = sample_xml

    # имя
    c = re.sub(r'(name\s*=\s*")[^"]+(")', r"\g<1>%s\g<2>" % blank_name, c, count=1)
    # свои подписи
    c = re.sub(r'(localisation_key_name\s*=\s*")[^"]+(")', r"\g<1>%s\g<2>" % key, c, count=1)
    c = re.sub(r'(localisation_key_description\s*=\s*")[^"]+(")', r"\g<1>%s\g<2>" % DESC_KEY, c, count=1)
    # цена болванки — символическая, настоящая цена в ингредиентах
    c = re.sub(r'(price\s*=\s*")[^"]+(")', r"\g<1>80\g<2>", c, count=1)
    # кована на совесть: 125 прочности против 100 у 595 из 602 мечей игры —
    # часть «капельки за возню» (решение пользователя)
    c = re.sub(r'(initial_durability\s*=\s*")[^"]+(")', r"\g<1>%d\g<2>" % BLANK_DURABILITY, c, count=1)
    c = re.sub(r'(max_durability\s*=\s*")[^"]+(")', r"\g<1>%d\g<2>" % BLANK_DURABILITY, c, count=1)
    # НОЛЬ гнёзд рун (решение пользователя): гнёзда набиваются отдельной штатной
    # механикой игры, болванка приходит голой. Если у образца атрибута нет вовсе —
    # дописываем его явно, чтобы не унаследовать значение по умолчанию.
    if re.search(r'enhancement_slots\s*=\s*"', c):
        c = re.sub(r'(enhancement_slots\s*=\s*")[^"]+(")', r"\g<1>0\g<2>", c, count=1)
    else:
        c = re.sub(r'(<item\b)', r'\g<1> enhancement_slots="0"', c, count=1)

    # ПУСТЫЕ статы: единственное карточное свойство — наше, с качеством НОЛЬ.
    # Совсем без блока нельзя — предметы без свойств рискуют не пережить загрузку
    # (грабли категории upgrade). Ноль, а не единица (решение пользователя):
    # quality — атрибут type="add" и СУММИРУЕТСЯ, своя единица превращала реликт
    # донора (4) в «Ведьмачье снаряжение» (5). Ноль не платит штраф −7 к стопкам
    # урона (case 0 в переключателе W3EE нет), так что голая болванка идёт с 89
    # стопками вместо 82 — принято как честная плата за точную подпись донора.
    c = re.sub(r"<base_abilities>.*?</base_abilities>",
               "<base_abilities>" + P + "<a>" + ability_for(blank_name) + "</a>\n"
               + P + "</base_abilities>", c, count=1, flags=re.S)

    # разбор болванки отдаёт часть материалов
    c = re.sub(r"<recycling_parts>.*?</recycling_parts>",
               "<recycling_parts>" + P + '<parts count="1">Leather straps</parts>\n'
               + P + "</recycling_parts>", c, count=1, flags=re.S)

    # свой ярлык поверх образцовых (образцовые НЕ трогаем — они делают вещь
    # надеваемой). FRG_BlankRaw — только мечам: пул прокрутки слота заготовки
    # в ковке. DoNotEnhance — чтобы Редукс не докинул случайную абилку.
    # теги образца чистим от комплектов и автогена: заготовка обязана быть
    # пустой болванкой, а не «деталью темерского доспеха» (жалоба 05.09)
    _m = re.search(r"<tags>(.*?)</tags>", c, flags=re.S)
    if _m:
        _keep = [x.strip() for x in _m.group(1).split(",") if x.strip()
                 and not is_set_tag(x) and x.strip() != "Autogen"
                 and x.strip() != "mod_legendary"]
        c = re.sub(r"<tags>.*?</tags>",
                   "<tags>" + P + ", ".join(_keep) + "\n" + P + "</tags>",
                   c, count=1, flags=re.S)

    if blank_name in ("FRG Blank Steel Sword", "FRG Blank Silver Sword"):
        c = re.sub(r"(<tags>\s*)", r"\g<1>FRG_Blank, FRG_BlankRaw, DoNotEnhance, ", c, count=1)
    elif blank_name == "FRG Blank Secondary":
        # своя ось прокрутки: в слот заготовки вспомогательной ковки
        c = re.sub(r"(<tags>\s*)", r"\g<1>FRG_Blank, FRG_BlankRawS, DoNotEnhance, ", c, count=1)
    else:
        c = re.sub(r"(<tags>\s*)", r"\g<1>FRG_Blank, DoNotEnhance, ", c, count=1)
    return c


def schem_card(blank_name, key):
    return (
        T * 3 + "<item\n"
        + P + 'name' + P + '="' + blank_name + ' schematic"\n'
        + P + 'category' + P + '="crafting_schematic"\n'
        + P + 'price' + P + '="120"\n'
        + P + 'weight' + P + '="0.1"\n'
        + P + 'stackable' + P + '="100"\n'
        + P + 'grid_size' + P + '="1"\n'
        + P + 'localisation_key_name' + P + '="' + key + '_sc"\n'
        + P + 'localisation_key_description' + P + '="' + SC_DESC_KEY + '"\n'
        + P + 'icon_path' + P + '="icons/inventory/quests/ico_recipe.png"\n'
        + T * 3 + ">\n"
        # FRG_Schem — по нему кузница выдаёт чертежи, не зная имён
        + P + "<tags>" + P + "ReadableItem, mod_crafting, FRG_Schem\n"
        + P + "</tags>\n"
        + T * 3 + "</item>\n"
    )


def schematic(blank_name, ctype, ingredients):
    ing = "".join(T * 5 + '<ingredient quantity="%d" item_name="%s"/>\n' % (q, it)
                  for q, it in ingredients)
    # мечевые заготовки: craftedItem — заглушка категории «Путь клинка»
    # (болванку создаёт наша ветка Craft), рецепт попадает в свою группу
    crafted = blank_name
    for stub, blank, _key in ui_data.BLANK_RESULTS:
        if blank == blank_name:
            crafted = stub
    return (
        T * 2 + "<schematic\n"
        + T * 3 + 'name_name' + P + '="' + blank_name + ' schematic"\n'
        + T * 3 + 'craftedItem_name' + P + '="' + crafted + '"\n'
        + T * 3 + 'craftsmanLevel_name' + P + '="Journeyman"\n'
        + T * 3 + 'craftsmanType_name' + P + '="' + ctype + '"\n'
        + T * 3 + 'price' + P + '="50"\n'
        + T * 2 + ">\n"
        + T * 3 + "<ingredients>\n" + ing + T * 3 + "</ingredients>\n"
        + T * 2 + "</schematic>\n"
    )


def fix_crc(buf):
    b = bytearray(buf)
    o0, c0, _ = struct.unpack_from("<III", b, 40)
    struct.pack_into("<I", b, 48, zlib.crc32(bytes(b[o0:o0 + c0])) & 0xFFFFFFFF)
    o4, c4, _ = struct.unpack_from("<III", b, 40 + 48)
    for i in range(c4):
        p = o4 + i * 24
        _t, _pa, size, off, _z, _c = struct.unpack_from("<6I", b, p)
        struct.pack_into("<I", b, p + 20, zlib.crc32(bytes(b[off:off + size])) & 0xFFFFFFFF)
    struct.pack_into("<I", b, 40 + 48 + 8, zlib.crc32(bytes(b[o4:o4 + c4 * 24])) & 0xFFFFFFFF)
    return bytes(b)


def text_for(key, loc):
    ru = loc == "ru"
    ui = ui_data.ui_text_for(key, ru)
    if ui is not None:
        return ui
    if key in _STAT_KEYS:
        return stat_short(_STAT_KEYS[key], ru)
    if key.startswith("frgar_"):
        # подпись жетона сопротивлений: перечень статов донора человеческим
        # языком (тот же словарь, что у строк-свойств)
        _num = int(key.split("_")[1])
        for _n, _r in ARMOR.items():
            if _r.get("num") == _num:
                return stat_short(_r.get("skel", []), ru)
        return key
    if key == "frgu_b_junk":
        return "[хлам: +1 место]" if ru else "[junk: +1 slot]"
    if key == "frgu_b_plain":
        return "[обычное]" if ru else "[ordinary]"
    if key == "frgu_b_relic":
        return "[РЕЛИКТ: одна на вещь]" if ru else "[RELIC: one per item]"
    if key == "frgu_awake":
        return "(в полную силу — на реликтовой ступени)" if ru else \
               "(full power at the relic tier)"
    if key == DESC_KEY:
        return DESC_RU if ru else DESC_EN
    if key == SC_DESC_KEY:
        return SC_DESC_RU if ru else SC_DESC_EN
    if key == "frgb_probe" or key == "frgb_probe_sc":
        return "Проба интерфейса кузницы" if ru else "Forge UI probe"
    if key == "frgv_frayed":
        return "Обтрёпанный плащ" if ru else "Frayed Coat"
    if key == "frgv_frayedg":
        return "Обтрёпанные перчатки" if ru else "Frayed Gloves"
    if key == "frgv_vagabond":
        return "Одеяние бродяги" if ru else "Vagabond Garb"
    if key in FRGZ_TEXT:
        return FRGZ_TEXT[key][0 if ru else 1]
    if key == "frgv_vesemir":
        return ("Доспех Весемира из Каэр-Морхена" if ru
                else "Vesemir's Kaer Morhen Armour")
    if key == TOKEN_KEY:
        return TOKEN_RU if ru else TOKEN_EN
    if key == TOKEN_DESC_KEY:
        return TOKEN_DESC_RU if ru else TOKEN_DESC_EN
    # имена строк конструктора: RU своё, остальные 16 локалей — EN
    for lid, _redux, _ours, _junk, _attrs, r, e in LINES:
        if key == "frgl_%d" % lid:
            return r if ru else e
    for lid, _redux, _ours, _w, _attrs, r, e in ARMOR_LINES:
        if key == "frgl_%d" % lid:
            return r if ru else e
    for tid, _ours, _attrs, r, e in TEMPER:
        if key == "frgt_%d" % tid:
            return r if ru else e
    for _f in FLAWS:
        if key == "frgf_%d" % _f[0]:
            return _f[2] if ru else _f[3]
        if key == "frgfd_desc_%d" % _f[0]:
            return _f[6] if ru else _f[6]
    for lvl, _ab, _pen, r, e in DMG_MARKS:
        if key == "frgd_%d" % lvl:
            return r if ru else e
    for _nm, _s, ky, _ct, _ing, r, e in BLANKS:
        if ky == key:
            return r if ru else e
        if ky + "_sc" == key:
            return ("Чертёж: " + r) if ru else ("Diagram: " + e)
    return key


head("Болванки кузницы — dlcFRGBlanks")

if game_running():
    say("   ИГРА ЗАПУЩЕНА — закройте её")
    sys.exit(3)
if not TPL.exists():
    say("   [!!] нет образца паспорта %s — сначала setbonus\\build_dlc.py" % TPL)
    sys.exit(1)

say("   Собираю карточки-образцы и доноров из бандлов...")
# образцы нужны КАЖДОМУ броневому донору: облик и защита — разные жетоны
# (05.09), поэтому кованая карточка нужна и тому, у кого своей защиты нет.
# Без этого 64 облика выбирались в окне, а ковка отказывала (жалоба 07.09).
_donor_names = ([d["name"] for d in ui_data.DONORS]
                + [d["name"] for d in ARMOR_DONORS])
LIVE_TPL = live_templates()
say("   [ok] живых обликов в сборке: %d" % len(LIVE_TPL))
samples, ghosts = harvest([s for _n, s, _k, _c, _i, _r, _e in BLANKS] + _donor_names)
# болванка нужна любой ценой: у неё облик не главное — статы и поля
for _n, _s, _k, _c, _i, _r, _e in BLANKS:
    if _s not in samples and _s in ghosts:
        samples[_s] = ghosts.pop(_s)
missing = [s for _n, s, _k, _c, _i, _r, _e in BLANKS if s not in samples]
if missing:
    say("   [!!] образцы не найдены: %s" % ", ".join(missing))
    sys.exit(1)
_missing_donors = [n for n in _donor_names if n not in samples]
say("   [ok] образцов: %d, карточек доноров: %d (не найдено: %d)"
    % (len(samples) - len(_donor_names) + len(_missing_donors),
       len(_donor_names) - len(_missing_donors), len(_missing_donors)))
# ОБЛИК-НЕВИДИМКА ХУЖЕ ОТСУТСТВУЮЩЕГО (жалоба 15.09): донор, чья
# единственная карточка ссылается на несуществующую модель, выбывает
# отовсюду — из кованых карточек, из жетонов и из лавки Элихаля
# в ghosts попадает и тот, у кого позже НАШЛАСЬ живая карточка (у «Raven Armor»
# сперва встречается кунтушевый двойник из W3EE) — такие не выброшены
_ghost_names = sorted(n for n in ghosts if n in _donor_names and n not in samples)
if _ghost_names:
    say("   [!] обликов без моделей — выброшено %d:" % len(_ghost_names))
    for _i2 in range(0, len(_ghost_names), 4):
        say("       " + ", ".join(_ghost_names[_i2:_i2 + 4]))
ui_data.DONORS[:] = [d for d in ui_data.DONORS if d["name"] in samples]
ARMOR_DONORS[:] = [d for d in ARMOR_DONORS if d["name"] in samples]
ELIHAL_LOOKS[:] = [n for n in ELIHAL_LOOKS if n in samples]


def forged_card(donor_name, donor_xml, cat, cross=False):
    """«Кованая» карточка: полная копия карточки донора (модель, иконка,
    анимации, ножны в bound_items), но статы — ПУСТЫЕ, как у болванки.

    МЕТАЛЛ ЗАДАЁТ ЗАГОТОВКА (решение пользователя 22.08): у каждого донора
    ДВЕ версии — родная «FRG Forged X» и кросс «FRG CrossForged X» с
    противоположной категорией (стальной меч с обликом серебряного и
    наоборот). Ковка выбирает версию по категории болванки."""
    c = donor_xml
    out_cat = cat
    prefix = "FRG Forged "
    if cross:
        out_cat = "silversword" if cat == "steelsword" else "steelsword"
        prefix = "FRG CrossForged "
    c = re.sub(r'(name\s*=\s*")[^"]+(")', r"\g<1>%s%s\g<2>" % (prefix, donor_name), c, count=1)
    c = re.sub(r'(category\s*=\s*")[^"]+(")', r"\g<1>%s\g<2>" % out_cat, c, count=1)
    cat = out_cat
    want_metal = "silver" if out_cat == "silversword" else "steel"
    other_slot = "steel_sword_back_slot" if want_metal == "silver" else "silver_sword_back_slot"
    new_slot = "%s_sword_back_slot" % want_metal
    # ГДЕ МЕЧ ВИСИТ НА СПИНЕ — атрибут equip_slot шапки (не модель и не категория;
    # проверено 22.09). Кросс: всегда на сторону НОВОГО металла. Родная карточка:
    # только если у донора стоял слот ЧУЖОГО меча (у W3EE есть «серебряные» мечи на
    # стальной модели); прочие слоты (например axe_back_slot) не трогаем.
    # equip_slot внутри anim_switches — переходы анимаций, металл-нейтральны: не трогаем.
    _slot = re.search(r'equip_slot\s*=\s*"([^"]+)"', c)
    if cross or (_slot and _slot.group(1) == other_slot):
        c = re.sub(r'(equip_slot\s*=\s*")[^"]+(")', r"\g<1>%s\g<2>" % new_slot, c, count=1)
    # НОЖНЫ — по ОПИСАНИЮ предмета (категория + шаблон), а не по имени: у многих
    # мечей ножны зовутся «Long Steel Sword Scabbard», «Sabre Scabbard 02»… (23.09:
    # старый поиск по имени scabbard_steel_* пропускал 200 кросс-карточек из 565).
    # Ножны уже нужной стороны не трогаем; иначе пара того же стиля другого металла
    # → ДВОЙНИК ножен (тот же меш, кости другой стороны) → обычные нужной стороны.

    def _swap_scab(m, _wm=want_metal):
        return "<item>" + _twin_maker().cross_scabbard(m.group(1).strip(), _wm) + "</item>"

    c = re.sub(r'<bound_items>.*?</bound_items>',
               lambda mb: re.sub(r'<item>\s*([^<]+?)\s*</item>', _swap_scab, mb.group(0)),
               c, flags=re.S)
    # ОБЛИК+НОЖНЫ: показ ножен у игрока гейтит swordType в сущности клинка. Если
    # металл МОДЕЛИ донора не совпадает с металлом КАРТОЧКИ (кросс — всегда; у W3EE
    # бывает и в родной: «серебряные» гномьи/краснолюдские на стальной модели) —
    # перенаправляем equip_template на ДВОЙНИКА: оболочка нужного металла + меш
    # донора (правка всей «матрёшки» CR2W). Подробно — forge_twins.py.
    _mt = re.search(r'equip_template\s*=\s*"([^"]+)"', c)
    if _mt and _mt.group(1):
        _em = _twin_maker().entity_metal(_mt.group(1))
        if _em and _em != want_metal:
            _tw = _twin_maker().make(_mt.group(1), want_metal)
            if _tw:
                _twn, _twb = _tw
                _TWINS[_twn] = _twb
                c = re.sub(r'(equip_template\s*=\s*")[^"]+(")',
                           r"\g<1>%s\g<2>" % _twn, c, count=1)
    # имя вещи остаётся донорским (localisation_key_name не трогаем): игрок
    # ВОССОЗДАЛ Эмменталь; описание — своё
    c = re.sub(r'(localisation_key_description\s*=\s*")[^"]+(")',
               r"\g<1>frgu_forged_desc\g<2>", c, count=1)
    c = re.sub(r'(price\s*=\s*")[^"]+(")', r"\g<1>80\g<2>", c, count=1)
    if re.search(r'enhancement_slots\s*=\s*"', c):
        c = re.sub(r'(enhancement_slots\s*=\s*")[^"]+(")', r"\g<1>0\g<2>", c, count=1)
    c = re.sub(r'(initial_durability\s*=\s*")[^"]+(")', r"\g<1>%d\g<2>" % BLANK_DURABILITY, c, count=1)
    c = re.sub(r'(max_durability\s*=\s*")[^"]+(")', r"\g<1>%d\g<2>" % BLANK_DURABILITY, c, count=1)
    # статы: только наша реликтовая подпись — всё боевое кладут жетоны
    c = re.sub(r"<base_abilities>.*?</base_abilities>",
               "<base_abilities>" + P + "<a>FRG Forged _Stats</a>\n"
               + P + "</base_abilities>", c, count=1, flags=re.S)
    # теги СВОИ: донорские несут эффекты (SwordGasEffect дал бы облако бесплатно,
    # мимо жетона) и сеты (SetBonusPiece вписал бы клинок в чужой сет)
    if cat == "silversword":
        tags = "PlayerSilverWeapon, Weapon, sword1h, 1handedWeapon, mod_weapon, FRG_Blank, FRG_Forge, DoNotEnhance"
    else:
        tags = "PlayerSteelWeapon, Weapon, sword1h, 1handedWeapon, mod_weapon, FRG_Blank, FRG_Forge, DoNotEnhance"
    c = re.sub(r"<tags>.*?</tags>",
               "<tags>" + P + tags + "\n" + P + "</tags>", c, count=1, flags=re.S)
    c = re.sub(r"<recycling_parts>.*?</recycling_parts>",
               "<recycling_parts>" + P + '<parts count="1">%s</parts>\n' % (
                   "FRG Blank Silver Sword" if cat == "silversword" else "FRG Blank Steel Sword")
               + P + "</recycling_parts>", c, count=1, flags=re.S)
    return c


def forged_side_card(donor_name, donor_xml):
    """Кованое вспомогательное: копия карточки донора (модель, анимации,
    КАТЕГОРИЯ — хват и махи задаёт она), статы пустые, теги донора
    фильтруются (эффекты и сеты не должны ехать даром)."""
    c = donor_xml
    c = re.sub(r'(name\s*=\s*")[^"]+(")', r"\g<1>FRG Forged %s\g<2>" % donor_name, c, count=1)
    c = re.sub(r'(localisation_key_description\s*=\s*")[^"]+(")',
               r"\g<1>frgu_forged_desc\g<2>", c, count=1)
    c = re.sub(r'(price\s*=\s*")[^"]+(")', r"\g<1>80\g<2>", c, count=1)
    if re.search(r'enhancement_slots\s*=\s*"', c):
        c = re.sub(r'(enhancement_slots\s*=\s*")[^"]+(")', r"\g<1>0\g<2>", c, count=1)
    c = re.sub(r'(initial_durability\s*=\s*")[^"]+(")', r"\g<1>%d\g<2>" % BLANK_DURABILITY, c, count=1)
    c = re.sub(r'(max_durability\s*=\s*")[^"]+(")', r"\g<1>%d\g<2>" % BLANK_DURABILITY, c, count=1)
    c = re.sub(r"<base_abilities>.*?</base_abilities>",
               "<base_abilities>" + P + "<a>FRG Forged _Stats</a>\n"
               + P + "</base_abilities>", c, count=1, flags=re.S)
    m = re.search(r"<tags>(.*?)</tags>", c, flags=re.S)
    old_tags = [x.strip() for x in (m.group(1) if m else "").split(",") if x.strip()]
    keep = [x for x in old_tags
            if not x.endswith("Effect")
            and x not in ("Autogen", "Quest", "NoDrop", "NoShow", "DoNotEnhance")
            and not is_set_tag(x)]
    keep += ["mod_weapon", "FRG_Blank", "FRG_Forge", "DoNotEnhance"]
    c = re.sub(r"<tags>.*?</tags>",
               "<tags>" + P + ", ".join(keep) + "\n" + P + "</tags>",
               c, count=1, flags=re.S)
    c = re.sub(r"<recycling_parts>.*?</recycling_parts>",
               "<recycling_parts>" + P + '<parts count="1">FRG Blank Secondary</parts>\n'
               + P + "</recycling_parts>", c, count=1, flags=re.S)
    return c


def forged_armor_card(donor_name, donor_xml, cat):
    """Кованая броня: копия карточки донора, статы пустые, теги донора
    ФИЛЬТРУЮТСЯ (сет-принадлежность и эффекты не должны ехать даром),
    вес-класс (LightArmor/...) сохраняется — он рулит пулами и строками."""
    c = donor_xml
    c = re.sub(r'(name\s*=\s*")[^"]+(")', r"\g<1>FRG Forged %s\g<2>" % donor_name, c, count=1)
    c = re.sub(r'(localisation_key_description\s*=\s*")[^"]+(")',
               r"\g<1>frgu_forged_desc\g<2>", c, count=1)
    c = re.sub(r'(price\s*=\s*")[^"]+(")', r"\g<1>80\g<2>", c, count=1)
    if re.search(r'enhancement_slots\s*=\s*"', c):
        c = re.sub(r'(enhancement_slots\s*=\s*")[^"]+(")', r"\g<1>0\g<2>", c, count=1)
    c = re.sub(r'(initial_durability\s*=\s*")[^"]+(")', r"\g<1>%d\g<2>" % BLANK_DURABILITY, c, count=1)
    c = re.sub(r'(max_durability\s*=\s*")[^"]+(")', r"\g<1>%d\g<2>" % BLANK_DURABILITY, c, count=1)
    c = re.sub(r"<base_abilities>.*?</base_abilities>",
               "<base_abilities>" + P + "<a>FRG Forged _Stats</a>\n"
               + P + "</base_abilities>", c, count=1, flags=re.S)
    m = re.search(r"<tags>(.*?)</tags>", c, flags=re.S)
    old_tags = [t.strip() for t in (m.group(1) if m else "").split(",") if t.strip()]
    # вес-теги ОБЛИКА вычищаются: вес-класс задаёт ЖЕТОН ЗАЩИТЫ (экземплярным
    # тегом) — «облик от медведя, броня и класс от кота»
    keep = [t for t in old_tags
            if not t.endswith("Effect")
            and t not in ("Autogen", "Quest", "NoDrop", "NoShow", "DoNotEnhance",
                          "LightArmor", "MediumArmor", "HeavyArmor")
            and not is_set_tag(t)]
    keep += ["FRG_Blank", "FRG_Forge", "DoNotEnhance"]
    c = re.sub(r"<tags>.*?</tags>",
               "<tags>" + P + ", ".join(keep) + "\n" + P + "</tags>",
               c, count=1, flags=re.S)
    c = re.sub(r"<recycling_parts>.*?</recycling_parts>",
               "<recycling_parts>" + P + '<parts count="1">%s</parts>\n' % _BLANK_OF[cat]
               + P + "</recycling_parts>", c, count=1, flags=re.S)
    return c


def armor_shape_cards():
    """Жетоны обликов брони: категорийная ось, иконка и лок-имя донора."""
    out = []
    for d in ARMOR_DONORS:
        icon = d.get("icon") or "icons/inventory/quests/ico_recipe.png"
        lockey = d.get("lockey") or "frgl_token"
        _sc = ui_data._tok_card("FRG Shape " + d["name"], lockey, icon,
                                "mod_crafting, " + _SHAPE_TAG[d["cat"]])
        # цена жетона облика — базовая (25): «сейчас дорого очень» (05.09)
        out.append(_sc)
    return "".join(out)


def armor_def_cards():
    """Жетоны ЗАЩИТЫ брони: значение брони и вес-класс донора (только у кого
    есть защита). Отдельная ось от облика — кросс-сборка «вид/класс»."""
    out = []
    for d in ARMOR_DONORS:
        if d["name"] not in ARMOR:
            continue
        icon = d.get("icon") or "icons/inventory/quests/ico_recipe.png"
        lockey = d.get("lockey") or "frgl_token"
        out.append(ui_data._tok_card("FRG Def " + d["name"], lockey, icon,
                                     "mod_crafting, " + _DEF_TAG[d["cat"]]).replace(
            'frgu_tok_desc', 'frgu_def_desc', 1))
    return "".join(out)


def armor_res_cards():
    """Жетоны СОПРОТИВЛЕНИЙ брони: резисты и повадки веса донора."""
    out = []
    for d in ARMOR_DONORS:
        if d["name"] not in ARMOR or not ARMOR[d["name"]].get("skel"):
            continue
        icon = d.get("icon") or "icons/inventory/quests/ico_recipe.png"
        lockey = d.get("lockey") or "frgl_token"
        out.append(ui_data._tok_card("FRG Res " + d["name"], lockey, icon,
                                     "mod_crafting, " + _RES_TAG[d["cat"]]).replace(
            'frgu_tok_desc', 'frgu_res_desc', 1))
    return "".join(out)


cards = []
for nm, sample, key, _ct, _ing, _r, _e in BLANKS:
    cards.append(make_card(nm, samples[sample], key))
for d in ui_data.DONORS:
    if d["name"] in samples:
        if d["cat"] in ui_data.SIDE_CATS:
            cards.append(forged_side_card(d["name"], samples[d["name"]]))
            continue
        cards.append(forged_card(d["name"], samples[d["name"]], d["cat"]))
        cards.append(forged_card(d["name"], samples[d["name"]], d["cat"], cross=True))
# двойники ножен кросс-мечей (новые предметы-ножны) — рядом с кованными картами
if _TWIN_MAKER_INST is not None:
    cards.extend(_TWIN_MAKER_INST.scab_defs_new)
for d in ARMOR_DONORS:
    if d["name"] in samples:
        _fc = forged_armor_card(d["name"], samples[d["name"]], d["cat"])
        if d["name"] in _LOOK_LOCKEY:
            _fc = re.sub(r'(localisation_key_name\s*=\s*")[^"]+(")',
                         r"\g<1>%s\g<2>" % _LOOK_LOCKEY[d["name"]], _fc, count=1)
        cards.append(_fc)

def line_abilities():
    """Абилки строк: 26 пулов FRG_L_* + 4 клейма FRG_T_* + нарезка FRG_C_*.

    Только min, без max: движку нечего роллить, сейв-скам мёртв. Тип 'effect'
    (PoisonEffect и родня) пишется is_ability="true" — «свойство, дающее
    свойство», как в исходных карточках Редукса."""
    def rows_of(attrs):
        rows = ""
        for a, t, v in attrs:
            if t == "effect":
                rows += P + '<%s is_ability="true"/>\n' % a
            else:
                rows += P + '<%s type="%s" min="%s"/>\n' % (a, t, "%g" % v)
        return rows

    out = []
    for _lid, _redux, ours, _junk, attrs, _ru, _en in LINES:
        out.append(T * 3 + '<ability name="%s">\n' % ours
                   + P + "<tags></tags>\n" + rows_of(attrs)
                   + T * 3 + "</ability>\n")
    for _tid, ours, attrs, _ru, _en in TEMPER:
        out.append(T * 3 + '<ability name="%s">\n' % ours
                   + P + "<tags></tags>\n" + rows_of(attrs)
                   + T * 3 + "</ability>\n")
    for _f in FLAWS:
        out.append(T * 3 + '<ability name="%s">\n' % _f[1]
                   + P + "<tags></tags>\n" + rows_of(_f[4])
                   + T * 3 + "</ability>\n")
    # вампиризм, вшитый в чары «Тёмное проклятье» (ГД 24.09): сами чары W3EE —
    # чистый минус, скрипт кузницы вешает эту абилку на клинок с проклятьем
    out.append(T * 3 + '<ability name="FRG_CurseVamp">\n'
               + P + "<tags></tags>\n" + rows_of([("lifesteal", "add", 0.1)])
               + T * 3 + "</ability>\n")
    for c in CUT:
        out.append(T * 3 + '<ability name="%s">\n' % c["ability"]
                   + P + "<tags></tags>\n" + rows_of(c["stats"])
                   + T * 3 + "</ability>\n")
    return "".join(out)


def cut_token_cards():
    """Жетоны нарезанных строк: иконка и ИМЯ донора (его лок-ключ), статы
    доскажет тултип-обёртка."""
    out = []
    for c in CUT:
        icon = c.get("icon") or "icons/inventory/quests/ico_recipe.png"
        lockey = c.get("lockey") or TOKEN_KEY
        out.append(
            T * 3 + "<item\n"
            + P + 'name' + P + '="' + c["card"] + '"\n'
            + P + 'category' + P + '="misc"\n'
            + P + 'price' + P + '="25"\n'
            + P + 'weight' + P + '="0.01"\n'
            + P + 'stackable' + P + '="1"\n'
            + P + 'grid_size' + P + '="1"\n'
            + P + 'localisation_key_name' + P + '="' + lockey + '"\n'
            + P + 'localisation_key_description' + P + '="' + TOKEN_DESC_KEY + '"\n'
            + P + 'icon_path' + P + '="' + icon + '"\n'
            + T * 3 + ">\n"
            + P + "<tags>" + P + "mod_crafting, FRG_LineTok\n"
            + P + "</tags>\n"
            + T * 3 + "</item>\n"
        )
    return "".join(out)


def token_card():
    """Жетон строки. stackable=1 (НЕ стакается): жетоны различаются
    модификатором FRG_Line, стак бы их слил в неразличимую кучу."""
    return (
        T * 3 + "<item\n"
        + P + 'name' + P + '="' + TOKEN_ITEM + '"\n'
        + P + 'category' + P + '="misc"\n'
        + P + 'price' + P + '="25"\n'
        + P + 'weight' + P + '="0.01"\n'
        + P + 'stackable' + P + '="1"\n'
        + P + 'grid_size' + P + '="1"\n'
        + P + 'localisation_key_name' + P + '="' + TOKEN_KEY + '"\n'
        + P + 'localisation_key_description' + P + '="' + TOKEN_DESC_KEY + '"\n'
        + P + 'icon_path' + P + '="icons/inventory/quests/ico_recipe.png"\n'
        + T * 3 + ">\n"
        + P + "<tags>" + P + "mod_crafting, FRG_LineToken\n"
        + P + "</tags>\n"
        + T * 3 + "</item>\n"
    )


# Защита брони доноров (карточный armor; автоген брони в W3EE выключен) +
# снимаемые тир-налоги и пул-строки брони.
def armor_abilities():
    out = []
    for donor, rec in sorted(ARMOR.items(), key=lambda kv: kv[1]["num"]):
        # ОДИН ЖЕТОН (возврат 15.09 по требованию ГД): в Redux показатель
        # брони и сопротивления неразрывны — тяжёлая броня это минус
        # скорость, большая защита И большие резисты. Всё едет одной
        # абилкой: защита, резисты, повадки веса.
        skel = rec.get("skel", [])
        out.append(T * 3 + '<ability name="%s">\n' % armor_ability(donor)
                   + T * 4 + "<tags></tags>\n"
                   + T * 4 + '<armor type="base" min="%g"/>\n' % rec["armor"]
                   + "".join(T * 4 + '<%s type="%s" min="%g"/>\n' % (a, t, v)
                               for a, t, v in skel)
                   + T * 3 + "</ability>\n")
        # старый жетон сопротивлений остаётся ОБЪЯВЛЕННЫМ, но ПУСТЫМ: у
        # вещей, выкованных до слияния, он висит в списке свойств —
        # убрать совсем значит потерять их (движок не найдёт абилку),
        # оставить с числами значит посчитать резисты дважды
        if skel:
            out.append(T * 3 + '<ability name="%s">\n' % armor_res_ability(donor)
                       + T * 4 + "<tags></tags>\n"
                       + T * 3 + "</ability>\n")
    for _t, ab, pen in ARMOR_TIER_PENALTY:
        out.append(T * 3 + '<ability name="%s">\n' % ab
                   + T * 4 + "<tags></tags>\n"
                   + T * 4 + '<armor type="mult" min="%g"/>\n' % pen
                   + T * 3 + "</ability>\n")
    for lid, _redux, ours, _w, attrs, _ru, _en in ARMOR_LINES:
        rows = "".join(T * 4 + '<%s type="%s" min="%g"/>\n' % (a, t, v)
                       for a, t, v in attrs)
        out.append(T * 3 + '<ability name="%s">\n' % ours
                   + T * 4 + "<tags></tags>\n" + rows
                   + T * 3 + "</ability>\n")
    return "".join(out)


def armor_pool_token_cards():
    """Жетоны пул-строк брони: frg_line_<id>, лок frgl_<id>."""
    out = []
    for lid, _redux, _ours, _w, _attrs, _ru, _en in ARMOR_LINES:
        out.append(ui_data._tok_card("frg_line_%d" % lid, "frgl_%d" % lid,
                                     "icons/inventory/quests/ico_recipe.png",
                                     "mod_crafting, FRG_LineTok"))
    return "".join(out)


# Плоские урон-добавки доноров: чем реликты различаются по урону с руки.
# Вешаются на клинок реликтовым улучшением (жетон урона несёт весь урон).
def flat_abilities():
    out = []
    for donor, rec in sorted(FLAT.items(), key=lambda kv: kv[1]["num"]):
        rows = "".join(T * 4 + '<%s type="%s" min="%g"/>\n' % (a, t, v)
                       for a, t, v in rec["rows"])
        out.append(T * 3 + '<ability name="%s">\n' % flat_ability(donor)
                   + T * 4 + "<tags></tags>\n" + rows
                   + T * 3 + "</ability>\n")
    return "".join(out)


# Желоба под гравировку — снимаемые уровни урон-штрафа (не карточные:
# ставятся и снимаются у мастера, слоты пересчитываются от уровня).
def groove_abilities():
    out = []
    for _lvl, ab, pen, _ru, _en in DMG_MARKS:
        out.append(T * 3 + '<ability name="%s">\n' % ab
                   + T * 4 + "<tags></tags>\n"
                   + T * 4 + '<attack_power type="mult" min="%g"/>\n' % pen
                   + T * 3 + "</ability>\n")
    return "".join(out)


# Ступени «Пути клинка»: каждая Q-абилка добавляет +1 к качеству (add
# суммируется). Урон растёт РОДНОЙ формулой качества W3EE (штраф стопок
# -7/-5/-3/0), подпись и цвет пересчитываются движком.
def tier_abilities():
    out = []
    for _t, ab, _d, _m, _ru, _en in TIERS:
        if not ab:
            continue
        out.append(T * 3 + '<ability name="%s">\n' % ab
                   + T * 4 + "<tags></tags>\n"
                   + T * 4 + '<quality type="add" min="1" max="1"/>\n'
                   + T * 3 + "</ability>\n")
    return "".join(out)


ABILITIES = (
    T * 2 + "<abilities>\n"
    + T * 3 + '<ability name="' + ABILITY + '">\n'
    + T * 4 + "<tags></tags>\n"
    + T * 4 + '<quality type="add" min="0" max="0"/>\n'
    + T * 3 + "</ability>\n"
    # кованый клинок РОЖДАЕТСЯ «Обычным» (кач. 1) и растёт ступенями до
    # «Реликта» (1 + три Q-абилки = 4). Существующие клинки без ступеней
    # мигрируют на загрузке (FRG_MigrateForged в скрипте).
    + T * 3 + '<ability name="FRG Forged _Stats">\n'
    + T * 4 + "<tags></tags>\n"
    + T * 4 + '<quality type="add" min="1" max="1"/>\n'
    + T * 3 + "</ability>\n"
    + tier_abilities()
    + flat_abilities()
    + armor_abilities()
    + groove_abilities()
    + line_abilities()
    + T * 2 + "</abilities>\n"
)

# Смок-тест этапа 4 (конструктор в окне кузнеца): схема с ПЯТЬЮ ингредиентами.
# Проверяет главную догадку ТЗ — сетка swf рисует 5 квадратиков, тултип и
# прокрутка работают в каждом. Результат безвреден (болванка). Убрать после
# проверки, когда встанет настоящий якорь «Кованый клинок».
PROBE_SCHEM = (
    T * 2 + "<schematic\n"
    + T * 3 + 'name_name' + P + '="FRG UI Probe schematic"\n'
    + T * 3 + 'craftedItem_name' + P + '="FRG Blank Steel Sword"\n'
    + T * 3 + 'craftsmanLevel_name' + P + '="Journeyman"\n'
    + T * 3 + 'craftsmanType_name' + P + '="Smith"\n'
    + T * 3 + 'price' + P + '="1"\n'
    + T * 2 + ">\n"
    + T * 3 + "<ingredients>\n"
    + T * 5 + '<ingredient quantity="1" item_name="Steel ingot"/>\n'
    + T * 5 + '<ingredient quantity="1" item_name="Leather straps"/>\n'
    + T * 5 + '<ingredient quantity="1" item_name="Timber"/>\n'
    + T * 5 + '<ingredient quantity="1" item_name="Linen"/>\n'
    + T * 5 + '<ingredient quantity="1" item_name="Iron ingot"/>\n'
    + T * 3 + "</ingredients>\n"
    + T * 2 + "</schematic>\n"
)

# иконки доноров для жетонов конструктора
_donor_icons = {d["name"]: d.get("icon", "") for d in ui_data.DONORS}

ITEMXML = (
    '<?xml version="1.0" encoding="UTF-16"?>\n<redxml>\n'
    + T + "<definitions>\n" + ABILITIES + T * 2 + "<items>\n"
    + "\n".join(cards) + "\n"
    + "".join(schem_card(nm, ky) for nm, _s, ky, _c, _i, _r, _e in BLANKS)
    + schem_card("FRG ForgeBlade", "frgu_forged")
    + schem_card("FRG ForgeSide", "frgu_fside")
    + schem_card("FRG CopyLook", "frgu_copylook")
    + schem_card("FRG Reskin", "frgu_reskin")
    + "".join(schem_card(_sc.replace(" schematic", ""), _k)
              for _sc, _ct, _slot, _k, _res, _ic in ui_data.RESKIN_ARMOR)
    + "".join(schem_card(_sc.replace(" schematic", ""), _k)
              for _sc, _ct, _slot, _k, _res, _ic in ui_data.MEASURE_SCHEMS)
    + schem_card("FRG Engrave", "frgu_engrave")
    + schem_card("FRG Enchant", "frgu_enchant")
    + schem_card("FRG Name", "frgu_name")
    + "".join(schem_card(sc.replace(" schematic", ""), key)
              for sc, _b, _p, _dp, _s, key, _rp in ui_data.ARMOR_FORGE)
    + token_card()
    + cut_token_cards()
    + armor_shape_cards()
    + armor_def_cards()
    + armor_res_cards()
    + armor_pool_token_cards()
    + ui_data.ui_cards(_donor_icons)
    # мини-пруф 22.09 (маркер frg_swtest) из релиза убран 26.09
    + T * 2 + "</items>\n" + T + "</definitions>\n"
    + T + "<custom>\n" + T * 2 + "<crafting_schematics>\n"
    + "".join(schematic(nm, ct, ing) for nm, _s, _k, ct, ing, _r, _e in BLANKS)
    + ui_data.anchor_schematic()
    + T * 2 + "</crafting_schematics>\n" + T + "</custom>\n</redxml>\n"
)

EMPTY_XML = ('<?xml version="1.0" encoding="UTF-16"?>\r\n<redxml>\r\n\t<definitions>\r\n'
             '\t\t<items>\r\n\t\t</items>\r\n\t</definitions>\r\n</redxml>\r\n')

# ВРЕМЕННО (мини-пруф 22.09): даём ванильному Аэрондиту (серебряный меч) вариант
# со стальной моделью Дикой Охоты. Пока надет маркер frg_swtest — движок должен
# нарисовать у Аэрондита стальную модель В СЕРЕБРЯНОЙ позиции (проверка кросс-металла).
TEST_EXTS = ('<?xml version="1.0" encoding="UTF-16"?>\r\n<redxml>\r\n\t<definitions>\r\n'
             '\t\t<items_extensions>\r\n'
             '\t\t\t<item_extension name="Aerondight">\r\n'
             '\t\t\t\t<variants>\r\n'
             '\t\t\t\t\t<variant equip_template="wildhunt_sword_lvl1">\r\n'
             '\t\t\t\t\t\t<item>frg_swtest</item>\r\n'
             '\t\t\t\t\t</variant>\r\n'
             '\t\t\t\t</variants>\r\n'
             '\t\t\t</item_extension>\r\n'
             '\t\t</items_extensions>\r\n'
             '\t</definitions>\r\n</redxml>\r\n')

# Проверка разметки ДО упаковки: обрубленный <item> ломает весь файл целиком,
# и игра просто не выдаёт НИ ОДНОГО предмета мода — без ошибки и без лога.
try:
    import xml.etree.ElementTree as _ET
    _ET.fromstring(ITEMXML)
    say("   [ok] разметка XML проверена")
except Exception as _e:
    say("   [!!] XML СЛОМАН, не пакую: %s" % _e)
    sys.exit(1)

# ---- паспорт ------------------------------------------------------------------
passport = TPL.read_bytes()
for old, new in PATCH:
    if len(old) != len(new):
        say("   [!!] длины не совпадают: %r -> %r" % (old, new))
        sys.exit(1)
    passport = passport.replace(old, new)
if re.search(rb"vagabond", passport):
    say("   [!!] остались следы образца")
    sys.exit(1)
passport = fix_crc(passport)
say("   [ok] паспорт готов, %d Б" % len(passport))

# ---- дерево -------------------------------------------------------------------
if RAW.exists():
    shutil.rmtree(RAW)
RAW.mkdir(parents=True)
(RAW / "strings.list").write_bytes(b'{\n    "files": []\n}')
base = RAW / "dlc" / MOUNT
base.mkdir(parents=True)
(base / (MOUNT + ".reddlc")).write_bytes(passport)

payload = ITEMXML.replace("\n", "\r\n").encode("utf-16")
def _loot_rows(names):
    """Строки товара: жетон облика, всегда в наличии.

    chance="-1" — «гарантированно», ровно то значение, с которым в этой же
    лавке лежат 128 записей W3EE. Уровни 0/0 — без ограничений."""
    return "".join('\t\t\t\t<loot_entry name="FRG Shape %s" quantity_min="1" '
                   'quantity_max="1" player_level_min="0" player_level_max="0" '
                   'chance="-1" />\r\n' % n for n in names)


def shops_xml(sections):
    """Файл лавок: у каждой свой прилавок. Жетон, которого нет в карточках,
    в лавку не попадает — иначе торговец ссылается в пустоту."""
    body = ""
    for loot, names in sections:
        if not loot or not names:
            continue
        rows = sorted(n for n in set(names) if n in samples)
        # общий прилавок — как было (у Элихаля это работает)
        body += ('\t\t\t<loot name="%s">\r\n' % loot
                 + _loot_rows(rows) + '\t\t\t</loot>\r\n')
        # ...и ЗЕРКАЛО со своим потолком: его кузница доливает торговцу
        # напрямую, минуя и чужую очередь за слоты, и запёкшийся сейв
        body += ('\t\t\t<loot name="%s" player_level_min="0" '
                 'player_level_max="0" quantity_min="%d" quantity_max="%d" '
                 'chance="-1">\r\n' % (MIRROR[loot], len(rows), len(rows))
                 + _loot_rows(rows) + '\t\t\t</loot>\r\n')
    return ('<?xml version="1.0" encoding="UTF-16"?>\r\n<redxml>\r\n'
            '\t<definitions>\r\n\t\t<loot_definitions>\r\n'
            + body + '\t\t</loot_definitions>\r\n'
            '\t</definitions>\r\n</redxml>\r\n')


_ARMOR_LOOKS = set(ELIHAL_LOOKS) | SKIN_ONLY_NAMES
# у гроссмейстера — ВСЁ: и клинки, и броня (уточнение ГД 15.09)
SHOPS = [("_store__Elihal_Apparel_Shop", _ARMOR_LOOKS),
         (GM_SHOP, _ARMOR_LOOKS | set(GM_LOOKS))]
ELIHAL_XML = shops_xml(SHOPS)
for _loot, _names in SHOPS:
    if _loot:
        say("   [ok] лавка %s: %d жетонов"
            % (_loot, len([n for n in set(_names) if n in samples])))
empty = EMPTY_XML.encode("utf-16")
shop_payload = ELIHAL_XML.encode("utf-16")
for branch in ("items", "items_plus"):
    d = base / "data" / "gameplay" / branch
    d.mkdir(parents=True)
    (d / ITEMS).write_bytes(payload)
    (d / SHOP).write_bytes(shop_payload)
    # мини-пруф 22.09 (вариант Аэрондита) убран 26.09: расширение ПУСТОЕ в
    # обеих ветках — чужую ванильную карточку релиз не трогает
    (d / EXTS).write_bytes(empty)
(base / "data" / "items").mkdir(parents=True)
(base / "data" / "items" / "readme.txt").write_bytes(b"placeholder\n")
say("   [ok] карточки: %d болванок + %d чертежей, %d Б" % (len(BLANKS), len(BLANKS), len(payload)))

# ---- двойники кросс-обликов (ножны) -------------------------------------------
# Сущности-двойники кладём в дерево игры по depot-пути items/weapons/swords/frg/,
# чтобы equip_template кросс-карточек их резолвил. RAW-корень (не под dlc/MOUNT),
# как обычные ассеты (проверено мини-пруфом modFRGScabTest).
if _TWINS:
    tw_dir = RAW / "items" / "weapons" / "swords" / "frg"
    tw_dir.mkdir(parents=True, exist_ok=True)
    for _twn, _twb in _TWINS.items():
        (tw_dir / (_twn + ".w2ent")).write_bytes(_twb)
    # волна 2: скопированные меши (геометрия донора на новый путь длины оболочки)
    _extra = getattr(_twin_maker(), "extra", {})
    for _dp, _mb in _extra.items():
        _p = RAW / _dp.replace("/", os.sep)
        _p.parent.mkdir(parents=True, exist_ok=True)
        _p.write_bytes(_mb)
    _tm = _twin_maker()
    say("   [ok] двойников клинков: %d; ножны кросс-мечей: пара %d, двойник %d, запас %d; файлов ножен %d; сбоев %s"
        % (len(_TWINS),
           sum(1 for v in _tm.scab_log.values() if v.startswith("пара")),
           sum(1 for v in _tm.scab_log.values() if v.startswith("двойник")),
           sum(1 for v in _tm.scab_log.values() if v.startswith("запас")),
           len(_tm.extra), dict((k, v) for k, v in _tm.stats.items() if k != "ok" and v)))

# ---- подписи ------------------------------------------------------------------
keys = ([ky for _n, _s, ky, _c, _i, _r, _e in BLANKS]
        + [ky + "_sc" for _n, _s, ky, _c, _i, _r, _e in BLANKS]
        + [DESC_KEY, SC_DESC_KEY, TOKEN_KEY, TOKEN_DESC_KEY, "frgb_probe", "frgb_probe_sc"]
        + ["frgl_%d" % lid for lid, _r, _o, _j, _a, _ru, _en in LINES]
        + ["frgl_%d" % lid for lid, _r, _o, _w, _a, _ru, _en in ARMOR_LINES]
        + sorted(_STAT_KEYS)
        + ["frgu_b_junk", "frgu_b_relic", "frgu_b_plain", "frgu_awake"]
        + ["frgar_%d" % _r["num"] for _n, _r in sorted(ARMOR.items(),
                                                       key=lambda kv: kv[1]["num"])
           if _r.get("skel")]
        + ["frgv_frayed", "frgv_frayedg", "frgv_vagabond", "frgv_vesemir"]
        + list(FRGZ_TEXT.keys())
        + ["frgt_%d" % tid for tid, _o, _a, _ru, _en in TEMPER]
        + ["frgf_%d" % _f[0] for _f in FLAWS]
        + ["frgd_%d" % lvl for lvl, _ab, _p, _ru, _en in DMG_MARKS]
        + ui_data.ui_loc_keys())
base_id = int("211%04d000" % IDSPACE)
if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir(parents=True)
ok = 0
for loc in LOCALES:
    rows = [";meta[language=%s]" % META_LANG.get(loc, loc), "; id      |key(hex)|key(str)| text"]
    for i, k in enumerate(keys):
        rows.append("%d|        |%s|%s" % (base_id + i, k, " ".join(text_for(k, loc).split())))
    csv = WORK / ("frgb_%s.csv" % loc)
    csv.write_bytes(("\r\n".join(rows) + "\r\n").encode("utf-8"))
    # ключей больше 1000: id переливаются в соседние id-space 4481-4482
    # (проверены сканом — свободны). Force-флаг ставится ВМЕСТО --id-space:
    # вместе они падают той же проверкой.
    subprocess.run([str(ENC), "--encode", str(csv),
                    "--force-ignore-id-space-check-i-know-what-i-am-doing"],
                   capture_output=True, cwd=str(WORK))
    if Path(str(csv) + ".w3strings").exists():
        ok += 1
say("   [ok] подписи: %d локалей из %d" % (ok, len(LOCALES)))

# ---- упаковка -----------------------------------------------------------------
content = DLC / "content"
if content.exists():
    shutil.rmtree(content)
content.mkdir(parents=True)
r = subprocess.run([str(WCC), "pack", "-dir=" + str(RAW), "-outdir=" + str(content)],
                   capture_output=True, text=True, timeout=300, cwd=str(WCC.parent))
if not (content / "blob0.bundle").exists():
    say("   [!!] pack не собрал (код %d)" % r.returncode)
    for line in ((r.stdout or "") + (r.stderr or "")).splitlines()[-8:]:
        say("      " + line.strip()[:110])
    sys.exit(1)
subprocess.run([str(WCC), "metadatastore", "-path=" + str(content)],
               capture_output=True, text=True, timeout=300, cwd=str(WCC.parent))
for loc in LOCALES:
    src = WORK / ("frgb_%s.csv.w3strings" % loc)
    if src.exists():
        shutil.copyfile(src, content / ("%s.w3strings" % loc))
say("   [ok] blob0.bundle %d Б, файлов %d"
    % ((content / "blob0.bundle").stat().st_size,
       sum(1 for _ in DLC.rglob("*") if _.is_file())))

# ---- ревизия витрин ------------------------------------------------------------
# Кузница доливает торговцу своё зеркало один раз НА РЕВИЗИЮ состава: сменился
# список жетонов — сменилась ревизия, и уже встреченный торговец (его полка
# живёт в сейве) получит новые при следующем открытии лавки. Ревизию
# вписывает в скрипт build_lab.py — после build_blanks пересобрать и его.
# Пишется только здесь, после удачной упаковки DLC.
import hashlib as _hl
_rev = {}
for _loot, _names in SHOPS:
    if _loot:
        _rows = sorted(n for n in set(_names) if n in samples)
        _rev[MIRROR[_loot]] = _hl.sha1("\n".join(_rows).encode("utf-8")).hexdigest()[:8]
_stock_list = {}
for _loot, _names in SHOPS:
    if _loot:
        _stock_list[MIRROR[_loot]] = ["FRG Shape " + _n
                                     for _n in sorted(set(_names)) if _n in samples]
(Path(__file__).parent / "stock_list.json").write_text(
    _json.dumps(_stock_list, ensure_ascii=False, indent=1), encoding="utf-8")
say("   [ok] список долива: %s"
    % ", ".join("%s=%d" % (k, len(v)) for k, v in sorted(_stock_list.items())))
(Path(__file__).parent / "stock_rev.json").write_text(
    _json.dumps(_rev, indent=1, sort_keys=True), encoding="utf-8")
say("   [ok] ревизия витрин: %s — пересобери build_lab.py"
    % ", ".join("%s=%s" % kv for kv in sorted(_rev.items())))

# ---- включить -----------------------------------------------------------------
key = "DlcEnabled_%s" % DLC_ID
for name in ("user.settings", "dx12user.settings"):
    p = DOCS / name
    if not p.exists():
        continue
    t = p.read_bytes().decode("utf-8", "replace")
    if key in t:
        say("   [--] %s — уже включено" % name)
        continue
    m = re.search(r"\[DLC\]\r?\n", t)
    t = (t[:m.end()] + "%s=1\r\n" % key + t[m.end():]) if m else \
        (t.rstrip("\r\n") + "\r\n[DLC]\r\n%s=1\r\n" % key)
    p.write_bytes(t.encode("utf-8"))
    say("   [ok] %s — включено" % name)

head("ГОТОВО")
say("   В игре (или крафт у мастеров после выдачи чертежей):")
for nm, _s, _k, ct, _i, r_, _e in BLANKS:
    say("     additem('%s')%s// %s (%s)" % (nm, " " * max(1, 26 - len(nm)), r_, ct))
say()
say("   Проверка: болванка надевается, fstat показывает FRG Blank _Stats +")
say("   autogen-урон (для мечей), и НИ ОДНОГО карточного процента.")
