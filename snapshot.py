# -*- coding: utf-8 -*-
"""
Точка возврата для сборки Ведьмака: снимок ДО миграции и откат к нему.

  py -3 snapshot.py --make      снять слепок текущего состояния
  py -3 snapshot.py --restore   вернуть всё как было
  py -3 snapshot.py --verify    сверить снимок с текущим состоянием

Что попадает в снимок:
  скрипты modW3EE и mod0000_MergedFiles (включая бэкапы .orig_w3ee_tweaks),
  журнал слияний, ВСЕ конфиги меню модов, все файлы настроек из Документов,
  описание правок patches.json.

Сохранения НЕ трогаются ни снимком, ни миграцией — они лежат отдельно.
"""
import os, sys, shutil, json, hashlib

GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
DOCS = os.path.join(os.environ["USERPROFILE"], "Documents", "The Witcher 3")
SNAP = r"D:\W3EE-точка-возврата"
TWEAKS = os.path.dirname(os.path.abspath(__file__))

# (что копируем, тип, имя внутри снимка)
ITEMS = [
    (os.path.join(GAME, r"mods\modW3EE\content\scripts"),            "dir",  "modW3EE-scripts"),
    (os.path.join(GAME, r"mods\mod0000_MergedFiles\content\scripts"), "dir",  "merged-scripts"),
    (os.path.join(GAME, r"bin\config\r4game\user_config_matrix\pc"),  "dir",  "menu-config"),
    (os.path.join(GAME, r"mods\MergeInventory.xml"),                  "file", "MergeInventory.xml"),
    (os.path.join(DOCS, "input.settings"),                            "file", "input.settings"),
    (os.path.join(DOCS, "user.settings"),                             "file", "user.settings"),
    (os.path.join(DOCS, "dx12user.settings"),                         "file", "dx12user.settings"),
    (os.path.join(DOCS, "mods.settings"),                             "file", "mods.settings"),
    (os.path.join(DOCS, "profile.settings"),                          "file", "profile.settings"),
    (os.path.join(TWEAKS, "patches.json"),                            "file", "patches.json"),
]


def say(s=""):
    print(s, flush=True)


def head(s):
    say(); say("=" * 68); say("  " + s); say("=" * 68)


def game_running():
    import subprocess
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq witcher3.exe"],
                             capture_output=True, text=True, timeout=25).stdout
        return "witcher3.exe" in out.lower()
    except Exception:
        return False


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_manifest(root):
    """путь относительно root -> (размер, sha256)"""
    out = {}
    for base, _dirs, files in os.walk(root):
        for fn in files:
            p = os.path.join(base, fn)
            rel = os.path.relpath(p, root).replace("\\", "/")
            out[rel] = [os.path.getsize(p), sha(p)]
    return out


def make():
    if game_running():
        say("  ИГРА ЗАПУЩЕНА. Закройте её — иначе снимок поймает файлы на лету."); return 3
    if os.path.exists(SNAP):
        say("  Снимок уже существует: %s" % SNAP)
        say("  Удалите его вручную, если хотите снять заново. Перезаписывать не буду —")
        say("  это единственная дорога назад.")
        return 1

    head("СНИМАЮ ТОЧКУ ВОЗВРАТА")
    os.makedirs(SNAP)
    manifest = {}
    for src, kind, name in ITEMS:
        dst = os.path.join(SNAP, name)
        if not os.path.exists(src):
            say("   [--] нет: %s" % src); continue
        if kind == "dir":
            shutil.copytree(src, dst)
            manifest[name] = {"kind": "dir", "src": src, "files": walk_manifest(src)}
            say("   [ok] %-22s %d файлов" % (name, len(manifest[name]["files"])))
        else:
            shutil.copy2(src, dst)
            manifest[name] = {"kind": "file", "src": src,
                              "files": {name: [os.path.getsize(src), sha(src)]}}
            say("   [ok] %-22s %d Б" % (name, os.path.getsize(src)))

    with open(os.path.join(SNAP, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    total = sum(len(v["files"]) for v in manifest.values())
    size = sum(sz for v in manifest.values() for sz, _ in v["files"].values())
    head("СНИМОК ГОТОВ")
    say("   %s" % SNAP)
    say("   всего файлов: %d, объём: %.1f МБ" % (total, size / 1048576.0))
    say()
    say("   Вернуться назад:  «Вернуться к точке возврата.bat»")
    return 0


def load_manifest():
    p = os.path.join(SNAP, "_manifest.json")
    if not os.path.exists(p):
        say("  Снимка нет: %s" % SNAP); return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def verify():
    m = load_manifest()
    if m is None:
        return 1
    head("СВЕРКА СНИМКА С ТЕКУЩИМ СОСТОЯНИЕМ")
    diff = 0
    for name, info in m.items():
        src = info["src"]
        changed, missing, extra = 0, 0, 0
        if info["kind"] == "dir":
            now = walk_manifest(src) if os.path.exists(src) else {}
            for rel, (sz, h) in info["files"].items():
                if rel not in now:
                    missing += 1
                elif now[rel][1] != h:
                    changed += 1
            extra = len(set(now) - set(info["files"]))
        else:
            if not os.path.exists(src):
                missing = 1
            elif sha(src) != list(info["files"].values())[0][1]:
                changed = 1
        mark = "==" if (changed + missing + extra) == 0 else "!="
        say("   [%s] %-22s изменено:%-4d пропало:%-3d добавилось:%-3d"
            % (mark, name, changed, missing, extra))
        diff += changed + missing + extra
    say()
    say("   Отличий от снимка: %d" % diff)
    return 0


def restore():
    if game_running():
        say("  ИГРА ЗАПУЩЕНА. Закройте её и запустите откат снова."); return 3
    m = load_manifest()
    if m is None:
        return 1
    head("ВОЗВРАТ К ТОЧКЕ")
    for name, info in m.items():
        src = info["src"]
        snap = os.path.join(SNAP, name)
        if not os.path.exists(snap):
            say("   [--] в снимке нет: %s" % name); continue
        if info["kind"] == "dir":
            if os.path.exists(src):
                shutil.rmtree(src)
            shutil.copytree(snap, src)
            say("   [ok] %-22s возвращена папка (%d файлов)" % (name, len(info["files"])))
        else:
            os.makedirs(os.path.dirname(src), exist_ok=True)
            shutil.copy2(snap, src)
            say("   [ok] %-22s возвращён файл" % name)
    head("ГОТОВО")
    say("   Состояние откачено к моменту снимка.")
    say("   Сохранения не затрагивались ни разу.")
    return 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--make"
    if arg == "--make":
        sys.exit(make())
    if arg == "--restore":
        sys.exit(restore())
    if arg == "--verify":
        sys.exit(verify())
    say("Неизвестный режим. Возможные: --make | --restore | --verify")
    sys.exit(2)
