# -*- coding: utf-8 -*-
r"""
Собирает пять отдельных модов и ставит их в игру вместо старого бандла
modAardShatter.

Ключ --stage-only собирает только dist\ и не трогает игру — этим можно
пользоваться при запущенной игре.

Порядок:
  1. проверка, что игра закрыта, и сверка описаний
  2. сборка в dist\<мод>\ — там уже готовое дерево для архива
  3. снятие старого бандла (папка уезжает в backup\, не удаляется)
  4. установка пяти модов, регистрация в filelist и mods.settings
  5. перенос уже выставленных настроек из [AardShatter] в новые группы

Запускать ТОЛЬКО при закрытой игре: на выходе она перезаписывает user.settings.
"""
import os, io, sys, shutil, subprocess, datetime, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from spec import GAME, LOCALES, MENU_PATH, MENU_ROOT, MODS, TR, keys_of

SRC   = os.path.join(ROOT, "src")
DIST  = os.path.join(ROOT, "dist")
WORK  = os.path.join(ROOT, "strings_work")
BAK   = os.path.join(ROOT, "backup")
EXE   = os.path.join(ROOT, "tools", "w3strings", "w3strings.exe")

CFG   = os.path.join(GAME, "bin", "config", "r4game", "user_config_matrix", "pc")
MODS_DIR = os.path.join(GAME, "mods")
DOCS  = os.path.join(os.path.expanduser("~"), "Documents", "The Witcher 3")

# Всё, что осталось от прежних имён и должно быть снято при установке.
# Бандл modAardShatter плюс первая, непрефиксованная версия разделённых модов.
LEGACY_MODS = ["modAardShatter"] + [m["oldmod"] for m in MODS if m.get("oldmod")]
LEGACY_XML  = ["AardShatter.xml"] + ["%s.xml" % m["oldgroup"] for m in MODS if m.get("oldgroup")]

# старая настройка -> (новая группа, новое имя)
MIGRATE = {
    "HumanPoise":        ("SignShatter",      "HumanPoise"),
    "HumanHP":           ("SignShatter",      "HumanHP"),
    "ShatterScale":      ("SignShatter",      "ShatterScale"),
    "KillShatter":       ("SignShatter",      "KillShatter"),
    "KillShatterHumans": ("SignShatter",      "KillShatterHumans"),
    "IgniPoise":         ("SignShatter",      "IgniPoise"),
    "IgniKill":          ("SignShatter",      "IgniKill"),
    "SloMoChance":       ("SignShatter",      "SloMoChance"),
    "SloMoScale":        ("SignShatter",      "SloMoScale"),
    "SloMoTime":         ("SignShatter",      "SloMoTime"),
    "ArmorDism":         ("DismemberAnyone",  "ArmorDism"),
    "ArmorChance":       ("DismemberAnyone",  "ArmorChance"),
    "FinVariety":        ("FinisherVariety",  "Mode"),
    "MetaPicker":        ("MetamorphPicker",  "Enabled"),
    # FixIgniLatch не переносится: у modFinisherFix настроек нет
}


def say(s=""):
    print(s, flush=True)


def head(t):
    say(); say("=" * 66); say("  " + t); say("=" * 66)


def game_running():
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq witcher3.exe"],
                       capture_output=True, text=True, errors="replace")
    return "witcher3" in (r.stdout or "").lower()


# ---------------------------------------------------------------------------
# 1. Сверка описаний
# ---------------------------------------------------------------------------

def validate():
    bad = 0
    seen_group, seen_ids, seen_keys = {}, {}, {}

    for m in MODS:
        if m["group"]:
            if m["group"] in seen_group:
                say("   [!!] группа %s занята дважды" % m["group"]); bad += 1
            seen_group[m["group"]] = m["mod"]
        if m["idspace"]:
            if m["idspace"] in seen_ids:
                say("   [!!] id-space %d занят дважды" % m["idspace"]); bad += 1
            seen_ids[m["idspace"]] = m["mod"]

        if not os.path.exists(os.path.join(SRC, m["src"])):
            say("   [!!] нет исходника %s" % m["src"]); bad += 1

        for k in keys_of(m):
            # Корневой пункт меню объявляют ВСЕ моды намеренно: иначе одиночная
            # установка дала бы папку без названия. Текст одинаковый, так что
            # чья запись победит при слиянии — неважно.
            if k in seen_keys and k != MENU_ROOT:
                say("   [!!] ключ %s объявлен дважды" % k); bad += 1
            seen_keys[k] = m["mod"]
            if k not in TR:
                say("   [!!] нет перевода для ключа %s" % k); bad += 1
                continue
            for loc in LOCALES:
                t = TR[k].get(loc)
                if not t:
                    say("   [!!] %s: нет локали %s" % (k, loc)); bad += 1
                elif "|" in t:
                    say("   [!!] %s/%s: вертикальная черта в тексте" % (k, loc)); bad += 1

    say("   модов: %d, групп: %d, id-space: %d, ключей: %d, локалей: %d"
        % (len(MODS), len(seen_group), len(seen_ids), len(seen_keys), len(LOCALES)))
    return bad


