# -*- coding: utf-8 -*-
"""
Кто какой диапазон подписей (id-space) занимает во всей сборке.

Повод: я выдал дополнению на реликты номер 4477, посмотрев только на основной мод
камней (4476) — и не заметив, что 4477 уже занят НАШИМ ЖЕ modW3EERedux_TierBonuses.
Подписи двух модов полезли друг на друга.

Запускать ПЕРЕД тем, как назначить новому моду номер.
"""
import collections, io, os, shutil, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8")

GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
ENC = r"D:\Apps\w3ee-tweaks\tools\w3strings\w3strings.exe"
WORK = os.path.join(os.environ["TEMP"], "idscan")

if os.path.exists(WORK):
    shutil.rmtree(WORK)
os.makedirs(WORK)
os.chdir(WORK)

spaces = collections.defaultdict(set)
read = 0

for base in (os.path.join(GAME, "mods"), os.path.join(GAME, "dlc")):
    if not os.path.exists(base):
        continue
    for d in sorted(os.listdir(base)):
        src = os.path.join(base, d, "content", "en.w3strings")
        if not os.path.exists(src):
            continue
        dst = "%s_en.w3strings" % d
        shutil.copyfile(src, dst)
        subprocess.run([ENC, "--decode", dst], capture_output=True)
        csv = dst + ".csv"
        if not os.path.exists(csv):
            continue
        read += 1
        for line in io.open(csv, encoding="utf-8", errors="replace").read().splitlines():
            if line.startswith(";") or "|" not in line:
                continue
            i = line.split("|")[0].strip()
            # id вида 211<space><номер>
            if i.isdigit() and len(i) >= 10 and i.startswith("211"):
                spaces[i[3:7]].add(d)

print("Модов и дополнений со своими подписями прочитано: %d" % read)
print()
print("%-9s %s" % ("id-space", "кто занимает"))
for s in sorted(spaces):
    mark = "  ⛔ СТОЛКНОВЕНИЕ" if len(spaces[s]) > 1 else ""
    print("%-9s %s%s" % (s, ", ".join(sorted(spaces[s])), mark))

print()
free = [str(x) for x in range(4400, 4600) if str(x) not in spaces]
print("Свободные в 4400..4599 (первые 20):")
print("   " + " ".join(free[:20]))
