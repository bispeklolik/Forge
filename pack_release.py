# -*- coding: utf-8 -*-
"""
Пакует мод рунных камней в ОТДЕЛЬНЫЕ архивы для раздачи.

Три архива, и это принципиально: человек с Nexus качает СВОЙ вариант, а не один мод
с настройками. Версия под Redux и версия под ваниль — разные сборки скрипта, вместе
они не работают и рядом лежать не должны.

  SetBonusTransfer-Redux-<в>.zip      мод камней под W3EE Redux + 8 камней школ
  SetBonusTransfer-RelicSets-<в>.zip  дополнение: 11 камней реликтовых комплектов
                                      Redux, ставится поверх основного мода
  SetBonusTransfer-Vanilla-<в>.zip    мод камней под чистую ваниль + 8 камней
                                      (реликтовых комплектов в ванили НЕТ)
  VanillaSetBonuses-<в>.zip           ванильные сетовые бонусы: ползунки порога
                                      и ослабление по ступени

Перед запуском собрать всё:
    setbonus\\build_core.py              (сборка под Redux, ставится в игру)
    setbonus\\build_item.py + build_dlc.py + build_relics.py
    setbonus\\build_menu.py
    setbonus\\build_core.py --vanilla    (ванильная сборка в dist_vanilla)
    build_vanilla.py                     (ванильные сетовые бонусы)
"""
import os, shutil, sys, zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
GAME = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")
DIST_V = ROOT / "dist_vanilla"
# Кладём сразу в папку на выкладку — там же лежат остальные готовые моды.
OUT = Path(r"D:\Apps\w3ee-mods") / "Архивы по отдельности"
VER = "1.1"

CFG = "bin/config/r4game/user_config_matrix/pc"


def say(s=""):
    print(s, flush=True)


def head(s):
    say(); say("=" * 70); say("  " + s); say("=" * 70)


def add_tree(z, src: Path, prefix: str, n=[0]):
    """Кладёт папку в архив под нужным путём. Возвращает число файлов."""
    cnt = 0
    for p in sorted(src.rglob("*")):
        if p.is_file():
            z.write(p, prefix + "/" + str(p.relative_to(src)).replace("\\", "/"))
            cnt += 1
    return cnt


README_COMMON = """
ЧТО ЭТО
  Рунные камни, переносящие сетовый бонус на любую вещь. Камень применяется из
  сумки, как краска, гнездо руны НЕ занимает и не тратится. Цели — вся броня и
  оба меча.

  Камень куётся из ПОЛНОГО КОМПЛЕКТА своей школы: комплект нужно ИМЕТЬ, а не
  сжечь — при крафте расходуется только пустой рунный камень.

  Есть камень очищения: снимает перенесённый бонус, возвращая вещи её собственный
  комплект.

УСТАНОВКА
  Содержимое архива — в корень игры (папки mods, dlc, bin ложатся поверх своих).
  Затем вписать имя раздела настроек в ОБА списка меню:
      bin\\config\\r4game\\user_config_matrix\\pc\\dx11filelist.txt
      bin\\config\\r4game\\user_config_matrix\\pc\\dx12filelist.txt
  строкой   SetBonusTransfer.xml;
  ⚠️ Эти файлы в UTF-16 LE с BOM — править только редактором, который это умеет,
  иначе пропадут меню ВСЕХ модов сразу.

  И включить дополнения в Documents\\The Witcher 3\\user.settings И
  dx12user.settings, в секции [DLC]:
{dlc_keys}
УДАЛЕНИЕ
  Убрать папки мода и дополнений, снять строки из списков меню и из [DLC].
  Сохранение переживает удаление: пометки лежат на предметах, и без мода они
  просто ничего не значат.

КОНСОЛЬНЫЕ КОМАНДЫ
  sbtsets()          самопроверка: код комплекта -> номер, все должны быть > 0
  sbtinfo()          сколько вещей помечено и счётчики комплектов
  sbtdiag()          подробно по каждому слоту
  sbtuse(слот, код)  применить на надетую вещь; слот 0..5, мечи — 4 и 5
  sbtset(код)        пометить разом всю надетую броню
  sbtclear()         снять пометки
"""

