# -*- coding: utf-8 -*-
"""
Собирает файлы строк для modAardShatter, чтобы подписи в меню были текстом,
а не пустотой. Без .w3strings игра подписи не рисует вообще — это правило,
а не особенность нашего мода.

Требования формата (из docs.w3strings):
  - CSV в UTF-8 БЕЗ BOM
  - ключи только из a-z0-9_ , регистр не важен
  - идентификаторы вида 211<id-space><000..999>
"""
import os, subprocess, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXE  = os.path.join(HERE, "tools", "w3strings", "w3strings.exe")
GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
MODC = os.path.join(GAME, "mods", "modAardShatter", "content")
OUT  = os.path.join(HERE, "strings")

ID_SPACE = 4471          # свой диапазон, чтобы не столкнуться с чужими модами
BASE     = 2114471000

# ключ, русский текст, английский текст
STRINGS = [
    ("ash_menu",              "Разрыв Аардом",                                  "Aard Shatter"),
    ("ash_humanpoise",        "Разрывать людей со сбитой стойкой",              "Shatter humans with broken poise"),
    ("ash_humanhp",           "   ...только ниже этого % здоровья",             "   ...only below this health %"),
    ("ash_killshatter",       "Разрывать всех, кого добил Аард",                "Shatter anything Aard kills"),
    ("ash_killshatterhumans", "   ...включая людей",                            "   ...including humans"),
    ("ash_slomochance",       "Шанс замедления времени при разрыве",            "Slow motion chance on shatter"),
    ("ash_slomoscale",        "   ...сила замедления (меньше = сильнее)",       "   ...strength (lower = stronger)"),
    ("ash_slomotime",         "   ...длительность, сек",                        "   ...duration, sec"),
    ("ash_finvariety",        "Разнообразие добиваний: 0 выкл, 1 ваниль, 2 макс","Finisher variety: 0 off, 1 vanilla, 2 max"),
    ("ash_shatterscale",      "   ...крутизна кривой шанса (100 = один к одному)", "   ...chance curve scale (100 = one to one)"),
    ("ash_ignipoise",         "Разрывать людей Игни (та же логика)",               "Igni shatters humans too"),
    ("ash_ignikill",          "Разрывать всех, кого добил Игни",                   "Shatter anything Igni kills"),
    ("ash_fixignilatch",      "Чинить баг: Eruption убивает добивания",            "Fix: Eruption disables finishers"),
    ("ash_armordism",         "Расчленять бронированных людей",                 "Dismember armoured humans"),
    ("ash_armorchance",       "   ...шанс для бронированных",                   "   ...chance for armoured"),
]


def say(s=""):
    print(s, flush=True)


def make_csv(lang, col):
    lines = ["meta[language=%s]" % lang,
             "; id      |key(hex)|key(str)| text"]
    out = [";" + lines[0], lines[1]]
    for i, item in enumerate(STRINGS):
        out.append("%d|        |%s|%s" % (BASE + i, item[0], item[col]))
    path = os.path.join(OUT, "%s.csv" % lang)
    with open(path, "wb") as f:
        f.write(("\r\n".join(out) + "\r\n").encode("utf-8"))   # UTF-8 без BOM
    return path


if not os.path.exists(EXE):
    say("НЕ НАЙДЕН кодировщик: %s" % EXE); sys.exit(1)

os.makedirs(OUT, exist_ok=True)
say("=" * 62)
say("  СБОРКА СТРОК modAardShatter (id-space %d)" % ID_SPACE)
say("=" * 62)

ok = 0
for lang, col in (("ru", 1), ("en", 2)):
    csv = make_csv(lang, col)
    say()
    say("--- %s ---" % lang)
    r = subprocess.run([EXE, "--encode", csv, "--id-space", str(ID_SPACE)],
                       capture_output=True, cwd=OUT)
    out = (r.stdout or b"").decode("utf-8", "replace") + (r.stderr or b"").decode("utf-8", "replace")
    for line in out.strip().splitlines()[-6:]:
        say("   " + line)

    produced = csv + ".w3strings"
    if not os.path.exists(produced):
        say("   [!!] файл не создан"); continue

    dest = os.path.join(MODC, "%s.w3strings" % lang)
    shutil.copyfile(produced, dest)
    say("   [ok] %s.w3strings -> мод (%d Б)" % (lang, os.path.getsize(dest)))
    ok += 1

say()
say("=" * 62)
say("  Готово: языков собрано %d из 2" % ok)
say("  Ключи: " + ", ".join(s[0] for s in STRINGS[:3]) + " ...")
say("=" * 62)
