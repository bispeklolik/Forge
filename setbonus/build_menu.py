# -*- coding: utf-8 -*-
"""
Ставит раздел настроек мода в меню «Модификации».

Три провода, и все три обязательны — без любого раздел просто не появится, молча:
  1. XML раздела в  bin\\config\\r4game\\user_config_matrix\\pc\\
  2. имя этого XML — в ОБА списка dx11filelist.txt и dx12filelist.txt (UTF-16 LE!)
  3. значения по умолчанию — в user.settings И dx12user.settings

⚠️ Файлы настроек игра перезаписывает при выходе, поэтому работаем только при
   закрытой игре.
⚠️ Имя группы «SetBonusTransfer» продублировано внутри .ws — менять только вместе.
"""
import os, shutil, subprocess, sys
from pathlib import Path

GAME = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")
DOCS = Path(os.environ["USERPROFILE"]) / "Documents" / "The Witcher 3"
CFG = GAME / "bin" / "config" / "r4game" / "user_config_matrix" / "pc"

GROUP = "SetBonusTransfer"
XML = GROUP + ".xml"
MENU_PATH = "Mods."          # префикс кладёт раздел в панель «Модификации»
MENU_KEY = "sbt_menu"

# (переменная, ключ подписи, вид, значение по умолчанию)
VARS = [
    ("ShowMessages",   "sbt_messages",  "TOGGLE", "true"),
    ("AllowSwords",    "sbt_swords",    "TOGGLE", "true"),
    ("AllowSetPieces", "sbt_setpieces", "TOGGLE", "true"),
    ("ConsumeStone",   "sbt_consume",   "TOGGLE", "false"),
    ("GrantSchematics", "sbt_grant",    "TOGGLE", "true"),
    # Сила перенесённого бонуса. Настройку ЧИТАЕТ не этот мод, а Tier-Scaled Set
    # Bonuses: он видит на вещи наше число и решает, считать ли силу по тому
    # комплекту, который игрок реально собрал. Объявлена здесь, потому что речь о
    # камнях, и игрок будет искать её тут.
    #   включено  — сила по собранному комплекту (в сумке, на Плотве, в тайнике)
    #   выключено — всегда полная, как было
    ("PowerFromOwnedSet", "sbt_ownedpower", "TOGGLE", "true"),
]


def say(s=""):
    print(s, flush=True)


def head(s):
    say(); say("=" * 68); say("  " + s); say("=" * 68)


def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq witcher3.exe"],
                             capture_output=True, text=True, timeout=25).stdout
        return "witcher3.exe" in out.lower()
    except Exception:
        return False


def make_xml():
    L = ['<?xml version="1.0" encoding="UTF-16"?>', "<UserConfig>"]
    L.append('\t<Group id="%s" displayName="%s%s">' % (GROUP, MENU_PATH, MENU_KEY))
    L.append("\t\t<PresetsArray>")
    L.append('\t\t\t<Preset id="0" displayName="default">')
    for vid, _key, _dt, default in VARS:
        L.append('\t\t\t\t<Entry varId="%s" value="%s" />' % (vid, default))
    L.append("\t\t\t</Preset>")
    L.append("\t\t</PresetsArray>")
    L.append("\t\t<VisibleVars>")
    for vid, key, dt, _default in VARS:
        L.append('\t\t\t<Var overrideGroup="%s" id="%s" displayName="%s" displayType="%s"/>'
                 % (GROUP, vid, key, dt))
    L.append("\t\t</VisibleVars>")
    L.append("\t</Group>")
    L.append("</UserConfig>")
    return "\r\n".join(L) + "\r\n"


head("Раздел настроек мода")

if game_running():
    say("   ИГРА ЗАПУЩЕНА — закройте её: она перезаписывает файлы настроек при выходе")
    sys.exit(3)

# ---- 1. сам XML --------------------------------------------------------------
CFG.mkdir(parents=True, exist_ok=True)
# XML физически в UTF-8 БЕЗ BOM, хотя в прологе объявлен UTF-16 — игра пролог игнорирует.
(CFG / XML).write_bytes(make_xml().encode("utf-8"))
say("   [ok] %s — %d Б, настроек %d" % (XML, (CFG / XML).stat().st_size, len(VARS)))

# ---- 2. оба списка -----------------------------------------------------------
for lst in ("dx11filelist.txt", "dx12filelist.txt"):
    p = CFG / lst
    if not p.exists():
        say("   [!!] нет %s" % lst)
        continue
    raw = p.read_bytes()
    # ⚠️ Списки в UTF-16 LE с BOM. Запись в UTF-8 ломает ВСЕ модовые меню сразу.
    if raw[:2] != b"\xff\xfe":
        say("   [!!] %s не в UTF-16 LE — не трогаю" % lst)
        continue
    txt = raw.decode("utf-16")
    if XML in txt:
        say("   [--] %s — уже вписан" % lst)
        continue
    if not p.with_suffix(p.suffix + ".bak_sbt").exists():
        shutil.copyfile(p, str(p) + ".bak_sbt")
    txt = txt.rstrip("\r\n") + "\r\n" + XML + ";\r\n"
    p.write_bytes(txt.encode("utf-16"))
    say("   [ok] %s — вписан" % lst)

# ---- 3. значения по умолчанию в ОБА файла настроек ---------------------------
for name in ("user.settings", "dx12user.settings"):
    p = DOCS / name
    if not p.exists():
        say("   [--] нет %s" % name)
        continue
    raw = p.read_bytes().decode("utf-8", "replace")   # без BOM, CRLF
    if not (p.parent / (name + ".bak_sbt")).exists():
        shutil.copyfile(p, str(p) + ".bak_sbt")

    import re as _re
    m = _re.search(r"\[%s\]\r?\n(.*?)(?=\r?\n\[|\Z)" % GROUP, raw, _re.S)

    if not m:
        block = "[%s]\r\n" % GROUP + "".join(
            "%s=%s\r\n" % (vid, default) for vid, _k, _dt, default in VARS)
        raw = raw.rstrip("\r\n") + "\r\n" + block
        p.write_bytes(raw.encode("utf-8"))
        say("   [ok] %s — секция создана, %d значений" % (name, len(VARS)))
        continue

    # Секция уже есть. Дописываем только НЕДОСТАЮЩИЕ ключи: значения, которые
    # игрок уже выставил, трогать нельзя, а новая настройка мода без строки в
    # файле осталась бы невидимой в меню.
    have = set(_re.findall(r"^(\w+)\s*=", m.group(1), _re.M))
    missing = [(vid, d) for vid, _k, _dt, d in VARS if vid not in have]
    if not missing:
        say("   [--] %s — все значения на месте" % name)
        continue

    add = "".join("%s=%s\r\n" % (vid, d) for vid, d in missing)
    raw = raw[:m.end(1)].rstrip("\r\n") + "\r\n" + add + raw[m.end(1):].lstrip("\r\n")
    p.write_bytes(raw.encode("utf-8"))
    say("   [ok] %s — дописано: %s" % (name, ", ".join(v for v, _d in missing)))

head("ГОТОВО")
say("   В игре: Настройки -> Модификации -> «Перенос сетовых бонусов»")
say()
for vid, key, _dt, default in VARS:
    say("     %-16s по умолчанию %-6s (%s)" % (vid, default, key))
say()
say("   ⚠️ Подписи берутся из .w3strings мода — если раздел появился, а строки пустые,")
say("      значит не собраны подписи: запустите build_item.py")
