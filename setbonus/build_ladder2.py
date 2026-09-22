# -*- coding: utf-8 -*-
"""
ЛЕСЕНКА 2 — подбираем категорию предмета.

Что установлено первой лесенкой (делом, в игре):
    T1 category="armor"    -> ПЕРЕЖИЛ загрузку
    T2 category="upgrade"  -> НЕ пережил
    карточки в остальном совпадают до символа.

То есть виновата КАТЕГОРИЯ. Причём ванильные руны — тоже "upgrade" — переживают
прекрасно; значит игра по-особому обходится с НОВЫМИ предметами этой категории.
Косвенно сходится и с наблюдением: пока камни были "dye", они не пропадали, и
пропадать начали ровно после смены категории на "upgrade" ради значков.

Здесь тот же камень в шести категориях. Нужна та, которая одновременно:
    * переживает загрузку,
    * рисует значок (у "dye" его не было — краски рисуют цветной образец),
    * не засоряет чужой раздел (из-за "dye" пропал рецепт чёрной краски).
"""
import os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
T = "\t"
P = T * 4

ABILITY = "SBT Ladder _Stats"          # объявлено первой лесенкой
ICON = "icons/inventory/ingredients/runes/rune_stribog_greater_64x64.png"
TAGS = "mod_upgrade, mod_dye, SBT_Stone, SBT_Gryphon"

# (имя предмета, категория) — по одному на проверку
CATS = [
    ("SBT C1 misc",    "misc"),
    ("SBT C2 usable",  "usable"),
    ("SBT C3 craft",   "crafting_ingredient"),
    ("SBT C4 alch",    "alchemy_ingredient"),
    ("SBT C5 dye",     "dye"),
    ("SBT C6 quest",   "quest"),
]


def item(name, category):
    s = T * 3 + '<item name="' + name + '"\n'
    s += P + 'category="' + category + '"\n'
    s += P + 'stackable="1"\n'
    s += P + 'grid_size="1"\n'
    s += P + 'icon_path="' + ICON + '"\n'
    s += P + 'localisation_key_name="sbt_st_griffin"\n'
    s += P + 'localisation_key_description="sbt_st_desc"\n'
    s += P + 'price="300" >\n'
    s += P + "<tags>" + TAGS + "</tags>\n"
    s += P + "<base_abilities>\n" + P + T + "<a>" + ABILITY + "</a>\n" + P + "</base_abilities>\n"
    s += T * 3 + "</item>\n"
    return s


LADDER2 = "".join(item(n, c) for n, c in CATS)

if __name__ == "__main__":
    print("=" * 66)
    print("  Лесенка 2: подбор категории")
    print("=" * 66)

    for branch in ("items", "items_plus"):
        p = Path(os.environ["TEMP"]) / "sbt_raw" / "gameplay" / branch / "sbt_items.xml"
        if not p.exists():
            print("   [!!] нет %s — сначала build_item.py" % p)
            sys.exit(1)
        t = p.read_bytes().decode("utf-16")
        if "SBT C1 misc" in t:
            print("   [--] уже вклеено в %s" % branch)
            continue
        t = t.replace("\t\t<items>\r\n", "\t\t<items>\r\n" + LADDER2.replace("\n", "\r\n"))
        p.write_bytes(t.encode("utf-16"))
        print("   [ok] вклеено в %s" % branch)

    print()
    r = subprocess.run([sys.executable, str(HERE / "build_dlc.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in (r.stdout or "").splitlines():
        if any(k in line for k in ("[ok]", "[!!]", "ГОТОВО")):
            print("   " + line.strip())

    print()
    print("   В ИГРЕ:")
    for n, c in CATS:
        print("     additem('%s')%s// %s" % (n, " " * max(1, 22 - len(n)), c))
    print()
    print("   Сохраниться, ВЫЙТИ В МЕНЮ, загрузиться.")
    print("   Сказать: какие остались и у каких был ЗНАЧОК.")
