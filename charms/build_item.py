# -*- coding: utf-8 -*-
"""
Предметы мода «Камни чар»: пустой камень, камень очищения и пятнадцать
заряженных — по одному на каждые чары Redux. Карточки, значки, подписи (17
локалей), рецепты и упаковка в набор мода.

Камни объявляют себя КРАСКАМИ (ярлык mod_dye) — этим они бесплатно получают
игровой ход «использовать из сумки → выбрать надетую вещь». Ярлык CHT_Stone
отличает их от настоящих красок, а ЯРЛЫК ЧАР на заряженном камне (тот же
SwordGasEffect, что стоит на реликтовом мече) сразу говорит скрипту, какие это
чары — отдельная таблица не нужна, и подсказка сама рисует красную строку.

Грабли, купленные modSetBonusTransfer и записанные там же в исходнике:
  ⛔ категория "upgrade" — предмет ПРОПАДАЕТ из сумки после перезапуска;
     берём "usable" (вкладка снаряжения не отсеивает mod_dye);
  ⛔ блок <base_abilities> ОБЯЗАТЕЛЕН, иначе та же пропажа;
  ⛔ ссылаться на чужое свойство нельзя — объявляем своё в этом же файле;
  ⛔ подписи ОБЯЗАНЫ лежать в .w3strings, сырой текст игра не рисует;
  ⛔ wcc_lite запускать ИЗ ЕГО СОБСТВЕННОЙ ПАПКИ;
  ⛔ перевод строки внутри текста подписи рушит сборку всех локалей разом.
"""
import os, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from data import CHARMS, STONE, EMPTY_NAME, CLEAN_NAME

ROOT = Path(r"D:\Apps\w3ee-tweaks")
GAME = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")
MOD = GAME / "mods" / "modCharmTransfer"
WCC = GAME / "mods" / "Tools" / "wcc_lite" / "bin" / "x64" / "wcc_lite.exe"
ENC = ROOT / "tools" / "w3strings" / "w3strings.exe"
RAW = Path(os.environ["TEMP"]) / "cht_raw"
STAGE = Path(os.environ["TEMP"]) / "cht_stage"
WORK = Path(os.environ["TEMP"]) / "cht_strings"

XML_NAME = "cht_items.xml"

# 4471…4476, 4478…4480 заняты своими же модами — берём следующее свободное.
IDSPACE = 4481

LOCALES = ["ar", "br", "cn", "cz", "de", "en", "es", "esmx",
           "fr", "hu", "it", "jp", "kr", "pl", "ru", "tr", "zh"]
META_LANG = {"cn": "zh"}

RUNE = "icons/inventory/ingredients/runes/%s_64x64.png"

# Значки: только те семейства рун, что уже проверены в modSetBonusTransfer.
ICONS = ["rune_devana_greater", "rune_stribog_greater", "rune_svarog_greater",
         "rune_morana_greater", "rune_perun_greater", "rune_veles_greater",
         "rune_triglav_greater", "rune_zoria_greater",
         "rune_devana_lesser", "rune_stribog_lesser", "rune_svarog_lesser",
         "rune_morana_lesser", "rune_perun_lesser", "rune_veles_lesser",
         "rune_triglav_lesser"]

T = "\t"
P = T * 4

ABILITY = "CHT Charmstone _Stats"
ABILITIES = (
    T * 2 + "<abilities>\n"
    + T * 3 + '<ability name="' + ABILITY + '">\n'
    + T * 4 + "<tags></tags>\n"
    # Реликтовое качество: камень несёт чары реликта, пусть так и выглядит.
    + T * 4 + '<quality type="add" min="4" max="4"/>\n'
    + T * 3 + "</ability>\n"
    + T * 2 + "</abilities>\n"
)

