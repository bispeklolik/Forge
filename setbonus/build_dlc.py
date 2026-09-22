# -*- coding: utf-8 -*-
"""
Собирает ДОПОЛНЕНИЕ с предметами мода: dlc\\dlcSetBonusTransfer.

ЗАЧЕМ. Новый предмет должен переживать сохранение. Для этого он живёт не в
mods\\, а в собственной папке dlc\\ с двоичным паспортом .reddlc и определениями
по пути dlc\\<точка>\\data\\gameplay\\items\\.

ПАСПОРТ собирает passport.py — из паспорта ВАНИЛЬНОГО dlc1, который есть у
каждого владельца игры. Раньше болванку брали из архива чужого мода «Vagabond
Armor» в Загрузках; это убрано (13.09.2026), потому что сборка зависела от
файла в личной папке и на другой машине мод не пересобирался вовсе. Новый
паспорт до байта того же размера, и все его значения сверены со старым.

ЧТО ВЫЯСНИЛОСЬ ПО ДОРОГЕ (обе мои прежние версии были неверны):

  * КОНТРОЛЬНЫЕ СУММЫ ИГРА НЕ ПРОВЕРЯЕТ. У «Бродяги» не сходится ни одна —
    ни таблица имён, ни один из восьми кусков, — и мод прекрасно работает.
    Пересчитываем всё равно, для опрятности, но лечило не это.
  * ПУСТОЙ ПУТЬ У ЛИШНЕГО МОНТИРОВЩИКА — НОРМА. У «Бродяги» монтировщик
    интерфейса объявлен, а путь пустой. Именно поэтому берём ЕГО паспорт, а не
    ванильный dlc13: у того путь вёл в несуществующую папку, и игра начинала
    спотыкаться — рывки при стабильном кадре.
  * СВОЙСТВА ПРЕДМЕТА ОБЪЯВЛЯЮТСЯ В СВОЁМ ЖЕ ФАЙЛЕ. Ссылка на чужое
    («Magic _Stats» из def_item_quality.xml) разрешалась в сессии, но предмет
    не переживал загрузку. У «Бродяги» — свой раздел <abilities> рядом с
    предметами, как и в каждом ванильном файле.

Скрипты и меню настроек ОСТАЮТСЯ в mods\\ — переезжают только определения.
"""
import os, re, shutil, struct, subprocess, sys, zlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import passport as passport_gen

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
from medallion import bundles

GAME = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")
DOCS = Path(os.environ["USERPROFILE"]) / "Documents" / "The Witcher 3"
WCC = GAME / "mods" / "Tools" / "wcc_lite" / "bin" / "x64" / "wcc_lite.exe"

MOD = GAME / "mods" / "modSetBonusTransfer"
DLC = GAME / "dlc" / "dlcSetBonusTransfer"
RAW = Path(os.environ["TEMP"]) / "sbt_dlc_raw"
SRC_XML = Path(os.environ["TEMP"]) / "sbt_raw" / "gameplay" / "items" / "sbt_items.xml"

MOUNT = "sbtstone"
ITEMS = "sbt_runestones.xml"
SHOP = "sbt_stoneshop.xml"
EXTS = "sbt_runestone_extensions.xml"
DLC_ID = "dlc_sbt_001"

STRINGS_LIST = b'{\n    "files": []\n}'
EMPTY_XML = ('<?xml version="1.0" encoding="UTF-16"?>\r\n<redxml>\r\n\t<definitions>\r\n'
             '\t\t<items>\r\n\t\t</items>\r\n\t</definitions>\r\n</redxml>\r\n')


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




head("Дополнение с предметами")

if game_running():
    say("   ИГРА ЗАПУЩЕНА — закройте её")
    sys.exit(3)

if not SRC_XML.exists():
    say("   [!!] нет собранных карточек — сначала build_item.py")
    sys.exit(1)

# ---- паспорт ------------------------------------------------------------------
# Собирается из паспорта ванильного dlc1, взятого прямо из бандла игры.
# Ничего чужого в цепочке нет, длины строк ничем не ограничены.
try:
    tpl = passport_gen.load_template(GAME)
except Exception as err:
    say("   [!!] не достаётся болванка из игры: %s" % err)
    sys.exit(1)

passport_bytes = passport_gen.build(MOUNT, "sbt_runestone", "sbt_runestone_desc",
                                ITEMS, SHOP, EXTS, template=tpl)
say("   болванка: ванильный %s из бандла игры, %d Б" % (passport_gen.TEMPLATE_DLC, len(tpl)))

if re.search(rb"vagabond", passport_bytes, re.I):
    say("   [!!] в паспорте следы чужого мода")
    sys.exit(1)

passport = passport_bytes          # дальше по коду имя прежнее
say("   [ok] паспорт готов, %d Б" % len(passport))

# ---- дерево -------------------------------------------------------------------
if RAW.exists():
    shutil.rmtree(RAW)
RAW.mkdir(parents=True)
(RAW / "strings.list").write_bytes(STRINGS_LIST)

items_xml = SRC_XML.read_bytes()
empty_xml = EMPTY_XML.encode("utf-16")

base = RAW / "dlc" / MOUNT
base.mkdir(parents=True)
(base / (MOUNT + ".reddlc")).write_bytes(passport)

for branch in ("items", "items_plus"):
    d = base / "data" / "gameplay" / branch
    d.mkdir(parents=True)
    (d / ITEMS).write_bytes(items_xml)
    (d / SHOP).write_bytes(empty_xml)
    (d / EXTS).write_bytes(empty_xml)

# Папка шаблонов сущностей: монтировщик на неё смотрит, и у «Бродяги» она
# не пустая. Кладём заглушку, чтобы папка существовала — пустая папка в набор
# файлов не попадает, а несуществующий путь игра переживает плохо (рывки).
items_dir = base / "data" / "items"
items_dir.mkdir(parents=True)
(items_dir / "readme.txt").write_bytes(b"placeholder so the directory exists\n")

say("   [ok] дерево: %d файлов" % sum(1 for _ in RAW.rglob("*") if _.is_file()))

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
say("   [ok] blob0.bundle %d Б" % (content / "blob0.bundle").stat().st_size)

subprocess.run([str(WCC), "metadatastore", "-path=" + str(content)],
               capture_output=True, text=True, timeout=300, cwd=str(WCC.parent))
say("   [ok] metadata.store %s" % ("есть" if (content / "metadata.store").exists() else "НЕТ"))

# ---- убрать предметы из мода --------------------------------------------------
gone = []
for f in ("blob0.bundle", "metadata.store"):
    p = MOD / "content" / f
    if p.exists():
        p.unlink()
        gone.append(f)
say("   [ok] из мода убрано: %s" % (", ".join(gone) if gone else "нечего"))

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
say("   ПРОВЕРКА полным кругом:")
say("     1. additem('SBT Clone Test')      — копия ванильной руны")
say("     2. additem('SBT Runestone Griffin')")
say("     3. сохраниться, ВЫЙТИ В МЕНЮ, загрузиться")
say("     4. оба на месте?")
say()
say("   Откат: python dlc_off.py")