REDUX_TAIL = """
ТРЕБОВАНИЯ
  W3EE Redux. Это НЕ ванильная версия — она в отдельном архиве.
  Проверено на The Witcher 3 Next-Gen (4.0x), DX12, с W3EE Redux.

ЧТО ВНУТРИ
  mods\\modSetBonusTransfer        скрипт мода
  dlc\\dlcSetBonusTransfer         8 камней школ, заготовка, камень очищения
  bin\\...\\SetBonusTransfer.xml    раздел настроек

ЕСТЬ ДОПОЛНЕНИЕ
  Отдельной закачкой — SetBonusTransfer-RelicSets: ещё 11 камней на реликтовые
  комплекты, которые добавляет Redux (Темерия, Нильфгаард, Скеллиге, Офир,
  Новолуние, Эльфы, Тигр, Готика, Диметрий, Метеорит, Вампир-иной).
  Ставится поверх этого мода и без него не работает.

ВМЕСТЕ С МОДОМ ТИРОВ
  Если стоит наш Tier-Scaled Set Bonuses, сила перенесённого бонуса считается по
  тому комплекту, который вы реально собрали, — где бы он ни лежал: в сумке, на
  Плотве или в тайнике. Выключается настройкой «Сила бонуса — по собранному
  комплекту».
"""

RELICS_README = """
ЧТО ЭТО
  Дополнение к моду SetBonusTransfer: ещё 11 рунных камней на реликтовые
  комплекты, которые добавляет W3EE Redux. Всего с основным модом получается 19.

  Темерия, Нильфгаард, Скеллиге, Офир, Новолуние, Эльфы, Тигр, Готика,
  Диметрий, Метеорит, Вампир (иной).

  Камни работают ровно как в основном моде: куются из полного комплекта своей
  школы, применяются из сумки как краска, гнездо руны не занимают и не тратятся.

ТРЕБОВАНИЯ
  1. Основной мод SetBonusTransfer (версия под W3EE Redux). Без него дополнение
     бесполезно: здесь нет ни строчки кода, только предметы и подписи.
  2. W3EE Redux — реликтовых комплектов в ванильной игре не существует вовсе.

УСТАНОВКА
  Папку dlc из архива — в корень игры, поверх существующей.
  Затем включить дополнение в Documents\\The Witcher 3\\user.settings И
  dx12user.settings, в секции [DLC]:
      DlcEnabled_dlc_sbt_002=1

  Ничего в списках меню прописывать не нужно: раздел настроек уже поставил
  основной мод.

УДАЛЕНИЕ
  Убрать папку dlc\\dlcSBTRelics и строку из [DLC]. Основной мод и сохранение
  от этого не страдают: пометки лежат на предметах и без камня просто не
  обновляются.

ПРОВЕРКА
  sbtsets()   в консоли: коды всех 19 комплектов должны быть больше нуля.
"""

VANILLA_TAIL = """
ТРЕБОВАНИЯ
  ЧИСТАЯ игра, БЕЗ W3EE Redux. Для Redux есть отдельный архив — не путайте, они
  собраны по-разному и вместе не работают.

  ⚠️ ЭТА СБОРКА НЕ ПРОВЕРЕНА В ИГРЕ. Она собиралась на установке с Redux, где
  ванильных классов не существует, так что скомпилировать её было негде. Первый
  запуск на чистой игре и есть её первая проверка.

ЧТО ВНУТРИ
  mods\\modSetBonusTransfer        скрипт мода (ванильная сборка)
  dlc\\dlcSetBonusTransfer         8 камней школ, заготовка, камень очищения
  bin\\...\\SetBonusTransfer.xml    раздел настроек

  Дополнения на реликтовые комплекты здесь НЕТ намеренно: этих комплектов в
  ванильной игре не существует.

ОГОВОРКИ ВАНИЛИ
  У Гадюки в ванильной игре нет ни одного сетового бонуса, у Вампира только один.
  Пометить вещь их комплектом можно, но бонуса не будет — это сама игра, не мод.
"""


