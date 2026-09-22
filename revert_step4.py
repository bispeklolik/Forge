# -*- coding: utf-8 -*-
"""
Точечный откат ШАГА 4 — «Сетовые бонусы по тирам» — из файлов W3EE.

Нужен потому, что эта правка переехала в отдельный мод
modW3EERedux_TierBonuses. Если оставить обе, ослабление применится ДВАЖДЫ.

Штатный apply.py --revert возвращает файлы из бэкапа целиком и снёс бы заодно
все остальные правки, поэтому здесь идёт обратная замена по парам
«стало → было», которые лежат в patches.json.

  py -3 revert_step4.py --dry-run   только показать
  py -3 revert_step4.py             выполнить
"""
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PATCHES = os.path.join(HERE, "patches.json")
DRY = "--dry-run" in sys.argv


def say(s=""):
    print(s, flush=True)


def read_file(path, encoding):
    raw = open(path, "rb").read()
    if encoding == "utf16":
        if raw[:2] == b"\xff\xfe":
            return raw[2:].decode("utf-16-le"), b"\xff\xfe", "utf-16-le"
        if raw[:2] == b"\xfe\xff":
            return raw[2:].decode("utf-16-be"), b"\xfe\xff", "utf-16-be"
        return raw.decode("utf-16-le"), b"", "utf-16-le"
    if raw[:3] == b"\xef\xbb\xbf":
        return raw[3:].decode("utf-8"), b"\xef\xbb\xbf", "utf-8"
    return raw.decode("utf-8", "replace"), b"", "utf-8"


def write_file(path, text, bom, codec):
    open(path, "wb").write(bom + text.encode(codec))


def newline_of(text):
    if "\r\n" in text:
        return "\r\n"
    return "\n"


def game_running():
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq witcher3.exe"],
                       capture_output=True, text=True, errors="replace")
    return "witcher3" in (r.stdout or "").lower()


steps = [p for p in json.load(open(PATCHES, encoding="utf-8"))
         if str(p.get("id", "")).startswith("4.")]
steps.reverse()          # снимаем в обратном порядке применения

say("=" * 66)
say("  ОТКАТ ШАГА 4 из файлов W3EE%s" % ("  (только показ)" if DRY else ""))
say("=" * 66)
say("  правок в шаге: %d" % len(steps))

if not DRY and game_running():
    say("  Игра запущена. Закрой её."); sys.exit(3)

done = already = drift = 0
for p in steps:
    path = p["file"]
    name = os.path.basename(path)
    if not os.path.exists(path):
        say("  [нет файла] %-34s %s" % (p["id"], name)); drift += 1; continue

    text, bom, codec = read_file(path, p.get("encoding", "utf8"))
    nl = newline_of(text)
    before = p["before"].replace("\n", nl)
    after = p["after"].replace("\n", nl)

    if after not in text:
        if before in text:
            say("  [уже откачено] %-31s %s" % (p["id"], name)); already += 1
        else:
            say("  [!! НЕ НАЙДЕНО] %-30s %s" % (p["id"], name)); drift += 1
        continue

    if text.count(after) != 1:
        say("  [!! неоднозначно, %d совпадений] %-14s %s" % (text.count(after), p["id"], name))
        drift += 1
        continue

    if not DRY:
        write_file(path, text.replace(after, before, 1), bom, codec)
    say("  [ok] %-40s %s" % (p["id"], name))
    done += 1

say()
say("  откачено: %d, уже было: %d, расхождений: %d" % (done, already, drift))
if DRY:
    say("  Ничего не записано.")
elif drift:
    say("  ⚠️ Есть расхождения — проверь их прежде чем запускать игру.")
else:
    say("  Готово. Ослабление теперь делает только modW3EERedux_TierBonuses.")
