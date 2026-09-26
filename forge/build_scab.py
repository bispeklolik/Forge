# -*- coding: utf-8 -*-
"""Карта «меч -> его ножны» для облика ванильного меча (ГД 26.09).

Ножны в игре — отдельная скрытая вещь (категория steel_scabbards /
silver_scabbards), которую движок кладёт в сумку и вешает на скелет вместе
с мечом: раздел <player_override><bound_items> карточки меча. Скрипт кузницы
читать карточки не умеет, поэтому карту собираем здесь и build_lab.py
вшивает её таблицей FRGW_BoundScab.

Читает УСТАНОВЛЕННЫЕ бандлы (ваниль, W3EE, DLC, наш dlcFRGBlanks) — работает
и при запущенной игре. Порядок сборки: build_blanks.py -> build_scab.py ->
build_lab.py (кованые карточки и двойники ножен берутся из собранного DLC).
"""
import io
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
from medallion import bundles as B  # noqa: E402

GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scab_map.json")

# первый встреченный побеждает: W3EE перекрывает ваниль
ROOTS = [os.path.join("mods", "modW3EE", "content"), os.path.join("content", "content0")]
_dlc = os.path.join(GAME, "dlc")
ROOTS += [os.path.join("dlc", d, "content") for d in sorted(os.listdir(_dlc))
          if os.path.isdir(os.path.join(_dlc, d, "content"))]


def bound_of(it):
    """Ножны карточки: сначала раздел игрока, потом общий."""
    for path in ("player_override/bound_items", "bound_items"):
        node = it.find(path)
        if node is not None:
            names = [x.text.strip() for x in node.iter("item") if x.text and x.text.strip()]
            if names:
                return names
    return []


def main():
    swords = {}
    scabs = set()
    for rel in ROOTS:
        base = os.path.join(GAME, rel)
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
                    nm = str(getattr(e, "name", e))
                    if not nm.endswith(".xml") or "gameplay/items" not in nm.replace("\\", "/"):
                        continue
                    try:
                        raw = B.extract(blob, e)
                    except Exception:
                        continue
                    t = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") \
                        else raw.decode("utf-8", "replace")
                    try:
                        doc = ET.fromstring(t)
                    except Exception:
                        continue
                    for it in doc.iter("item"):
                        n, c = it.get("name"), it.get("category")
                        if not n or not c:
                            continue
                        if c in ("steel_scabbards", "silver_scabbards"):
                            scabs.add(n)
                        if c not in ("steelsword", "silversword") or n in swords:
                            continue
                        b = bound_of(it)
                        swords[n] = b[0] if b else ""
    out = {n: s for n, s in sorted(swords.items()) if s}
    bad = [n for n in list(out) + list(out.values()) if "'" in n or "\\" in n]
    if bad:
        raise SystemExit("имена с кавычкой/слэшем не лягут в таблицу: %r" % bad[:5])
    missing = sorted(set(out.values()) - scabs)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
    frg = sum(1 for n in out if n.startswith("FRG "))
    print("мечей с ножнами: %d (кованых %d, прочих %d), разных ножен: %d"
          % (len(out), frg, len(out) - frg, len(set(out.values()))))
    if missing:
        print("ножны без найденной карточки (в игре не наденутся, останутся родные): %d — %s"
              % (len(missing), ", ".join(missing[:8])))
    if frg == 0:
        raise SystemExit("кованых карточек не найдено — DLC кузницы не собран?")
    print("записано:", OUT)


if __name__ == "__main__":
    main()