def audit_zip(path, want, label):
    """Пересчитывает готовый архив и сверяет с ожиданием.

    Это не перестраховка: подписи .w3strings лежат ОТДЕЛЬНО от скрипта, и стоит
    забыть их положить, как архив молча выходит на треть меньше — снаружи такой
    же, внутри нерабочий. Единственная защита — считать.
    """
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
    got = {
        "всего": len(names),
        ".w3strings": sum(1 for n in names if n.endswith(".w3strings")),
        ".ws": sum(1 for n in names if n.endswith(".ws")),
        ".bundle": sum(1 for n in names if n.endswith(".bundle")),
        ".xml": sum(1 for n in names if n.endswith(".xml")),
    }
    dupes = len(names) - len(set(names))
    bad = [k for k, v in want.items() if got.get(k) != v]
    if bad or dupes:
        say()
        say("   [!!] СОСТАВ АРХИВА НЕ СОШЁЛСЯ: %s" % label)
        for k in want:
            mark = "  <-- ждали %d" % want[k] if k in bad else ""
            say("        %-12s %d%s" % (k, got.get(k, 0), mark))
        if dupes:
            say("        повторов одного пути: %d" % dupes)
        say("        архив НЕ годен для раздачи")
        sys.exit(1)
    say("        сверка состава: всего %d, подписей %d, скриптов %d, бандлов %d"
        % (got["всего"], got[".w3strings"], got[".ws"], got[".bundle"]))


head("Сборка архивов для раздачи")

OUT.mkdir(parents=True, exist_ok=True)

# ---- 1. под Redux ------------------------------------------------------------
name = OUT / ("SetBonusTransfer-Redux-%s.zip" % VER)
with zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED) as z:
    n = 0
    n += add_tree(z, GAME / "mods" / "modSetBonusTransfer", "mods/modSetBonusTransfer")
    n += add_tree(z, GAME / "dlc" / "dlcSetBonusTransfer", "dlc/dlcSetBonusTransfer")
    xml = GAME / "bin" / "config" / "r4game" / "user_config_matrix" / "pc" / "SetBonusTransfer.xml"
    z.write(xml, CFG + "/SetBonusTransfer.xml")
    n += 1
    txt = ("SetBonusTransfer %s — для W3EE Redux\n" % VER
           + "=" * 60 + "\n"
           + README_COMMON.replace("{dlc_keys}",
               "      DlcEnabled_dlc_sbt_001=1     (камни школ)\n")
           + REDUX_TAIL)
    z.writestr("README.txt", txt.encode("utf-8"))
