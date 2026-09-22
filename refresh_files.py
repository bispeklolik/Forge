# -*- coding: utf-8 -*-
"""
Перезаписывает только файлы мода в папке игры (скрипты + XML меню).
Настройки в Документах НЕ трогает — их можно писать лишь при закрытой игре.
Строки берутся из build_mod.py, чтобы не расходились.
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
SCR = os.path.join(GAME, "mods", "modAardShatter", "content", "scripts", "local")
CFG = os.path.join(GAME, "bin", "config", "r4game", "user_config_matrix", "pc")

src = open(os.path.join(HERE, "build_mod.py"), encoding="utf-8").read()

ns = {}
for name in ("CORE", "SIGNS", "FINISHERS", "DISMEMBER", "XML"):
    m = re.search(r'^%s = """(.*?)"""' % name, src, re.S | re.M)
    if not m:
        raise SystemExit("не найден блок %s в build_mod.py" % name)
    exec('%s = """%s"""' % (name, m.group(1)), ns)

os.makedirs(SCR, exist_ok=True)

for fname, key in [("AardShatter - Core.ws", "CORE"),
                   ("AardShatter - Signs.ws", "SIGNS"),
                   ("AardShatter - Finishers.ws", "FINISHERS"),
                   ("AardShatter - Dismember.ws", "DISMEMBER")]:
    data = ns[key].replace("\n", "\r\n").encode("utf-16")
    open(os.path.join(SCR, fname), "wb").write(data)
    print("   [ok] %-32s %6d Б  UTF-16 LE + BOM" % (fname, len(data)))

p = os.path.join(CFG, "AardShatter.xml")
open(p, "wb").write(ns["XML"].replace("\n", "\r\n").encode("utf-8"))
print("   [ok] %-32s %6d Б  UTF-8 без BOM" % ("AardShatter.xml", os.path.getsize(p)))
print()
print("   Настройки НЕ трогались — засев после закрытия игры.")
