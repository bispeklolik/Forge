# -*- coding: utf-8 -*-
"""
Переход с форка «NO INJURIES NO BLEEDING» на ОРИГИНАЛЬНЫЙ W3EE Redux.
Профиль А: увечья управляются тумблером в меню, кровотечения возвращаются.

Ничего не делает, если запущена игра. Все размеры сверяются с эталоном:
несовпадение = остановка до записи следующего шага.
"""
import os, sys, shutil, subprocess, zipfile, io

GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
ZIP  = r"C:\Users\New\Downloads\Redux for W3EE (NextGen) 5802 1.47 2026-07-04T17-50Z xiGk2gInk.zip"
BK   = r"D:\W3EE-backup-before-migration"
HERE = os.path.dirname(os.path.abspath(__file__))

MODW = os.path.join(GAME, "mods", "modW3EE", "content", "scripts")
MERG = os.path.join(GAME, "mods", "mod0000_MergedFiles", "content", "scripts")

INJ  = os.path.join(MODW, "local", "W3EE - Injuries.ws")
ACT  = os.path.join(MODW, "game", "actor.ws")
EFF  = os.path.join(MODW, "game", "gameplay", "effects", "effectManager.ws")
PW_M = os.path.join(MODW, "game", "player", "playerWitcher.ws")
PW_G = os.path.join(MERG, "game", "player", "playerWitcher.ws")

# путь в архиве -> куда класть -> ожидаемый размер
FROM_ZIP = [
    ("mods/modW3EE/content/scripts/local/W3EE - Injuries.ws", INJ, 57016),
    ("mods/modW3EE/content/scripts/game/actor.ws",            ACT, 452852),
    ("mods/modW3EE/content/scripts/game/gameplay/effects/effectManager.ws", EFF, 113146),
]

# бэкапы, заражённые форком: их надо снести, иначе «Откатить правки» вернёт форк
KILL_BACKUPS = [INJ + ".orig_w3ee_tweaks", EFF + ".orig_w3ee_tweaks"]

# playerWitcher: живые файлы и бэкапы -> ожидаемый размер после чистки
CLEAN = [
    (PW_M,                          938254),
    (PW_G,                          938888),
    (PW_M + ".orig_w3ee_tweaks",    930604),
    (PW_G + ".orig_w3ee_tweaks",    931238),
]

FINAL = [(INJ, 57184), (EFF, 113152)]

errors = []

def say(s=""):
    print(s, flush=True)

def head(s):
    say(); say("=" * 70); say("  " + s); say("=" * 70)

def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq witcher3.exe"],
                             capture_output=True, text=True, timeout=25).stdout
        return "witcher3.exe" in out.lower()
    except Exception:
        return False

def size(p):
    return os.path.getsize(p) if os.path.exists(p) else -1

def check(path, want, what):
    got = size(path)
    ok = (got == want)
    say("   %-9s %-46s %s" % ("[OK]" if ok else "[!!]",
                              os.path.basename(path),
                              ("%d Б" % got) if ok else ("%d Б, ждали %d" % (got, want))))
    if not ok:
        errors.append("%s: %s" % (what, os.path.basename(path)))
    return ok


head("ПЕРЕХОД НА ОРИГИНАЛЬНЫЙ W3EE REDUX (профиль А)")

if game_running():
    say()
    say("  ИГРА ЗАПУЩЕНА. Закройте Ведьмака полностью и запустите этот файл снова.")
    say("  Переход затрагивает 7 файлов сразу — останавливаться на середине нельзя.")
    sys.exit(3)

if not os.path.exists(ZIP):
    say("  НЕ НАЙДЕН архив оригинала:"); say("  " + ZIP); sys.exit(2)


# ---- 1. страховка -------------------------------------------------------
head("Шаг 1. Страховка")
if os.path.exists(BK):
    say("   копия уже существует, оставляю как есть: %s" % BK)
else:
    os.makedirs(BK, exist_ok=True)
    shutil.copytree(MODW, os.path.join(BK, "modW3EE-scripts"))
    shutil.copytree(MERG, os.path.join(BK, "merged-scripts"))
    n = sum(len(f) for _, _, f in os.walk(BK))
    say("   создана: %s  (%d файлов)" % (BK, n))