# ---------------------------------------------------------------------------
# 2. Сборка
# ---------------------------------------------------------------------------

def write_ws(dest, text):
    """.ws — UTF-16 LE с BOM, переводы строк CRLF."""
    data = text.replace("\r\n", "\n").replace("\n", "\r\n")
    with open(dest, "wb") as f:
        f.write(b"\xff\xfe" + data.encode("utf-16-le"))
    return os.path.getsize(dest)


def make_xml(m):
    g = m["group"]
    L = ['<?xml version="1.0" encoding="UTF-16"?>', "<UserConfig>"]
    L.append('\t<Group id="%s" displayName="%s%s">' % (g, MENU_PATH, m["menu_key"]))
    L.append("\t\t<PresetsArray>")
    L.append('\t\t\t<Preset id="0" displayName="default">')
    for vid, _key, _dt, default in m["vars"]:
        L.append('\t\t\t\t<Entry varId="%s" value="%s" />' % (vid, default))
    L.append("\t\t\t</Preset>")
    L.append("\t\t</PresetsArray>")
    L.append("\t\t<VisibleVars>")
    for vid, key, dt, _default in m["vars"]:
        L.append('\t\t\t<Var overrideGroup="%s" id="%s" displayName="%s" displayType="%s"/>'
                 % (g, vid, key, dt))
    L.append("\t\t</VisibleVars>")
    L.append("\t</Group>")
    L.append("</UserConfig>")
    return "\r\n".join(L) + "\r\n"


def make_strings(m, content_dir):
    """Собирает <локаль>.w3strings в content-папку мода."""
    keys = keys_of(m)
    if not keys:
        return 0, []

    base = int("211%04d000" % m["idspace"])
    os.makedirs(WORK, exist_ok=True)
    ok, failed = 0, []

    # Кодировщик не знает код cn, хотя игра такую локаль грузит. Язык определяет
    # ИМЯ файла, метка внутри нужна только кодировщику — подставляем ближайший.
    META_LANG = {"cn": "zh"}

    for loc in LOCALES:
        rows = [";meta[language=%s]" % META_LANG.get(loc, loc),
                "; id      |key(hex)|key(str)| text"]
        for i, k in enumerate(keys):
            rows.append("%d|        |%s|%s" % (base + i, k, TR[k][loc]))

        csv = os.path.join(WORK, "%s_%s.csv" % (m["group"], loc))
        with open(csv, "wb") as f:
            f.write(("\r\n".join(rows) + "\r\n").encode("utf-8"))   # UTF-8 без BOM

        r = subprocess.run([EXE, "--encode", csv, "--id-space", str(m["idspace"])],
                           capture_output=True, cwd=WORK)
        produced = csv + ".w3strings"
        if not os.path.exists(produced):
            out = ((r.stdout or b"") + (r.stderr or b"")).decode("utf-8", "replace")
            failed.append((loc, out.strip().splitlines()[-1:] or ["?"]))
            continue

        shutil.copyfile(produced, os.path.join(content_dir, "%s.w3strings" % loc))
        ok += 1

    return ok, failed


def build_one(m):
    root = os.path.join(DIST, m["mod"])
    if os.path.exists(root):
        shutil.rmtree(root)

    # Дерево внутри архива повторяет дерево игры: mods\ и bin\ рядом. Менеджеры
    # модов опознают папку mods и кладут скрипты куда надо; при ручной установке
    # обе папки просто перетаскиваются в папку игры и сливаются с существующими.
    # Без сегмента mods менеджер разложит мод в корень игры, где игра его не
    # ищет, — и это провал БЕЗ единого сообщения об ошибке.
    content = os.path.join(root, "mods", m["mod"], "content")
    local   = os.path.join(content, "scripts", "local")
    os.makedirs(local)

    text = io.open(os.path.join(SRC, m["src"]), encoding="utf-8").read()
    n = write_ws(os.path.join(local, m["src"]), text)
    say("   %-22s %-22s %6d Б  UTF-16 LE + BOM" % (m["mod"], m["src"], n))

    if m["menu_key"]:
        pc = os.path.join(root, "bin", "config", "r4game", "user_config_matrix", "pc")
        os.makedirs(pc)
        xml = os.path.join(pc, "%s.xml" % m["group"])
        with open(xml, "wb") as f:
            f.write(make_xml(m).encode("utf-8"))          # UTF-8 БЕЗ BOM
        say("   %-22s %-22s %6d Б  UTF-8 без BOM, %d настроек"
            % ("", m["group"] + ".xml", os.path.getsize(xml), len(m["vars"])))

        ok, failed = make_strings(m, content)
        say("   %-22s %-22s локалей собрано %d из %d" % ("", "w3strings", ok, len(LOCALES)))
        for loc, msg in failed:
            say("   %-22s   [!!] %s: %s" % ("", loc, " ".join(msg)))
    else:
        say("   %-22s %-22s без меню и без строк" % ("", "-"))

    return root


