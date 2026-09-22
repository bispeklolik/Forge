# -*- coding: utf-8 -*-
"""Считает живые места вызова тех форм обращения, которые использует опыт."""
import os, re

GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
ROOTS = [os.path.join(GAME, "content", "content0", "scripts"),
         os.path.join(GAME, "mods", "modW3EE", "content", "scripts")]

PATTERNS = {
    "thePlayer.GetItemEquippedOnSlot(": None,
    "thePlayer.inv.": None,
    "theGame.GetGuiManager()": None,
    "LogChannel(": None,
}

hits = {k: [] for k in PATTERNS}

for root in ROOTS:
    for base, _d, fs in os.walk(root):
        for fn in fs:
            if not fn.endswith(".ws"):
                continue
            p = os.path.join(base, fn)
            raw = open(p, "rb").read()
            t = raw.decode("utf-16", "replace") if raw[:2] == b"\xff\xfe" else raw.decode("utf-8", "replace")
            for k in PATTERNS:
                c = t.count(k)
                if c:
                    hits[k].append((os.path.basename(p), c))

for k, lst in hits.items():
    total = sum(c for _f, c in lst)
    mark = "OK" if total else "!!"
    print("[%s] %-34s всего %5d   в %d файлах" % (mark, k, total, len(lst)))
    for f, c in sorted(lst, key=lambda x: -x[1])[:3]:
        print("        %-30s %d" % (f, c))

# объявление поля inv
print()
for root in ROOTS:
    p = os.path.join(root, "game", "player", "playerWitcher.ws")
    if not os.path.exists(p):
        p = os.path.join(root, "game", "player", "r4Player.ws")
    if os.path.exists(p):
        raw = open(p, "rb").read()
        t = raw.decode("utf-16", "replace") if raw[:2] == b"\xff\xfe" else raw.decode("utf-8", "replace")
        for m in re.finditer(r"^.*\binv\s*:\s*CInventoryComponent.*$", t, re.M):
            print("объявление inv:", os.path.basename(p), "|", m.group(0).strip())
