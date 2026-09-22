# -*- coding: utf-8 -*-
"""
Собирает ВАНИЛЬНЫЕ версии модов — для игры БЕЗ W3EE Redux.

⚠️ В ИГРУ НИЧЕГО НЕ СТАВИТ. Всё складывается в dist_vanilla\\ рядом с этим файлом.
Иначе никак: в этой установке стоит Redux, ванильных классов тут не существует, и
такой мод просто не скомпилируется. Проверять — только на чистой игре.

Что собирается:
  modVanillaSetBonuses  — сетовые бонусы для ванили: нижние ступени начинают
                          считаться, пороги становятся ползунками, сила падает
                          со ступенью. Три перехвата, чужие файлы не трогаются.

Мод рунных камней собирается своим сборщиком:  setbonus\\build_core.py --vanilla
"""
import os, shutil, subprocess, sys
from pathlib import Path

# Консоль Windows по умолчанию в cp1251 и давится на ⚠️ — переключаем вывод.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist_vanilla"
ENC = ROOT / "tools" / "w3strings" / "w3strings.exe"
WORK = Path(os.environ["TEMP"]) / "vsb_strings"

MOD = "modVanillaSetBonuses"
GROUP = "VanillaSetBonuses"
SRC_WS = "VanillaSetBonuses.ws"
PRIORITY = 19

# 4471…4478 заняты своими же модами — проверено сплошным обходом,
# research\scan_idspaces.py. Берём следующее свободное.
IDSPACE = 4479

LOCALES = ["ar", "br", "cn", "cz", "de", "en", "es", "esmx",
           "fr", "hu", "it", "jp", "kr", "pl", "ru", "tr", "zh"]
META_LANG = {"cn": "zh"}

# (переменная, ключ подписи, вид, по умолчанию, ru, en)
VARS = [
    ("MinorCount",    "vsb_minor",  "SLIDER;1;6;1",     "3",
     "Частей для младшего бонуса", "Pieces for the minor bonus"),
    ("MajorCount",    "vsb_major",  "SLIDER;1;6;1",     "6",
     "Частей для старшего бонуса", "Pieces for the major bonus"),
    ("CountAllTiers", "vsb_count",  "TOGGLE",           "true",
     "Считать нижние ступени",     "Count lower tiers as set pieces"),
    ("ScalePower",    "vsb_scale",  "TOGGLE",           "true",
     "Ослаблять бонус по ступени", "Weaken the bonus by tier"),
    ("Tier1",         "vsb_t1",     "SLIDER;0;100;5",   "40",
     "Сила на 1-й ступени, %",     "Strength at tier 1, %"),
    ("Tier2",         "vsb_t2",     "SLIDER;0;100;5",   "55",
     "Сила на 2-й ступени, %",     "Strength at tier 2, %"),
    ("Tier3",         "vsb_t3",     "SLIDER;0;100;5",   "70",
     "Сила на 3-й ступени, %",     "Strength at tier 3, %"),
    ("Tier4",         "vsb_t4",     "SLIDER;0;100;5",   "85",
     "Сила на 4-й ступени, %",     "Strength at tier 4, %"),
]

MENU_KEY = "vsb_menu"
MENU_RU = "Сетовые бонусы (ваниль)"
MENU_EN = "Set Bonuses (vanilla)"

T = "\t"


def say(s=""):
    print(s, flush=True)


def head(s):
    say(); say("=" * 70); say("  " + s); say("=" * 70)


def make_xml():
    L = ['<?xml version="1.0" encoding="UTF-16"?>', "<UserConfig>"]
    L.append('\t<Group id="%s" displayName="Mods.%s">' % (GROUP, MENU_KEY))
    L.append("\t\t<PresetsArray>")
    L.append('\t\t\t<Preset id="0" displayName="default">')
    for vid, _k, _dt, default, _ru, _en in VARS:
        L.append('\t\t\t\t<Entry varId="%s" value="%s" />' % (vid, default))
    L.append("\t\t\t</Preset>")
    L.append("\t\t</PresetsArray>")
    L.append("\t\t<VisibleVars>")
    for vid, key, dt, _d, _ru, _en in VARS:
        L.append('\t\t\t<Var overrideGroup="%s" id="%s" displayName="%s" displayType="%s"/>'
                 % (GROUP, vid, key, dt))
    L.append("\t\t</VisibleVars>")
    L.append("\t</Group>")
    L.append("</UserConfig>")
    return "\r\n".join(L) + "\r\n"


def text_for(key, loc):
    if key == MENU_KEY:
        return MENU_RU if loc == "ru" else MENU_EN
    for _vid, k, _dt, _d, ru, en in VARS:
        if k == key:
            return ru if loc == "ru" else en
    return key


head("Ванильные версии — сборка в dist_vanilla")

if not (SRC / SRC_WS).exists():
    say("   [!!] нет исходника %s" % (SRC / SRC_WS))
    sys.exit(1)

