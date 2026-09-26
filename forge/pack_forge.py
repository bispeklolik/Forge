# -*- coding: utf-8 -*-
"""Релизный архив кузницы «Путь клинка» для Nexus.

Кладёт в архив то, что ДОЛЖНО там лежать, и после записи открывает архив
заново и пересчитывает состав (урок SetBonusTransfer: подписи забывались,
тестовые хвосты ехали в архив — см. заметку witcher3-release-packaging).

    python pack_forge.py            основной архив (скрипт + пакет предметов)
                                    и архивы дополнений с обликами из чужих
                                    модов — их выкладывать ТОЛЬКО с разрешения
                                    авторов (TW2 Gear; Perfect KM и доспех
                                    Весемира). Основной архив чужих моделей
                                    не содержит: жетоны этих обликов лавки
                                    предлагают, только когда дополнение стоит.

Перед запуском: build_blanks.py (игра закрыта) -> build_scab.py -> build_lab.py.
"""
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
GAME = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")
OUT = Path(r"D:\Apps\w3ee-mods") / "Архивы по отдельности"
VER = "1.0"
NAME = "PathOfTheBlade-Forge"

SCRIPT = GAME / "mods" / "modForgeLab" / "content" / "scripts" / "local" / "ForgeLab.ws"
CORE_DLC = ["dlcFRGBlanks"]
# дополнения с чужими моделями: имя архива -> папки DLC
ADDONS = {"Looks-TW2Gear": ["dlcFRGTW2"],
          "Looks-KaerMorhen": ["dlcFRGZmeya", "dlcFRGVesemir"]}

# ровно столько языков кладёт build_blanks.py
LANGS = 17


def say(s=""):
    print(s, flush=True)


def fail(s):
    say("[!!] " + s)
    sys.exit(1)


def add_tree(z, src, prefix):
    n = 0
    for p in sorted(src.rglob("*")):
        if p.is_file():
            z.write(p, prefix + "/" + p.relative_to(src).as_posix())
            n += 1
    return n


def check(path, want):
    """Открыть записанный архив заново и пересчитать состав."""
    z = zipfile.ZipFile(path)
    names = z.namelist()
    if len(names) != len(set(names)):
        fail("%s: один путь лежит дважды" % path.name)
    got = {
        "всего": len(names),
        "скрипт": sum(1 for n in names if n.endswith(".ws")),
        "подписи": sum(1 for n in names if n.endswith(".w3strings")),
        "бандлы": sum(1 for n in names if n.endswith(".bundle")),
        "паспорта": sum(1 for n in names if n.endswith("metadata.store")),
        "readme": sum(1 for n in names if n.lower().startswith("readme")),
    }
    bad = {k: (got[k], v) for k, v in want.items() if got[k] != v}
    for k in sorted(got):
        say("      %-9s %d%s" % (k, got[k], "   <-- ждали %d" % want[k] if k in bad else ""))
    if bad:
        fail("%s: состав не сошёлся" % path.name)
    ws = [n for n in names if n.endswith(".ws")]
    for n in ws:
        body = z.read(n).decode("utf-16")
        # тестовые хвосты не едут в релиз
        for probe in ("frgswtest_ext", "items_plus\\frgswtest", "frgvtest", "'frg_swtest'"):
            if probe in body:
                fail("%s: в скрипте тестовый след %r" % (n, probe))
    return got


def main():
    if not SCRIPT.exists():
        fail("нет скрипта %s — сначала build_lab.py" % SCRIPT)
    for d in CORE_DLC + [x for v in ADDONS.values() for x in v]:
        if not (GAME / "dlc" / d / "content" / "blob0.bundle").exists():
            fail("нет пакета dlc/%s — сначала его сборщик" % d)
    readme_ru = (ROOT / "release" / "README_RU.txt")
    readme_en = (ROOT / "release" / "README_EN.txt")
    for r in (readme_ru, readme_en):
        if not r.exists():
            fail("нет %s" % r)

    OUT.mkdir(parents=True, exist_ok=True)
    core = OUT / ("%s-%s.zip" % (NAME, VER))
    say("== %s" % core.name)
    with zipfile.ZipFile(core, "w", zipfile.ZIP_DEFLATED) as z:
        # ТОЛЬКО скрипт: blob0.bundle/metadata.store в папке мода — тестовый
        # хвост 22.09 (расширение Аэрондита), в релиз не идёт
        z.write(SCRIPT, "mods/modForgeLab/content/scripts/local/ForgeLab.ws")
        n = 1
        for d in CORE_DLC:
            n += add_tree(z, GAME / "dlc" / d, "dlc/" + d)
        z.write(readme_ru, "README_RU.txt")
        z.write(readme_en, "README_EN.txt")
    check(core, {"скрипт": 1, "подписи": LANGS * len(CORE_DLC),
                 "бандлы": 2 * len(CORE_DLC), "паспорта": len(CORE_DLC), "readme": 2})

    for key, dlcs in ADDONS.items():
        pack = OUT / ("%s-%s-%s.zip" % (NAME, key, VER))
        rd = ROOT / "release" / ("README_%s.txt" % key)
        if not rd.exists():
            fail("нет %s" % rd)
        say("== %s" % pack.name)
        with zipfile.ZipFile(pack, "w", zipfile.ZIP_DEFLATED) as z:
            for d in dlcs:
                add_tree(z, GAME / "dlc" / d, "dlc/" + d)
            z.write(rd, "README.txt")
        names = zipfile.ZipFile(pack).namelist()
        if len(names) != len(set(names)):
            fail("%s: один путь лежит дважды" % pack.name)
        if any(n.endswith(".ws") for n in names) or not any(n.endswith("blob0.bundle") for n in names):
            fail("%s: состав не тот (скрипт внутри или нет бандла)" % pack.name)
        say("      всего %d файлов, папок DLC %d" % (len(names), len({n.split("/")[1] for n in names if n.startswith("dlc/")})))
    say("готово: %s" % OUT)


if __name__ == "__main__":
    main()