# ---- 2. три файла из оригинального архива -------------------------------
head("Шаг 2. Забираю три файла из оригинального архива")
with zipfile.ZipFile(ZIP) as z:
    names = {n.replace("\\", "/"): n for n in z.namelist()}
    for want, dest, _sz in FROM_ZIP:
        real = names.get(want)
        if not real:
            say("   [!!] нет в архиве: %s" % want); errors.append("нет в архиве: " + want); continue
        data = z.read(real)
        with open(dest, "wb") as f:
            f.write(data)
        say("   [ok] %s  (%d Б)" % (os.path.basename(dest), len(data)))

say(); say("   Проверка размеров:")
for _w, dest, sz in FROM_ZIP:
    check(dest, sz, "шаг 2")
if errors:
    say(); say("  ОСТАНОВКА: размеры не сошлись. Ничего дальше не трогаю."); sys.exit(1)


# ---- 3. заражённые бэкапы ----------------------------------------------
head("Шаг 3. Удаляю бэкапы, заражённые форком")
for p in KILL_BACKUPS:
    if os.path.exists(p):
        os.remove(p); say("   [ok] удалён %s" % os.path.basename(p))
    else:
        say("   [--] уже нет  %s" % os.path.basename(p))


# ---- 4. чистка playerWitcher -------------------------------------------
head("Шаг 4. Убираю строки форка из playerWitcher (2 живых файла + 2 бэкапа)")

def clean(path):
    raw = open(path, "rb").read()
    if raw[:2] != b"\xff\xfe":
        raise RuntimeError("не UTF-16 LE: " + path)
    txt = raw.decode("utf-16")
    parts = txt.split("\r\n")
    if parts and parts[-1] == "":
        parts.pop()
    keep, cut = [], 0
    for line in parts:
        if "ClearInjuries" in line or "RemoveAllBuffsOfType(EET_Bleeding" in line:
            cut += 1
            continue
        keep.append(line)
    shutil.copyfile(path, path + ".beforeMigration")
    out = ("\r\n".join(keep) + "\r\n").encode("utf-16")
    open(path, "wb").write(out)
    return len(parts), len(keep), cut

for path, want in CLEAN:
    if not os.path.exists(path):
        say("   [!!] нет файла: %s" % path); errors.append("нет файла " + path); continue
    было, стало, срезано = clean(path)
    say("   %-46s %d -> %d строк (убрано %d)" % (os.path.basename(path), было, стало, срезано))

say(); say("   Проверка размеров:")
for path, want in CLEAN:
    check(path, want, "шаг 4")
if errors:
    say(); say("  ОСТАНОВКА: размеры не сошлись.")
    say("  Откат: файлы .beforeMigration лежат рядом с каждым."); sys.exit(1)


# ---- 5. вернуть свои правки в заменённые файлы --------------------------
head("Шаг 5. Возвращаю свои правки в заменённые файлы (1.3 и 4.8)")
r = subprocess.run([sys.executable, os.path.join(HERE, "apply.py"), "--ids", "1.3,4.8"],
                   cwd=HERE, capture_output=True, text=True)
for line in (r.stdout or "").splitlines()[-14:]:
    say("   " + line)
if r.returncode != 0:
    say(); say("  apply.py вернул код %d" % r.returncode); errors.append("apply.py")

say(); say("   Проверка размеров:")
for path, want in FINAL:
    check(path, want, "шаг 5")


# ---- итог ---------------------------------------------------------------
head("ИТОГ")
if errors:
    say("   ЕСТЬ ПРОБЛЕМЫ:")
    for e in errors:
        say("     - " + e)
    say()
    say("   Откат: верните папки из %s" % BK)
    sys.exit(1)

say("   ПЕРЕХОД ВЫПОЛНЕН. Стоит оригинальный W3EE Redux, все правки на месте.")
say()
say("   Дальше в игре:")
say("     1. Запустить игру. Дошла до меню — скрипты скомпилировались.")
say("     2. Опции -> Моды -> W3EE -> Gameplay -> Abilities -> Injuries")
say("        Там три строки: слайдер шанса, ТУМБЛЕР (средний), тумблер сообщений.")
say("        Включите средний тумблер, если увечья не нужны.")
say("     3. Кровотечения теперь работают — это сознательный выбор, тумблера для них нет.")
say()
say("   Страховка: %s" % BK)
say("   Плюс .beforeMigration рядом с каждым правленым playerWitcher.")