base = DIST / MOD
if base.exists():
    shutil.rmtree(base)

# ---- 1. скрипт ---------------------------------------------------------------
d = base / "content" / "scripts" / "local"
d.mkdir(parents=True)
text = (SRC / SRC_WS).read_text(encoding="utf-8")
if "\\t" in text:
    say("   [!!] в исходнике остались буквальные обратные слэши — не записываю")
    sys.exit(1)
data = text.replace("\n", "\r\n").encode("utf-16")
(d / SRC_WS).write_bytes(data)
say("   [ok] %s  %d Б  UTF-16 LE + BOM  (строк %d)"
    % (SRC_WS, len(data), len(text.splitlines())))

# ---- 2. раздел настроек ------------------------------------------------------
cfg = base / "bin" / "config" / "r4game" / "user_config_matrix" / "pc"
cfg.mkdir(parents=True)
# ⚠️ Физически UTF-8 без BOM, хотя в прологе объявлен UTF-16 — игра пролог игнорирует.
(cfg / (GROUP + ".xml")).write_bytes(make_xml().encode("utf-8"))
say("   [ok] %s.xml  настроек %d" % (GROUP, len(VARS)))

# ---- 3. подписи --------------------------------------------------------------
keys = [MENU_KEY] + [k for _v, k, _dt, _d, _ru, _en in VARS]
base_id = int("211%04d000" % IDSPACE)
if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir(parents=True)

ok = 0
for loc in LOCALES:
    rows = [";meta[language=%s]" % META_LANG.get(loc, loc), "; id      |key(hex)|key(str)| text"]
    for i, k in enumerate(keys):
        rows.append("%d|        |%s|%s" % (base_id + i, k, " ".join(text_for(k, loc).split())))
    csv = WORK / ("vsb_%s.csv" % loc)
    csv.write_bytes(("\r\n".join(rows) + "\r\n").encode("utf-8"))
    subprocess.run([str(ENC), "--encode", str(csv), "--id-space", str(IDSPACE)],
                   capture_output=True, cwd=str(WORK))
    made = Path(str(csv) + ".w3strings")
    if made.exists():
        shutil.copyfile(made, base / "content" / ("%s.w3strings" % loc))
        ok += 1
say("   [ok] подписи: %d локалей из %d" % (ok, len(LOCALES)))

# ---- 4. памятка --------------------------------------------------------------
readme = """modVanillaSetBonuses — сетовые бонусы для ЧИСТОЙ ванили (без W3EE Redux)
========================================================================

⚠️ НЕ ПРОВЕРЕНО В ИГРЕ. Собрано на установке, где стоит Redux, а значит
   скомпилировать и погонять этот мод было негде. Первый запуск на чистой игре
   и есть его первая проверка.

ЧТО ДЕЛАЕТ
  1. Нижние ступени комплекта начинают засчитываться. В ванили комплект вообще
     не считается, пока вещь не гроссмейстерская, — нижние ступени дают ноль.
  2. Пороги бонусов становятся ползунками (в ванили жёстко 3 и 6).
  3. Сила бонуса падает пропорционально средней ступени надетого: 40 / 55 / 70 /
     85 / 100 %. Все четыре числа — ползунки.

УСТАНОВКА
  content\\  и  bin\\  из этой папки — в корень игры (папка modVanillaSetBonuses
  целиком идёт в mods\\). Затем вписать имя XML в оба списка меню:
      bin\\config\\r4game\\user_config_matrix\\pc\\dx11filelist.txt
      ...\\dx12filelist.txt
  строкой  VanillaSetBonuses.xml;  — файлы в UTF-16 LE с BOM!
  И добавить в Documents\\The Witcher 3\\mods.settings:
      [modVanillaSetBonuses]
      Enabled=1
      Priority={priority}

ПРОВЕРКА В ИГРЕ
  vsbinfo()  — печатает пороги, число частей до и после ослабления и ступень
               по каждому комплекту.

ЧЕГО ЖДАТЬ
  ⚠️ Строка «N/6» в подсказке предмета показывает ОСЛАБЛЕННОЕ число частей —
     её рисует тот же метод, который мы перехватываем. Это честно (столько игра
     и засчитывает), но непривычно. Выключается настройкой «Ослаблять бонус».
  ⚠️ У Гадюки в ванили нет ни одного сетового бонуса, у Вампира только один.
""".replace("{priority}", str(PRIORITY))
(base / "README.txt").write_bytes(readme.encode("utf-8"))

head("ГОТОВО")
say("   %s" % base)
say()
say("   Файлов: %d" % sum(1 for _ in base.rglob("*") if _.is_file()))
say()
say("   ⚠️ В игру НЕ поставлено и в этой установке НЕ ПРОВЕРЯЕМО:")
say("      тут стоит Redux, ванильные классы отсутствуют.")
say()
say("   Мод рунных камней для ванили:  setbonus\\build_core.py --vanilla")
