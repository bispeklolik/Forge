# -*- coding: utf-8 -*-
"""
СПЛОШНАЯ проверка: какие предметы игры относятся к каким комплектам.

Повод — я заявил, что готического, диметриевого и метеоритного комплектов в игре
нет ни одной вещи, а пользователь возразил: «диметриевые вещи у меня в сумке есть,
и рецепты я видел». Первая проверка охватила ДВА хранилища из шестнадцати — этого
мало для слова «нет ни одной».

Здесь читаются ВСЕ бандлы: content0…content12, все папки dlc и все моды. Читалка —
своя, из «Медальона», поэтому распаковывать 35 ГБ на диск не нужно: берутся только
файлы определений предметов.

Печатает: по каждому из 19 ярлыков — сколько вещей, каких разделов, откуда; плюс
отдельно все предметы, в чьём имени есть «dimerit», чтобы отделить материалы
(диметриевый слиток) от комплекта.
"""
import os, re, sys
from pathlib import Path

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
sys.stdout.reconfigure(encoding="utf-8")

from medallion import bundles as B

GAME = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")

TAGS = {
    "LynxSet": "Кот", "GryphonSet": "Грифон", "BearSet": "Медведь",
    "WolfSet": "Волк", "RedWolfSet": "Мантикора", "VampireSet": "Вампир",
    "ViperSet": "Змея", "NetflixSet": "Netflix",
    "TemerianSet": "Темерия", "NilfgaardSet": "Нильфгаард",
    "SkelligeSet": "Скеллиге", "OfieriSet": "Офир", "NewMoonSet": "Новолуние",
    "ElvenSet": "Эльфы", "TigerSet": "Тигр",
    "GothicSetTag": "Готика", "DimeritiumSetTag": "Диметрий",
    "MeteoriteSetTag": "Метеорит", "VampireSetAlt": "Вампир (иной)",
}

WANT = re.compile(r"\.xml$", re.I)
ITEM = re.compile(r"<item\b(.*?)(?:/>|</item>)", re.S)
NAME = re.compile(r'name\s*=\s*"([^"]+)"')
CAT = re.compile(r'category\s*=\s*"([^"]+)"')
TAGBLK = re.compile(r"<tags>(.*?)</tags>", re.S)
DIM = re.compile(r"dimerit", re.I)

found = {t: {} for t in TAGS}     # ярлык -> имя предмета -> (раздел, откуда)
dim_items = {}                    # имя -> (раздел, откуда)
seen_files = 0
skipped = []


def decode(b):
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
        try:
            return b.decode("utf-16")
        except Exception:
            return None
    for enc in ("utf-8", "utf-16"):
        try:
            t = b.decode(enc)
            if "<" in t[:400]:
                return t
        except Exception:
            pass
    return None


def scan_text(t, where):
    global found, dim_items
    for m in ITEM.finditer(t):
        blk = m.group(1)
        nm = NAME.search(blk)
        if not nm:
            continue
        name = nm.group(1)
        cat = CAT.search(blk)
        cat = cat.group(1) if cat else "?"
        if DIM.search(name):
            dim_items.setdefault(name, (cat, where))
        tb = TAGBLK.search(blk)
        if not tb:
            continue
        tags = tb.group(1)
        for tag in TAGS:
            if re.search(r"(?<![A-Za-z_])" + tag + r"(?![A-Za-z_])", tags):
                found[tag].setdefault(name, (cat, where))


def scan_bundle(path, where):
    global seen_files, skipped
    try:
        idx = B.read_index(path)
    except Exception as e:
        skipped.append("%s — индекс: %s" % (where, e))
        return
    for e in idx:
        p = getattr(e, "name", None) or getattr(e, "path", "")
        if not WANT.search(str(p)):
            continue
        if not B.can_extract(e):
            skipped.append("%s :: %s — сжатие не по зубам" % (where, p))
            continue
        try:
            data = B.extract(path, e)
        except Exception as ex:
            skipped.append("%s :: %s — %s" % (where, p, ex))
            continue
        t = decode(data)
        if not t or "<item" not in t:
            continue
        seen_files += 1
        scan_text(t, where)


def bundles_under(root, label):
    out = []
    if not root.exists():
        return out
    for p in sorted(root.rglob("*.bundle")):
        if "Tools" in p.parts or "WitcherScriptMerger" in str(p):
            continue
        # ⛔ Папка на "~" — ВЫКЛЮЧЕННЫЙ мод, игра его не грузит. Один такой
        # (~modSetBonusAll) однажды подсунул ярлык гроссмейстера на все ступени
        # и чуть не породил ложный вывод «мод тиров не работает».
        if p.parent.parent.name.startswith("~"):
            continue
        out.append((p, "%s/%s" % (label, p.parent.parent.name)))
    return out


targets = []
targets += bundles_under(GAME / "content", "игра")
targets += bundles_under(GAME / "dlc", "dlc")
targets += bundles_under(GAME / "mods", "мод")

print("Бандлов к чтению: %d" % len(targets))
for i, (p, where) in enumerate(targets, 1):
    scan_bundle(p, where)
    if i % 10 == 0:
        print("   ...%d/%d" % (i, len(targets)), flush=True)

print()
print("Файлов определений прочитано: %d" % seen_files)
print("=" * 78)
print("КОМПЛЕКТЫ")
print("=" * 78)
for tag, ru in TAGS.items():
    d = found[tag]
    if not d:
        print("%-18s %-14s ВЕЩЕЙ НЕТ" % (ru, tag))
        continue
    cats = {}
    srcs = set()
    for nm, (c, w) in d.items():
        cats.setdefault(c, []).append(nm)
        srcs.add(w)
    print("%-18s %-18s всего %d" % (ru, tag, len(d)))
    for c in sorted(cats):
        print("      %-16s %d   %s" % (c, len(cats[c]), ", ".join(sorted(cats[c])[:3])))
    print("      откуда: %s" % ", ".join(sorted(srcs)))

print()
print("=" * 78)
print("ВСЁ, ГДЕ В ИМЕНИ ЕСТЬ «dimerit» (%d)" % len(dim_items))
print("=" * 78)
for nm in sorted(dim_items):
    c, w = dim_items[nm]
    print("   %-40s %-22s %s" % (nm, c, w))

if skipped:
    print()
    print("НЕ ПРОЧИТАНО (%d) — первые 25:" % len(skipped))
    for s in skipped[:25]:
        print("   " + s)