say("   [ok] %-42s файлов %d, %d КБ" % (name.name, n, name.stat().st_size // 1024))
# 22 = 18 (мод: 17 подписей + скрипт) + 2 (dlcSetBonusTransfer: бандл и metadata)
#    + 1 (xml) + 1 (README). Реликты уехали в отдельную закачку.
# Бандл ровно ОДИН. Второго быть не должно: build_dlc.py штатно убирает blob0.bundle
# и metadata.store из mods\modSetBonusTransfer — предметы переехали в dlc\, и копия
# в mods\ устаревший хвост. Если бандлов снова два, значит дополнение не собрано
# и в архив попал этот хвост.
audit_zip(name, {"всего": 22, ".w3strings": 17, ".ws": 1, ".bundle": 1, ".xml": 1},
          "SetBonusTransfer под Redux")

# ---- 1б. дополнение на реликтовые комплекты ----------------------------------
# Отдельная закачка: кода в нём нет ни строчки, только предметы и подписи, и без
# основного мода оно бесполезно.
name = OUT / ("SetBonusTransfer-RelicSets-%s.zip" % VER)
with zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED) as z:
    n = add_tree(z, GAME / "dlc" / "dlcSBTRelics", "dlc/dlcSBTRelics")
    z.writestr("README.txt",
               ("SetBonusTransfer: Relic Sets %s — дополнение на реликтовые комплекты\n" % VER
                + "=" * 60 + "\n" + RELICS_README).encode("utf-8"))
say("   [ok] %-42s файлов %d, %d КБ" % (name.name, n, name.stat().st_size // 1024))
# 20 = 19 (17 подписей + бандл и metadata) + 1 (README). Скриптов и xml тут нет вовсе.
audit_zip(name, {"всего": 20, ".w3strings": 17, ".ws": 0, ".bundle": 1, ".xml": 0},
          "SetBonusTransfer: дополнение на реликты")

# ---- 2. под ваниль -----------------------------------------------------------
vsrc = DIST_V / "modSetBonusTransfer"
if not vsrc.exists():
    say("   [!!] нет ванильной сборки — запустите setbonus\\build_core.py --vanilla")
    sys.exit(1)

name = OUT / ("SetBonusTransfer-Vanilla-%s.zip" % VER)
with zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED) as z:
    n = add_tree(z, vsrc, "mods/modSetBonusTransfer")

    # Подписи ванильной сборки — СВОИ, из dist_vanilla, а не из игры: Redux
    # переписывает сетовые бонусы, и описания камней в двух сборках РАЗНЫЕ.
    # Собираются так:  setbonus/build_item.py --vanilla
    #
    # ⚠️ Отдельно класть их НЕ НАДО: они лежат внутри dist_vanilla, и add_tree
    # выше уже забрал их. Прежний код добавлял их вторым заходом тем же путём,
    # и в архиве оказывалось 17 одинаковых записей.
    vstr = sorted((vsrc / "content").glob("*.w3strings"))
    if len(vstr) < 17:
        say("   [!!] ванильных подписей %d из 17 — запустите setbonus/build_item.py --vanilla"
            % len(vstr))
        sys.exit(1)

    # предметы у обеих сборок одинаковые — берём готовые из игры,
    # но БЕЗ дополнения на реликтовые комплекты: в ванили их нет
    n += add_tree(z, GAME / "dlc" / "dlcSetBonusTransfer", "dlc/dlcSetBonusTransfer")
    z.write(xml, CFG + "/SetBonusTransfer.xml")
    n += 1
    txt = ("SetBonusTransfer %s — для ЧИСТОЙ ванили\n" % VER
           + "=" * 60 + "\n"
           + README_COMMON.replace("{dlc_keys}",
               "      DlcEnabled_dlc_sbt_001=1     (камни школ)\n")
           + VANILLA_TAIL)
    z.writestr("README.txt", txt.encode("utf-8"))
say("   [ok] %-42s файлов %d, %d КБ" % (name.name, n, name.stat().st_size // 1024))
audit_zip(name, {"всего": 22, ".w3strings": 17, ".ws": 1, ".bundle": 1, ".xml": 1},
          "SetBonusTransfer под ваниль")

# ---- 3. ванильные сетовые бонусы ---------------------------------------------
vsb = DIST_V / "modVanillaSetBonuses"
if vsb.exists():
    name = OUT / ("VanillaSetBonuses-%s.zip" % VER)
    with zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED) as z:
        n = 0
        n += add_tree(z, vsb / "content", "mods/modVanillaSetBonuses/content")
        n += add_tree(z, vsb / "bin", "bin")
        z.write(vsb / "README.txt", "README.txt")
        n += 1
    say("   [ok] %-42s файлов %d, %d КБ" % (name.name, n, name.stat().st_size // 1024))
    audit_zip(name, {"всего": 20, ".w3strings": 17, ".ws": 1, ".bundle": 0, ".xml": 1},
              "VanillaSetBonuses")
else:
    say("   [--] ванильных сетовых бонусов нет — запустите build_vanilla.py")

head("ГОТОВО")
say("   %s" % OUT)
say()
say("   ⚠️ Redux-архив и ванильный — РАЗНЫЕ сборки одного мода.")
say("      Вместе не ставятся, у каждого свой README.")
