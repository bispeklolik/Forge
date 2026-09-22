# -*- coding: utf-8 -*-
"""Карта «вещь -> предыдущая ступень» из крафт-рецептов игры.

Решение пользователя 02.09 («го»): разбор вещи с уровнем возвращает,
помимо жетонов, предыдущую версию вещи — отличная куртка Волка ковалась
из улучшенной, значит при разборе улучшенная лежит внутри и выходит целой.

Правило: prev(X) = ингредиент рецепта X той же категории, что и X сам
(сталь из стали, доспех из доспеха). Слои по приоритету поздний бьёт
ранний: content0 -> dlc -> modW3EE. Выход: prev_data.json.
"""
import io, json, os, sys

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from medallion import bundles as B
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"

# порядок = приоритет: поздние слои ПЕРЕЗАПИСЫВАЮТ рецепты ранних
LAYERS = ("content\\content0", "dlc\\bob\\content", "dlc\\ep1\\content",
          "dlc\\dlcW3EE\\content", "mods\\modW3EE\\content")

item_cat = {}                 # имя вещи -> категория
recipes = {}                  # crafted -> (слой, [ингредиенты])

for li, rel in enumerate(LAYERS):
    base = os.path.join(GAME, rel)
    if not os.path.isdir(base):
        continue
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if not d.startswith("~")]
        for f in files:
            if not f.endswith(".bundle"):
                continue
            blob = os.path.join(root, f)
            try:
                idx = B.read_index(blob)
            except Exception:
                continue
            for e in idx:
                nm = str(getattr(e, "name", e)).replace("\\", "/")
                if not nm.endswith(".xml") or "gameplay" not in nm:
                    continue
                try:
                    raw = B.extract(blob, e)
                except Exception:
                    continue
                t = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") \
                    else raw.decode("utf-8", "replace")
                try:
                    r2 = ET.fromstring(t)
                except Exception:
                    continue
                for it in r2.iter("item"):
                    n = it.get("name")
                    c = it.get("category")
                    if n and c and n not in item_cat:
                        item_cat[n] = c
                for sc in r2.iter("schematic"):
                    crafted = sc.get("craftedItem_name")
                    if not crafted:
                        continue
                    ing = [i.get("item_name") for i in sc.iter("ingredient")
                           if i.get("item_name")]
                    old = recipes.get(crafted)
                    if old is None or li >= old[0]:
                        recipes[crafted] = (li, ing)

prev = {}
for crafted, (_li, ing) in recipes.items():
    ccat = item_cat.get(crafted)
    if not ccat:
        continue
    for i in ing:
        if i != crafted and item_cat.get(i) == ccat:
            prev[crafted] = i
            break

# NG+ копии («NGP X») лезут по той же лестнице: пара добавляется, если ОБЕ
# NG+ карточки существуют в игре. Без этого разбор в NG+ молчал (05.09).
ngp_added = 0
for crafted, prev_item in list(prev.items()):
    a, b = "NGP " + crafted, "NGP " + prev_item
    if a in item_cat and b in item_cat and a not in prev:
        prev[a] = b
        ngp_added += 1

print("карточек:", len(item_cat), "| рецептов:", len(recipes),
      "| лестниц (prev найден):", len(prev), "| из них NG+ пар добавлено:", ngp_added)
for probe in ("Wolf Armor 2", "Wolf Armor 3", "Lynx Armor 2",
              "Bear School steel sword 2", "Viper School steel sword 3"):
    print("  %-28s -> %s" % (probe, prev.get(probe, "—")))

tmp = os.path.join(HERE, "prev_data.json.tmp")
io.open(tmp, "w", encoding="utf-8").write(
    json.dumps(prev, ensure_ascii=False, indent=1, sort_keys=True))
os.replace(tmp, os.path.join(HERE, "prev_data.json"))
print("сохранено: forge/prev_data.json")
