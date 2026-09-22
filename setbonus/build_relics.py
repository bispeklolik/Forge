# -*- coding: utf-8 -*-
"""
ДОПОЛНЕНИЕ: одиннадцать реликтовых комплектов W3EE Redux.

Отдельная папка `dlc\\dlcSBTRelics` — ставится и снимается независимо от основного
мода. Требует Redux: этих комплектов в ванильной игре не существует вовсе.

⚠️ Кода в дополнении НЕТ ни строчки. Основной мод хранит на вещи ЧИСЛО-код, а тип
комплекта получает у самой игры через `SetItemNameToType( ярлык )`. Поэтому имена
редуксовых значений нигде не упоминаются и основной мод остаётся пригоден для ванили.

⛔ Первый замысел — «поставить ярлык на вещь и пусть игра сама его прочитает» — НЕ
работал: оригинал читает ярлыки через GetItemTags, а ярлык, добавленный на экземпляр
через AddItemTag, туда не попадает. Разбор — в заметке witcher3-relic-sets-addon.

Устройство и приёмы — те же, что в build_dlc.py:
  * паспорт собирается passport.py из ванильного dlc1 — чужого в цепочке нет;
  * категория "usable" (НЕ "upgrade" — с ней предмет не переживает загрузку);
  * качество 5 — «ведьмачье снаряжение», зелёная надпись;
  * свойство объявляется в своём же файле.

⚠️ Путь к значку, найденный в файлах игры, ещё НЕ значит, что текстура есть.
Семейство `rune_quentin` объявлено в content0 у трёх ванильных рун — а картинки к
нему нет, это вырезанный контент. Брать только те значки, что видели нарисованными.
"""
import os, re, shutil, struct, subprocess, sys, zlib
from pathlib import Path

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import loc as loc_tables
import passport as passport_gen

GAME = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")
DOCS = Path(os.environ["USERPROFILE"]) / "Documents" / "The Witcher 3"
WCC = GAME / "mods" / "Tools" / "wcc_lite" / "bin" / "x64" / "wcc_lite.exe"
ENC = Path(r"D:\Apps\w3ee-tweaks") / "tools" / "w3strings" / "w3strings.exe"

DLC = GAME / "dlc" / "dlcSBTRelics"
RAW = Path(os.environ["TEMP"]) / "sbtrel_raw"
WORK = Path(os.environ["TEMP"]) / "sbtrel_strings"

MOUNT = "sbtrelic"
ITEMS = "sbt_relic_sets.xml"
SHOP = "sbt_relicshop.xml"
EXTS = "sbt_relic_set_extensions.xml"
DLC_ID = "dlc_sbt_002"

IDSPACE = 4478       # ⚠️ 4477 БЫЛ ЗАНЯТ нашим же modW3EERedux_TierBonuses —
                     # столкновение подписей. Занятость проверять сплошным
                     # обходом: research\scan_idspaces.py
LOCALES = ["ar", "br", "cn", "cz", "de", "en", "es", "esmx",
           "fr", "hu", "it", "jp", "kr", "pl", "ru", "tr", "zh"]
META_LANG = {"cn": "zh"}
RUNE = "icons/inventory/ingredients/runes/%s_64x64.png"

ABILITY = "SBT Relic Runestone _Stats"