# ---------------------------------------------------------------------------
# 3-4. Установка
# ---------------------------------------------------------------------------

def read_utf16(p):
    raw = open(p, "rb").read()
    if raw[:2] != b"\xff\xfe":
        return None
    return raw.decode("utf-16")


def filelist_sync():
    """Приводит оба списка к нужному набору XML. Файлы — UTF-16 LE с BOM."""
    want = [m["group"] + ".xml" for m in MODS if m["menu_key"]]
    for fl in ("dx12filelist.txt", "dx11filelist.txt"):
        p = os.path.join(CFG, fl)
        if not os.path.exists(p):
            say("   [!!] нет файла %s" % fl); continue
        txt = read_utf16(p)
        if txt is None:
            say("   [!!] %s не UTF-16 LE — не трогаю" % fl); continue

        if not os.path.exists(p + ".bak_split"):
            shutil.copyfile(p, p + ".bak_split")

        lines = [l.strip() for l in txt.splitlines() if l.strip()]
        before = len(lines)
        lines = [l for l in lines if not any(x in l for x in LEGACY_XML)]
        dropped = before - len(lines)
        added = 0
        for w in want:
            if not any(w in l for l in lines):
                lines.append(w + ";")
                added += 1
        open(p, "wb").write(("\r\n".join(lines) + "\r\n").encode("utf-16"))
        say("   [ok] %s: снято старых %d, добавлено %d, всего строк %d"
            % (fl, dropped, added, len(lines)))


def mods_settings_sync():
    p = os.path.join(DOCS, "mods.settings")
    if not os.path.exists(p):
        say("   [--] mods.settings не найден — пропуск"); return
    txt = open(p, "rb").read().decode("utf-8", "replace")
    if not os.path.exists(p + ".bak_split"):
        shutil.copyfile(p, p + ".bak_split")

    gone = 0
    for legacy in LEGACY_MODS:
        new = re.sub(r"\[%s\][^\[]*" % re.escape(legacy), "", txt)
        if new != txt:
            gone += 1
        txt = new

    add = 0
    for m in MODS:
        if "[%s]" % m["mod"] in txt:
            continue
        txt = txt.rstrip("\r\n") + "\r\n[%s]\r\nEnabled=1\r\nPriority=%d\r\n" % (m["mod"], m["priority"])
        add += 1
    open(p, "wb").write(txt.encode("utf-8"))
    say("   [ok] mods.settings: снято старых %d, добавлено %d" % (gone, add))


def parse_ini(txt):
    out, cur = {}, None
    for line in txt.splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            cur = s[1:-1]; out.setdefault(cur, {})
        elif cur and "=" in s:
            k, v = s.split("=", 1)
            out[cur][k.strip()] = v.strip()
    return out


