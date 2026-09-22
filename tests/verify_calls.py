# -*- coding: utf-8 -*-
"""Сверяет каждый вызов из ASHTagTest.ws с объявлениями в скриптах игры."""
import os, re

GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
ROOTS = [os.path.join(GAME, "content", "content0", "scripts"),
         os.path.join(GAME, "mods", "modW3EE", "content", "scripts")]

WANT = ["ShowNotification", "AddItemTag", "ItemHasTag",
        "GetItemModifierInt", "SetItemModifierInt", "GetItemEquippedOnSlot"]

decls = {w: [] for w in WANT}

for root in ROOTS:
    for base, _d, fs in os.walk(root):
        for fn in fs:
            if not fn.endswith(".ws"):
                continue
            p = os.path.join(base, fn)
            raw = open(p, "rb").read()
            t = raw.decode("utf-16", "replace") if raw[:2] == b"\xff\xfe" else raw.decode("utf-8", "replace")
            for w in WANT:
                for m in re.finditer(r"^[ \t]*(?:public |private |protected |final |latent |import )*"
                                     r"function\s+%s\s*\((.*?)\)[^\n{]*" % w, t, re.M):
                    decls[w].append((os.path.basename(p), m.group(0).strip()))

for w in WANT:
    print("=" * 70)
    print(w, "— объявлений:", len(decls[w]))
    seen = set()
    for fname, line in decls[w]:
        key = line
        if key in seen:
            continue
        seen.add(key)
        print("   %-28s %s" % (fname, line[:150]))
    if not decls[w]:
        print("   !! НЕ НАЙДЕНО")
print("=" * 70)

# сколько exec-функций объявлено вне класса — подтверждение, что так можно
n = 0
for root in ROOTS:
    for base, _d, fs in os.walk(root):
        for fn in fs:
            if fn.endswith(".ws"):
                raw = open(os.path.join(base, fn), "rb").read()
                t = raw.decode("utf-16", "replace") if raw[:2] == b"\xff\xfe" else raw.decode("utf-8", "replace")
                n += len(re.findall(r"^exec function\s", t, re.M))
print("глобальных 'exec function' в сборке:", n)