# внутреннее имя, ярлык, ключ, значок, ru, en
RELICS = [
    ("SBT Runestone Temerian",   "SBT_Temerian",   "sbtr_temerian",   "rune_dazhbog",         "Темерия",       "Temerian"),
    ("SBT Runestone Nilfgaard",  "SBT_Nilfgaard",  "sbtr_nilfgaard",  "rune_devana",          "Нильфгаард",    "Nilfgaardian"),
    ("SBT Runestone Skellige",   "SBT_Skellige",   "sbtr_skellige",   "rune_elemental",       "Скеллиге",      "Skellige"),
    ("SBT Runestone Ofieri",     "SBT_Ofieri",     "sbtr_ofieri",     "rune_morana",          "Офир",          "Ofieri"),
    ("SBT Runestone NewMoon",    "SBT_NewMoon",    "sbtr_newmoon",    "rune_perun",           "Новолуние",     "New Moon"),
    ("SBT Runestone Elven",      "SBT_Elven",      "sbtr_elven",      "rune_zoria"   ,         "Эльфы",         "Elven"),
    ("SBT Runestone Tiger",      "SBT_Tiger",      "sbtr_tiger",      "rune_stribog",         "Тигр",          "Tiger"),
    ("SBT Runestone Gothic",     "SBT_Gothic",     "sbtr_gothic",     "rune_svarog",          "Готика",        "Gothic"),
    ("SBT Runestone Dimeritium", "SBT_Dimeritium", "sbtr_dimeritium", "rune_triglav",         "Диметрий",      "Dimeritium"),
    ("SBT Runestone Meteorite",  "SBT_Meteorite",  "sbtr_meteorite",  "rune_veles",           "Метеорит",      "Meteorite"),
    ("SBT Runestone VampireAlt", "SBT_VampireAlt", "sbtr_vampalt",    "rune_dazhbog_lesser",  "Вампир (иной)", "Vampire (alt)"),
]

DESC_KEY = "sbtr_desc"
DESC_RU = ("Рунный камень реликтового комплекта. Применяется к надетому предмету и делает "
           "его частью этого комплекта. Камень не тратится. Требует W3EE Redux.")
DESC_EN = ("A relic set runestone. Applied to a worn item, it makes that item count towards "
           "that set. The stone is not consumed. Requires W3EE Redux.")
SC_DESC_KEY = "sbtr_sc_desc"
SC_DESC_RU = ("Чертёж рунного камня реликтового комплекта. Требует пустой рунный камень и "
              "полный комплект этого набора на руках. Сам комплект не расходуется.")
SC_DESC_EN = ("Diagram for a relic set runestone. Requires an empty runestone and a complete "
              "set of that kind in your possession. The set itself is not consumed.")

EMPTY_NAME = "SBT Empty Runestone"       # заготовка из основного мода
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


def card(name, tag, key, icon):
    return (
        T * 3 + "<item\n"
        + P + 'name' + P + '="' + name + '"\n'
        + P + 'category' + P + '="usable"\n'
        + P + 'price' + P + '="500"\n'
        + P + 'weight' + P + '="0.1"\n'
        + P + 'stackable' + P + '="1"\n'
        + P + 'grid_size' + P + '="1"\n'
        + P + 'localisation_key_name' + P + '="' + key + '"\n'
        + P + 'localisation_key_description' + P + '="' + DESC_KEY + '"\n'
        + P + 'icon_path' + P + '="' + (RUNE % icon) + '"\n'
        + T * 3 + ">\n"
        + P + "<tags>" + P + "mod_upgrade, mod_dye, SBT_Stone, " + tag + "\n"
        + P + "</tags>\n"
        + P + "<base_abilities>" + P + "<a>" + ABILITY + "</a>\n"
        + P + "</base_abilities>\n"
        + T * 3 + "</item>\n"
    )


def schem_card(name, key):
    return (
        T * 3 + "<item\n"
        + P + 'name' + P + '="' + name + ' schematic"\n'
        + P + 'category' + P + '="crafting_schematic"\n'
        + P + 'price' + P + '="600"\n'
        + P + 'weight' + P + '="0.1"\n'
        + P + 'stackable' + P + '="100"\n'
        + P + 'grid_size' + P + '="1"\n'
        + P + 'localisation_key_name' + P + '="' + key + '_sc"\n'
        + P + 'localisation_key_description' + P + '="' + SC_DESC_KEY + '"\n'
        + P + 'icon_path' + P + '="icons/inventory/quests/ico_recipe.png"\n'
        + T * 3 + ">\n"
        # SBT_Schem — по нему основной мод выдаёт чертежи, не зная их имён.
        + P + "<tags>" + P + "ReadableItem, mod_crafting, mod_precious, SBT_Schem\n"
        + P + "</tags>\n"
        + T * 3 + "</item>\n"
    )


