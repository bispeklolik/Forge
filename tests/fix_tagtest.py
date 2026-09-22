# -*- coding: utf-8 -*-
"""
Перезаписывает ASHTagTest.ws с НАСТОЯЩИМИ табуляциями.

Прошлый заход вытащил текст регулярным выражением как сырую строку, и \t
остались двумя символами. Здесь литерал вычисляется через exec, как это
делает refresh_files.py, — тогда escape-последовательности обрабатываются.

Бандл опыта с предметом НЕ трогаем: он собран родным упаковщиком игры.
"""
import os, re, subprocess, sys

GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(GAME, "mods", "modASHTagTest", "content", "scripts", "local", "ASHTagTest.ws")


def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq witcher3.exe"],
                             capture_output=True, text=True, timeout=25).stdout
        return "witcher3.exe" in out.lower()
    except Exception:
        return False


# Запрет на работу при запущенной игре тут НЕ нужен: скрипт пишет только .ws,
# а они читаются и компилируются при СТАРТЕ игры. Запрет обязателен лишь для
# файлов настроек — их игра перезаписывает при выходе.
if game_running():
    print("   игра запущена — это нормально, .ws подхватится при следующем старте")

src = open(os.path.join(HERE, "build_tests.py"), encoding="utf-8").read()
m = re.search(r'^TAGWS = """(.*?)"""', src, re.S | re.M)
if not m:
    raise SystemExit("не найден блок TAGWS")

ns = {}
exec('TAGWS = """%s"""' % m.group(1), ns)   # <- вот здесь \t станет табом
code = ns["TAGWS"]

if "\\t" in code:
    raise SystemExit("в коде остались буквальные обратные слэши — не записываю")

os.makedirs(os.path.dirname(DST), exist_ok=True)
data = code.replace("\n", "\r\n").encode("utf-16")
open(DST, "wb").write(data)

print("   записан: ASHTagTest.ws  %d Б" % len(data))
print("   настоящих табуляций:", code.count("\t"))
print("   буквальных '\\t':", code.count("\\t"))
print("   BOM:", data[:2].hex(), "(ждём fffe)")
print()
print("   Первые строки функции:")
for line in code.split("\n")[10:16]:
    print("      " + line.replace("\t", "→   "))