# ---- подписи ------------------------------------------------------------------
TEXT = {
    "cht_empty": ("Пустой камень чар", "Empty Charmstone"),
    "cht_empty_d": (
        "Заготовка без свойств. Из неё у мастера-ремесленника делается камень "
        "чар — нужно лишь иметь при себе оружие с нужными чарами.",
        "A blank with no properties of its own. A craftsman turns it into a "
        "charmstone; all you need is a weapon carrying the charm on you."),
    "cht_clean": ("Камень очищения чар", "Cleansing Charmstone"),
    "cht_clean_d": (
        "Снимает с надетого оружия НАЛОЖЕННЫЕ чары. Собственные чары клинка "
        "остаются при нём. Камень не тратится.",
        "Strips a LAID charm off a worn weapon. A blade's own charm stays where "
        "it is. The stone is not consumed."),
    "cht_st_d": (
        "Камень с записанными чарами. Приложи к надетому оружию — чары лягут на "
        "него. На клинок со своими чарами не ложится: место занято. Камень не "
        "тратится.",
        "A stone with a charm recorded in it. Apply it to a worn weapon and the "
        "charm is laid on. A blade with a charm of its own will not take it - "
        "the place is taken. The stone is not consumed."),
    "cht_sc_d": (
        "Чертёж камня чар. Требует пустой камень чар и ОРУЖИЕ с этими чарами "
        "при себе. Оружие не расходуется — оно источник знания, а не материал.",
        "A charmstone diagram. Needs an empty charmstone and a WEAPON carrying "
        "that charm on you. The weapon is not consumed - it is the source of "
        "the knowledge, not a material."),
    "cht_from": ("Чары сняты с оружия:", "Charm native to:"),
    "cht_menu": ("Камни чар", "Charmstones"),
    "cht_messages": ("Показывать сообщения", "Show messages"),
    "cht_consume": ("Камень тратится при наложении", "Stone is consumed when laid"),
    "cht_grant": ("Выдавать чертежи камней", "Grant charmstone diagrams"),
}
NAME_RU = "Камень чар: %s"
NAME_EN = "Charmstone: %s"
SC_RU = "Чертёж: %s"
SC_EN = "Diagram: %s"

EMPTY_INGREDIENTS = [(1, "Meteorite ingot"), (1, "Ruby dust"), (2, "Infused dust")]
CLEAN_INGREDIENTS = [(1, EMPTY_NAME)]
STONE_INGREDIENTS = [(1, EMPTY_NAME)]


def stone_key(code):
    return "cht_st_%d" % code


def card(name, key, icon, tags, desc, price="400", stack="1"):
    return (
        T * 3 + "<item\n"
        + P + "name" + P + '="' + name + '"\n'
        # ⛔ НЕ "upgrade": предмет такой категории пропадает из сумки после
        # перезапуска (лесенка в игре, modSetBonusTransfer). "usable" выжил.
        + P + "category" + P + '="usable"\n'
        + P + "price" + P + '="' + price + '"\n'
        + P + "weight" + P + '="0.1"\n'
        + P + "stackable" + P + '="' + stack + '"\n'
        + P + "grid_size" + P + '="1"\n'
        + P + "localisation_key_name" + P + '="' + key + '"\n'
        + P + "localisation_key_description" + P + '="' + desc + '"\n'
        + P + "icon_path" + P + '="' + (RUNE % icon) + '"\n'
        + T * 3 + ">\n"
        + P + "<tags>" + P + tags + "\n"
        + P + "</tags>\n"
        # ⛔ блок свойств обязателен — без него предмет тоже пропадает
        + P + "<base_abilities>" + P + "<a>" + ABILITY + "</a>\n"
        + P + "</base_abilities>\n"
        + T * 3 + "</item>\n"
    )


def schem_card(name, key):
    return (
        T * 3 + "<item\n"
        + P + "name" + P + '="' + name + ' schematic"\n'
        + P + "category" + P + '="crafting_schematic"\n'
        + P + "price" + P + '="300"\n'
        + P + "weight" + P + '="0.1"\n'
        + P + "stackable" + P + '="100"\n'
        + P + "grid_size" + P + '="1"\n'
        + P + "localisation_key_name" + P + '="' + key + '"\n'
        + P + "localisation_key_description" + P + '="cht_sc_d"\n'
        + P + "icon_path" + P + '="icons/inventory/quests/ico_recipe.png"\n'
        + T * 3 + ">\n"
        # CHT_Schem — по нему мод выдаёт чертежи, не зная их имён
        + P + "<tags>" + P + "ReadableItem, mod_crafting, CHT_Schem\n"
        + P + "</tags>\n"
        + P + "<base_abilities>" + P + "<a>" + ABILITY + "</a>\n"
        + P + "</base_abilities>\n"
        + T * 3 + "</item>\n"
    )


