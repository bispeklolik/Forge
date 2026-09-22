# -*- coding: utf-8 -*-
"""Список УНИКАЛЬНЫХ обликов брони для витрины Элихаля (заказ 05.09).

Пользователь: «скины вообще всех уникальных доспехов — тех, которые можно
только скрафтить (ведьмачьи, реликтовые) или найти/купить/получить в
единственном экземпляре». Отбор из donors_armor.json:

  1. вон массовую одежду и обмундирование (Light armor 03r, Boots 012,
     стражники, стартовое, турнирные копии Геральта) — GENERIC;
  2. дедуп по модели НЕ делается (решение пользователя 05.09: «ведьмачьи
     сеты от каждого улучшения сильно отличаются внешним видом — под
     каждый уровень вещи нужен свой облик»). Факт из данных: сапоги,
     перчатки и штаны ступеней 1-2 и 3-4 делят один equip_template
     (s_01_mg__bear_lvl1 и т.д.), нагрудники разные на каждой ступени —
     но жетон даётся на КАЖДУЮ ступень, чтобы ни один вид не пропал;
  3. остальное (ведьмачьи школы, реликты, квестовые, DLC-сеты, наборы
     Redux, модовые скины) — в лавку.

Выход: forge/elihal_looks.json (читает build_blanks.py).
"""
import io, json, os, re, sys

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from medallion import bundles as B
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"

WANT = {d["name"]: d for d in
        json.load(io.open(os.path.join(HERE, "donors_armor.json"), encoding="utf-8"))}

# массовая одежда и обмундирование: не «уникальное», в лавку не идёт
GENERIC = [
    r"^(Light|Medium|Heavy) (armor|boots|gloves|pants) \d+r?(_crafted)?$",
    r"^(Boots|Gloves|Pants) \d+(_crafted)?$",
    r"^Guard Lvl", r"^Knight Geralt", r"^Starting (Armor|Boots|Gloves|Pants)",
    r"^Autogen ", r"^Frock", r"^Gambeson$", r"^Quilted Armor$",
    r"^Nilfgaardian (Armor|Boots|Gloves|Pants) \d+$",
    r"^Relic Heavy 3 ", r"^q108 ",
]


def is_generic(n):
    return any(re.search(p, n) for p in GENERIC)


tpl = {}
LAYERS = [r"content\content0", r"dlc\bob\content", r"dlc\ep1\content",
          r"dlc\dlcW3EE\content", r"dlc\dlc_FrayedCoatV2\content",
          r"dlc\dlc__raven_armor\content", r"dlc\vagabond\content",
          r"mods\modW3EE\content"]
for rel in LAYERS:
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
                if not nm.endswith(".xml") or "items_plus" in nm:
                    continue
                try:
                    raw = B.extract(blob, e)
                except Exception:
                    continue
                t = (raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff")
                     else raw.decode("utf-8", "replace"))
                try:
                    r2 = ET.fromstring(t)
                except Exception:
                    continue
                for it in r2.iter("item"):
                    n = it.get("name")
                    if n in WANT and n not in tpl:
                        tpl[n] = (it.get("equip_template") or "").strip()

picked = []
for n in sorted(WANT):
    if is_generic(n) or not tpl.get(n):
        continue
    picked.append(n)

picked.sort()
tmp = os.path.join(HERE, "elihal_looks.json.tmp")
io.open(tmp, "w", encoding="utf-8").write(json.dumps(picked, ensure_ascii=False, indent=1))
os.replace(tmp, os.path.join(HERE, "elihal_looks.json"))

from collections import Counter
print("обликов в лавке Элихаля:", len(picked),
      "| из", len(WANT), "доноров брони")
print("по слотам:", dict(Counter(WANT[n]["cat"] for n in picked)))
print("сохранено: forge/elihal_looks.json")