# ⚠️ Здесь была таблица материалов для готического, диметриевого и метеоритного
# камней — под вывод «этих комплектов в игре нет, значит требовать комплект нельзя».
# Вывод был НЕВЕРЕН. Первая проверка охватила два хранилища из шестнадцати и не
# заглянула в dlc\dlcW3EE, а вещи лежали именно там: по 9 предметов на комплект
# (броня, сапоги, перчатки, штаны — в двух исполнениях — и шлем), со своими
# чертежами. Сплошная проверка — research\scan_sets.py. Цена у всех одиннадцати
# теперь одна и та же: полный комплект на руках.
MATS = {}


def schematic(name):
    return (
        T * 2 + "<schematic\n"
        + T * 3 + 'name_name' + P + '="' + name + ' schematic"\n'
        + T * 3 + 'craftedItem_name' + P + '="' + name + '"\n'
        + T * 3 + 'craftsmanLevel_name' + P + '="Master"\n'
        + T * 3 + 'craftsmanType_name' + P + '="Crafter"\n'
        + T * 3 + 'price' + P + '="500"\n'
        + T * 2 + ">\n"
        + T * 3 + "<ingredients>\n"
        + T * 5 + '<ingredient quantity="1" item_name="' + EMPTY_NAME + '"/>\n'
        + "".join(T * 5 + '<ingredient quantity="%d" item_name="%s"/>\n' % (q, it)
                  for q, it in MATS.get(name, []))
        + T * 3 + "</ingredients>\n"
        + T * 2 + "</schematic>\n"
    )


ABILITIES = (
    T * 2 + "<abilities>\n"
    + T * 3 + '<ability name="' + ABILITY + '">\n'
    + T * 4 + "<tags></tags>\n"
    + T * 4 + '<quality type="add" min="5" max="5"/>\n'
    + T * 3 + "</ability>\n"
    + T * 2 + "</abilities>\n"
)

ITEMXML = (
    '<?xml version="1.0" encoding="UTF-16"?>\n<redxml>\n'
    + T + "<definitions>\n" + ABILITIES + T * 2 + "<items>\n"
    + "".join(card(nm, tg, ky, ic) for nm, tg, ky, ic, _r, _e in RELICS)
    + "".join(schem_card(nm, ky) for nm, _tg, ky, _ic, _r, _e in RELICS)
    + T * 2 + "</items>\n" + T + "</definitions>\n"
    + T + "<custom>\n" + T * 2 + "<crafting_schematics>\n"
    + "".join(schematic(nm) for nm, _tg, _ky, _ic, _r, _e in RELICS)
    + T * 2 + "</crafting_schematics>\n" + T + "</custom>\n</redxml>\n"
)

EMPTY_XML = ('<?xml version="1.0" encoding="UTF-16"?>\r\n<redxml>\r\n\t<definitions>\r\n'
             '\t\t<items>\r\n\t\t</items>\r\n\t</definitions>\r\n</redxml>\r\n')
STRINGS_LIST = b'{\n    "files": []\n}'




def text_for(key, loc):
    """Подписи — из loc.py, все 17 языков. Названия комплектов остаются английскими
    (кроме русского): чистого названия комплекта в файлах игры нет."""
    if key == DESC_KEY:
        return loc_tables.pick(loc_tables.DESC, loc)
    if key == SC_DESC_KEY:
        return loc_tables.pick(loc_tables.SC_DESC, loc)
    for _nm, _tg, ky, _ic, r, e in RELICS:
        name = r if loc == "ru" else e
        if ky == key:
            return loc_tables.pick(loc_tables.NAME, loc) % name
        if ky + "_sc" == key:
            return loc_tables.pick(loc_tables.SC_NAME, loc) % name
    return key