def schematic(name, ingredients, level, ctype, price):
    ing = "".join(T * 5 + '<ingredient quantity="%d" item_name="%s"/>\n' % (q, it)
                  for q, it in ingredients)
    return (
        T * 2 + "<schematic\n"
        + T * 3 + "name_name" + P + '="' + name + ' schematic"\n'
        + T * 3 + "craftedItem_name" + P + '="' + name + '"\n'
        + T * 3 + "craftsmanLevel_name" + P + '="' + level + '"\n'
        + T * 3 + "craftsmanType_name" + P + '="' + ctype + '"\n'
        + T * 3 + "price" + P + '="' + price + '"\n'
        + T * 2 + ">\n"
        + T * 3 + "<ingredients>\n" + ing + T * 3 + "</ingredients>\n"
        + T * 2 + "</schematic>\n"
    )


# Заряженный камень несёт ЯРЛЫК СВОИХ ЧАР — тот же, что стоит на реликтовом
# мече. Скрипт читает код прямо с него, а подсказка бесплатно получает красную
# строку. Бафф камень при этом не даёт: W3EE вешает его только на ОРУЖИЕ.
ITEMXML = (
    '<?xml version="1.0" encoding="UTF-16"?>\n<redxml>\n'
    + T + "<definitions>\n" + ABILITIES + T * 2 + "<items>\n"
    + "".join(card(STONE % c, stone_key(c), ICONS[i],
                   "mod_upgrade, mod_dye, CHT_Stone, " + tag, "cht_st_d")
              for i, (c, tag, _t, _ru, _en) in enumerate(CHARMS))
    + card(EMPTY_NAME, "cht_empty", "rune_elemental_lesser",
           "mod_upgrade, CraftingIngredient", "cht_empty_d",
           price="150", stack="20")
    + card(CLEAN_NAME, "cht_clean", "rune_elemental_greater",
           "mod_upgrade, mod_dye, CHT_Stone, CHT_Clean", "cht_clean_d",
           price="250")
    + schem_card(EMPTY_NAME, "cht_sc_empty")
    + schem_card(CLEAN_NAME, "cht_sc_clean")
    + "".join(schem_card(STONE % c, "cht_sc_%d" % c) for c, _t, _e, _r, _n in CHARMS)
    + T * 2 + "</items>\n" + T + "</definitions>\n"
    + T + "<custom>\n" + T * 2 + "<crafting_schematics>\n"
    + schematic(EMPTY_NAME, EMPTY_INGREDIENTS, "Journeyman", "Crafter", "150")
    + schematic(CLEAN_NAME, CLEAN_INGREDIENTS, "Master", "Crafter", "200")
    # ⚠️ ЦЕНА КАМНЯ — НЕ В ЭТОМ СПИСКЕ. Расходуется только заготовка; настоящее
    # требование — ИМЕТЬ оружие с этими чарами, и его проверяет скрипт
    # (CHT_HasCharm). Меч не расходуется: он источник знания, а не материал.
    + "".join(schematic(STONE % c, STONE_INGREDIENTS, "Master", "Crafter", "300")
              for c, _t, _e, _r, _n in CHARMS)
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
    ru = (loc == "ru")
    if key in TEXT:
        return TEXT[key][0] if ru else TEXT[key][1]
    for c, _tag, _t, name_ru, name_en in CHARMS:
        if key == stone_key(c):
            return (NAME_RU % name_ru) if ru else (NAME_EN % name_en)
    if key == "cht_sc_empty":
        return (SC_RU % TEXT["cht_empty"][0]) if ru else (SC_EN % TEXT["cht_empty"][1])
    if key == "cht_sc_clean":
        return (SC_RU % TEXT["cht_clean"][0]) if ru else (SC_EN % TEXT["cht_clean"][1])
    for c, _tag, _t, name_ru, name_en in CHARMS:
        if key == "cht_sc_%d" % c:
            return ((SC_RU % (NAME_RU % name_ru)) if ru
                    else (SC_EN % (NAME_EN % name_en)))
    return key


head("Камни чар: 15 заряженных + пустой + очищающий")

if not WCC.exists():
    say("   [!!] wcc_lite не найден: %s" % WCC); sys.exit(1)
if not ENC.exists():
    say("   [!!] кодировщик подписей не найден: %s" % ENC); sys.exit(1)

# разметку проверяем ДО упаковки: обрубленный <item> убивает весь файл целиком
try:
    import xml.etree.ElementTree as _ET
    _ET.fromstring(ITEMXML)
    say("   [ok] разметка XML проверена")
except Exception as e:
    say("   [!!] XML СЛОМАН, не пакую: %s" % e); sys.exit(1)

if RAW.exists():
    shutil.rmtree(RAW)
payload = ITEMXML.replace("\n", "\r\n").encode("utf-16")
for branch in ("items", "items_plus"):
    d = RAW / "gameplay" / branch
    d.mkdir(parents=True, exist_ok=True)
    (d / XML_NAME).write_bytes(payload)
say("   [ok] карточки: %d предметов, %d Б" % (len(CHARMS) * 2 + 4, len(payload)))

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

# ---- подписи ------------------------------------------------------------------
keys = ([stone_key(c) for c, _tg, _t, _r, _e in CHARMS]
        + ["cht_sc_%d" % c for c, _tg, _t, _r, _e in CHARMS]
        + ["cht_from",
           "cht_st_d", "cht_empty", "cht_empty_d", "cht_clean", "cht_clean_d",
           "cht_sc_d", "cht_sc_empty", "cht_sc_clean",
           "cht_menu", "cht_messages", "cht_consume", "cht_grant"])
base = int("211%04d000" % IDSPACE)
if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir(parents=True)

ok, failed = 0, []
for loc in LOCALES:
    rows = [";meta[language=%s]" % META_LANG.get(loc, loc),
            "; id      |key(hex)|key(str)| text"]
    for i, k in enumerate(keys):
        txt = " ".join(text_for(k, loc).split())   # перевод строки рушит сборку
        rows.append("%d|        |%s|%s" % (base + i, k, txt))
    csv = WORK / ("cht_%s.csv" % loc)
    csv.write_bytes(("\r\n".join(rows) + "\r\n").encode("utf-8"))
    subprocess.run([str(ENC), "--encode", str(csv), "--id-space", str(IDSPACE)],
                   capture_output=True, cwd=str(WORK))
    produced = Path(str(csv) + ".w3strings")
    if produced.exists():
        shutil.copyfile(produced, STAGE / ("%s.w3strings" % loc))
        ok += 1
    else:
        failed.append(loc)

say("   [%s] подписи: %d локалей из %d%s"
    % ("ok" if not failed else "!!", ok, len(LOCALES),
       (", не вышло: " + ", ".join(failed)) if failed else ""))

# ---- установка ----------------------------------------------------------------
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
    bat = Path(__file__).parent / "install_charms.bat"
    bat.write_text(
        "@echo off\r\n"
        'tasklist /FI "IMAGENAME eq witcher3.exe" | find /I "witcher3.exe" >nul\r\n'
        "if not errorlevel 1 (\r\n"
        "  echo The game is still running. Close it first, then run this again.\r\n"
        "  pause\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        'xcopy /Y /Q "%s\\*" "%s\\" >nul\r\n' % (STAGE, content) +
        "echo Charmstones installed. Start the game.\r\n"
        "pause\r\n", encoding="ascii")
    say("       установщик: %s" % bat)
else:
    say("   [ok] УСТАНОВЛЕНО в мод — файлов %d" % installed)

head("ГОТОВО")
say("   В игре:")
say("     additem('%s')      // пустой камень" % EMPTY_NAME)
say("     additem('%s')  // камень очищения" % CLEAN_NAME)
for c, _tg, _t, ru, _en in CHARMS:
    say("     additem('%s')%s// %s" % (STONE % c, " " * max(1, 26 - len(STONE % c)), ru))
say()
say("   Или одной командой в игре: chtgive()")