def user_settings_sync():
    # DX12 пишет в dx12user.settings, DX11 — в user.settings. Файла
    # dx11user.settings не существует: писали в пустоту, DX11 не мигрировался.
    for fn in ("dx12user.settings", "user.settings"):
        p = os.path.join(DOCS, fn)
        if not os.path.exists(p):
            continue
        raw = open(p, "rb").read().decode("utf-8", "replace")
        if not os.path.exists(p + ".bak_split"):
            shutil.copyfile(p, p + ".bak_split")

        ini = parse_ini(raw)
        old = ini.get("AardShatter", {})

        # Значения по умолчанию, поверх них — перенесённые из старого бандла,
        # и в самом верху — то, что уже стоит в новой группе. Последнее важно:
        # без него повторный запуск сбросил бы всё, что игрок настроил после
        # первой установки.
        blocks, moved, kept = [], 0, 0
        for m in MODS:
            if not m["vars"]:
                continue
            vals = {}
            for vid, _k, _dt, default in m["vars"]:
                vals[vid] = default
            # 1) значения из бандла [AardShatter]
            for ok_name, ov in old.items():
                tgt = MIGRATE.get(ok_name)
                if tgt and tgt[0] == m["oldgroup"] and tgt[1] in vals:
                    vals[tgt[1]] = ov
                    moved += 1
            # 2) значения из прежней, непрефиксованной версии этого же мода
            if m["oldgroup"]:
                for cur_name, cv in ini.get(m["oldgroup"], {}).items():
                    if cur_name in vals:
                        vals[cur_name] = cv
                        moved += 1
            # 3) и в самом верху — то, что уже стоит в нынешней группе
            for cur_name, cv in ini.get(m["group"], {}).items():
                if cur_name in vals:
                    vals[cur_name] = cv
                    kept += 1
            body = "".join("%s=%s\r\n" % (v[0], vals[v[0]]) for v in m["vars"])
            blocks.append("[%s]\r\n" % m["group"] + body)

        # снимаем все прежние секции и все нынешние, затем дописываем заново
        raw = re.sub(r"\[AardShatter\][^\[]*", "", raw)
        for m in MODS:
            for g in (m["oldgroup"], m["group"]):
                if g:
                    raw = re.sub(r"\[%s\][^\[]*" % re.escape(g), "", raw)

        raw = raw.rstrip("\r\n") + "\r\n" + "".join(blocks)
        open(p, "wb").write(raw.encode("utf-8"))
        say("   [ok] %s: групп записано %d, перенесено %d, сохранено своих %d"
            % (fn, len(blocks), moved, kept))


def install(roots):
    # всё прежнее — в backup, не удаляем
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    for legacy in LEGACY_MODS:
        old = os.path.join(MODS_DIR, legacy)
        if not os.path.exists(old):
            continue
        os.makedirs(BAK, exist_ok=True)
        shutil.move(old, os.path.join(BAK, "%s_%s" % (legacy, stamp)))
        say("   [ok] снят прежний %s -> backup" % legacy)

    for legacy in LEGACY_XML:
        oldxml = os.path.join(CFG, legacy)
        if os.path.exists(oldxml):
            os.remove(oldxml)
            say("   [ok] удалён прежний %s" % legacy)

    for m, root in zip(MODS, roots):
        src_mod = os.path.join(root, "mods", m["mod"])
        dst_mod = os.path.join(MODS_DIR, m["mod"])
        if os.path.exists(dst_mod):
            shutil.rmtree(dst_mod)
        shutil.copytree(src_mod, dst_mod)

        src_pc = os.path.join(root, "bin", "config", "r4game", "user_config_matrix", "pc")
        if os.path.exists(src_pc):
            for fn in os.listdir(src_pc):
                shutil.copyfile(os.path.join(src_pc, fn), os.path.join(CFG, fn))
        say("   [ok] установлен %s" % m["mod"])


# ---------------------------------------------------------------------------

STAGE_ONLY = "--stage-only" in sys.argv

head("СБОРКА ПЯТИ МОДОВ" + (" (только dist, игру не трогаем)" if STAGE_ONLY else ""))

if game_running() and not STAGE_ONLY:
    say("  Игра запущена. Закрой её — иначе настройки затрутся на выходе.")
    say("  Собрать в dist, не трогая игру:  python build.py --stage-only")
    sys.exit(3)

if not os.path.exists(EXE):
    say("  Не найден кодировщик строк: %s" % EXE); sys.exit(1)

head("1. Сверка описаний")
if validate():
    say(); say("  Есть ошибки — установка не выполнялась."); sys.exit(2)
say("   [ok] расхождений нет")

head("2. Сборка в dist")
if os.path.exists(DIST):
    shutil.rmtree(DIST)          # чтобы не оставались папки под прежними именами
os.makedirs(DIST, exist_ok=True)
roots = [build_one(m) for m in MODS]

if STAGE_ONLY:
    head("ГОТОВО (только сборка)")
    say("   dist собран. Установка в игру НЕ выполнялась.")
    say("   Закрой игру и запусти без ключа, чтобы поставить.")
    sys.exit(0)

head("3. Установка в игру")
install(roots)

head("4. Регистрация")
filelist_sync()
mods_settings_sync()
user_settings_sync()

head("ГОТОВО")
for m in MODS:
    say("   %-22s %s" % (m["mod"], m["title"]))
say()
say("   Настройки: Настройки -> Моды -> W3EE -> Дополнения")
say("   Старый бандл лежит в backup\\ — вернуть можно копированием обратно.")