head("Дополнение: реликтовые комплекты Redux")

if game_running():
    say("   ИГРА ЗАПУЩЕНА — закройте её")
    sys.exit(3)
for nm, tg, ky, ic, r, e in RELICS:
    say("   %-16s %-16s %s" % (r, tg, ic))

# ---- паспорт ------------------------------------------------------------------
# Из паспорта ванильного dlc1, прямо из бандла игры. См. passport.py.
try:
    tpl = passport_gen.load_template(GAME)
except Exception as err:
    say("   [!!] не достаётся болванка из игры: %s" % err)
    sys.exit(1)

passport_bytes = passport_gen.build(MOUNT, "sbt_relicsets", "sbt_relicsets_desc",
                                ITEMS, SHOP, EXTS, template=tpl)
if re.search(rb"vagabond", passport_bytes, re.I):
    say("   [!!] в паспорте следы чужого мода")
    sys.exit(1)

passport = passport_bytes          # дальше по коду имя прежнее
say()
say("   [ok] паспорт готов, %d Б (болванка — ванильный %s)" % (len(passport), "dlc1"))

# ---- дерево -------------------------------------------------------------------
if RAW.exists():
    shutil.rmtree(RAW)
RAW.mkdir(parents=True)
(RAW / "strings.list").write_bytes(STRINGS_LIST)
base = RAW / "dlc" / MOUNT
base.mkdir(parents=True)
(base / (MOUNT + ".reddlc")).write_bytes(passport)

payload = ITEMXML.replace("\n", "\r\n").encode("utf-16")
empty = EMPTY_XML.encode("utf-16")
for branch in ("items", "items_plus"):
    d = base / "data" / "gameplay" / branch
    d.mkdir(parents=True)
    (d / ITEMS).write_bytes(payload)
    (d / SHOP).write_bytes(empty)
    (d / EXTS).write_bytes(empty)
(base / "data" / "items").mkdir(parents=True)
(base / "data" / "items" / "readme.txt").write_bytes(b"placeholder so the directory exists\n")
say("   [ok] карточки: %d камней + %d чертежей, %d Б" % (len(RELICS), len(RELICS), len(payload)))

# ---- подписи ------------------------------------------------------------------
keys = ([ky for _n, _t, ky, _i, _r, _e in RELICS]
        + [ky + "_sc" for _n, _t, ky, _i, _r, _e in RELICS]
        + [DESC_KEY, SC_DESC_KEY])
base_id = int("211%04d000" % IDSPACE)
if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir(parents=True)
ok = 0
for loc in LOCALES:
    rows = [";meta[language=%s]" % META_LANG.get(loc, loc), "; id      |key(hex)|key(str)| text"]
    for i, k in enumerate(keys):
        rows.append("%d|        |%s|%s" % (base_id + i, k, " ".join(text_for(k, loc).split())))
    csv = WORK / ("sbtr_%s.csv" % loc)
    csv.write_bytes(("\r\n".join(rows) + "\r\n").encode("utf-8"))
    subprocess.run([str(ENC), "--encode", str(csv), "--id-space", str(IDSPACE)],
                   capture_output=True, cwd=str(WORK))
    made = Path(str(csv) + ".w3strings")
    if made.exists():
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
    src = WORK / ("sbtr_%s.csv.w3strings" % loc)
    if src.exists():
        shutil.copyfile(src, content / ("%s.w3strings" % loc))
say("   [ok] blob0.bundle %d Б, файлов в дополнении %d"
    % ((content / "blob0.bundle").stat().st_size,
       sum(1 for _ in DLC.rglob("*") if _.is_file())))

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
say("   В игре:")
for nm, _t, _k, _i, r, _e in RELICS:
    say("     additem('%s')%s// %s" % (nm, " " * max(1, 30 - len(nm)), r))
say()
say("   Снять дополнение: удалить папку")
say("     %s" % DLC)
say("   и строку %s из обоих файлов настроек." % key)
