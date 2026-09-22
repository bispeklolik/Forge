# -*- coding: utf-8 -*-
"""
Убирает дополнение из игры и возвращает предметы в папку мода.

Зачем: после установки дополнения в игре появились рывки при стабильном кадре.
Наиболее вероятная причина — два монтировщика, доставшиеся от образца dlc13 и
указывающие на папки, которых в нашем дополнении нет (модели арбалета и элементы
интерфейса). Игра пытается их подгружать и спотыкается.

Что делает:
  1. уносит папку дополнения из dlc\\ в сторону (не удаляет);
  2. выключает его в обоих файлах настроек;
  3. возвращает предметы в мод — там они хотя бы работают в сессии.
"""
import os, re, shutil, subprocess, sys, time
from pathlib import Path

GAME = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")
DOCS = Path(os.environ["USERPROFILE"]) / "Documents" / "The Witcher 3"
DLC = GAME / "dlc" / "dlcSetBonusTransfer"
PARK = Path(r"D:\Apps\w3ee-tweaks\setbonus\parked")
DLC_ID = "dlc_sbt_001"


def say(s=""):
    print(s, flush=True)


def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq witcher3.exe"],
                             capture_output=True, text=True, timeout=25).stdout
        return "witcher3.exe" in out.lower()
    except Exception:
        return False


say("=" * 66)
say("  Откат дополнения")
say("=" * 66)

if game_running():
    say("   ИГРА ЗАПУЩЕНА — закройте её")
    sys.exit(3)

# 1. унести папку
if DLC.exists():
    PARK.mkdir(parents=True, exist_ok=True)
    dst = PARK / ("dlcSetBonusTransfer_" + time.strftime("%Y%m%d-%H%M%S"))
    shutil.move(str(DLC), str(dst))
    say("   [ok] дополнение унесено в %s" % dst)
else:
    say("   [--] папки дополнения нет")

# 2. выключить в настройках
for name in ("user.settings", "dx12user.settings"):
    p = DOCS / name
    if not p.exists():
        continue
    t = p.read_bytes().decode("utf-8", "replace")
    new = re.sub(r"DlcEnabled_%s=\d\r?\n" % DLC_ID, "", t)
    if new != t:
        p.write_bytes(new.encode("utf-8"))
        say("   [ok] %s — запись о дополнении убрана" % name)
    else:
        say("   [--] %s — записи не было" % name)

say()
say("   Теперь запустите build_item.py — он вернёт предметы в мод.")
say("   Проверьте, ушли ли рывки.")
