# -*- coding: utf-8 -*-
"""
Применяльщик правок W3EE (Игни / крит от знаков / ледяное расчленение / тиры сетов).

Читает patches.json рядом с собой и накладывает правки на файлы мода.

Использование:
    py -3 apply.py --steps 1,2,3,4,5            применить шаги
    py -3 apply.py --steps 1,2,3,4,5 --dry-run  только проверить, ничего не писать
    py -3 apply.py --revert                     вернуть всё из бэкапа

Гарантии:
  * игра должна быть закрыта (проверяется процесс witcher3.exe);
  * .ws читаются/пишутся в UTF-16 с сохранением исходного BOM;
  * .xml пишется в UTF-8 без BOM;
  * переводы строк файла не меняются;
  * блок 'before' должен встречаться РОВНО ОДИН раз, иначе правка пропускается;
  * если 'after' уже в файле - правка считается применённой и пропускается;
  * до первой записи каждый затрагиваемый файл копируется в <имя>.orig_w3ee_tweaks
    (существующая копия НЕ перезаписывается - она хранит первозданный вариант).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

BACKUP_SUFFIX = ".orig_w3ee_tweaks"
HERE = os.path.dirname(os.path.abspath(__file__))
PATCHES_PATH = os.path.join(HERE, "patches.json")
GAME_EXE = "witcher3.exe"

STATUS_APPLIED = "applied"
STATUS_SKIPPED = "skipped"
STATUS_ERROR = "error"


# --------------------------------------------------------------------------- вывод

def setup_console():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def say(text=""):
    print(text)


# --------------------------------------------------------------------------- ввод-вывод файлов

def read_file(path, encoding):
    """Возвращает (текст, байты BOM, имя кодека). BOM отделён, чтобы вернуть его байт в байт."""
    with open(path, "rb") as handle:
        raw = handle.read()

    if encoding == "utf16":
        if raw[:2] == b"\xff\xfe":
            bom, codec = b"\xff\xfe", "utf-16-le"
        elif raw[:2] == b"\xfe\xff":
            bom, codec = b"\xfe\xff", "utf-16-be"
        else:
            bom, codec = b"", "utf-16-le"
    elif encoding == "utf8-nobom":
        bom = b"\xef\xbb\xbf" if raw[:3] == b"\xef\xbb\xbf" else b""
        codec = "utf-8"
    else:
        raise ValueError("неизвестная кодировка в patches.json: %r" % encoding)

    return raw[len(bom):].decode(codec), bom, codec


def write_file(path, text, bom, codec):
    """Пишет через временный файл и атомарную замену, чтобы не оставить обрубок."""
    data = bom + text.encode(codec)
    tmp = path + ".w3ee_tweaks_tmp"
    with open(tmp, "wb") as handle:
        handle.write(data)
    os.replace(tmp, path)


def newline_of(text):
    return "\r\n" if "\r\n" in text else "\n"


# --------------------------------------------------------------------------- проверка игры

def game_is_running():
    """True / False / None (не удалось выяснить)."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq " + GAME_EXE, "/NH"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=60,
        )
    except Exception:
        return None
    return GAME_EXE in result.stdout.decode("utf-8", "replace").lower()


def refuse_if_game_running(dry_run):
    """True = писать нельзя. При --dry-run запущенная игра не мешает: мы только читаем."""
    state = game_is_running()
    if state is True:
        if dry_run:
            say("ВНИМАНИЕ: игра сейчас запущена (процесс %s)." % GAME_EXE)
            say("          Для пробного прогона это не помеха - мы только читаем файлы.")
            say("          Но перед реальным применением игру надо закрыть.")
            say()
            return False
        say("ОТКАЗ: игра запущена (процесс %s)." % GAME_EXE)
        say("       Закройте The Witcher 3 полностью и запустите ещё раз.")
        say("       Правка запущенной игры бесполезна - скрипты уже загружены в память,")
        say("       а при выходе игра может перезаписать конфиг своими значениями.")
        return True
    if state is None:
        say("ВНИМАНИЕ: не удалось проверить, запущена ли игра (tasklist недоступен).")
        say("          Убедитесь сами, что The Witcher 3 закрыт.")
        say()
    return False


# --------------------------------------------------------------------------- загрузка правок

def load_patches():
    if not os.path.isfile(PATCHES_PATH):
        say("ОШИБКА: не найден файл правок %s" % PATCHES_PATH)
        return None
    with open(PATCHES_PATH, "r", encoding="utf-8") as handle:
        patches = json.load(handle)
    if not isinstance(patches, list) or not patches:
        say("ОШИБКА: %s пуст или имеет неверный формат" % PATCHES_PATH)
        return None
    return patches


def parse_steps(raw):
    if not raw:
        return None
    steps = set()
    for chunk in raw.replace(";", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if not chunk.isdigit():
            say("ОШИБКА: --steps ждёт числа через запятую, а получил %r" % chunk)
            return False
        steps.add(int(chunk))
    return steps


# --------------------------------------------------------------------------- бэкап и откат

def make_backup(path):
    """Возвращает (успех, сообщение). Существующую копию НЕ трогает."""
    backup = path + BACKUP_SUFFIX
    if os.path.exists(backup):
        return True, "бэкап уже был, сохранён первозданный"
    try:
        shutil.copy2(path, backup)
    except Exception as error:
        return False, "не удалось создать бэкап: %s" % error
    return True, "бэкап создан"


def do_revert(patches):
    say("=== ОТКАТ: возврат файлов из бэкапа ===")
    say()
    files = []
    for patch in patches:
        if patch["file"] not in files:
            files.append(patch["file"])

    restored = missing = failed = 0
    for path in files:
        backup = path + BACKUP_SUFFIX
        name = os.path.basename(path)
        if not os.path.exists(backup):
            say("  [бэкапа нет] %s" % name)
            say("               %s" % path)
            missing += 1
            continue
        try:
            shutil.copy2(backup, path)
        except Exception as error:
            say("  [ОШИБКА    ] %s -- %s" % (name, error))
            failed += 1
            continue
        say("  [возвращено] %s" % name)
        restored += 1

    say()
    say("Возвращено: %d   Бэкапа не было: %d   Ошибок: %d" % (restored, missing, failed))
    say()
    say("Файлы .orig_w3ee_tweaks НЕ удалены - можно накатить правки заново")
    say("и снова откатиться. Удалите их вручную, когда всё устоится.")
    if missing and not restored:
        say()
        say("Ни одного бэкапа не найдено. Похоже, правки ни разу не применялись.")
    return 1 if failed else 0


# --------------------------------------------------------------------------- применение

def apply_patches(patches, steps, dry_run, ids=None):
    ids = set(ids or [])
    if steps is None and not ids:
        selected = list(patches)
    else:
        # объединение: шаги ПЛЮС отдельные правки по номеру
        selected = [p for p in patches
                    if (steps is not None and p["step"] in steps) or p["id"] in ids]
        unknown = sorted(ids - {p["id"] for p in patches})
        if unknown:
            say("ВНИМАНИЕ: в patches.json нет правок с номерами: %s"
                % ", ".join(unknown))
            say()
    if not selected:
        say("Под выбранные шаги не подошла ни одна правка. Нечего делать.")
        return 0

    shown_steps = sorted({p["step"] for p in selected})
    say("=== %s: шаги %s, правок %d ===" % (
        "ПРОБНЫЙ ПРОГОН (ничего не пишется)" if dry_run else "ПРИМЕНЕНИЕ ПРАВОК",
        ",".join(str(s) for s in shown_steps), len(selected)))
    say()

    loaded = {}      # путь -> [текст, bom, codec, изменялся ли]
    results = []     # (статус, id, шаг, имя файла, заголовок, пояснение)

    for patch in selected:
        path = patch["file"]
        name = os.path.basename(path)

        if path not in loaded:
            if not os.path.isfile(path):
                loaded[path] = None
            else:
                try:
                    text, bom, codec = read_file(path, patch["encoding"])
                    loaded[path] = [text, bom, codec, False]
                except Exception as error:
                    loaded[path] = None
                    say("ОШИБКА чтения %s: %s" % (path, error))

        entry = loaded[path]
        if entry is None:
            results.append((STATUS_ERROR, patch["id"], patch["step"], name, patch["title"],
                            "файл не найден или не читается: %s" % path))
            continue

        text = entry[0]
        newline = newline_of(text)
        before = patch["before"].replace("\n", newline)
        after = patch["after"].replace("\n", newline)

        if after in text:
            results.append((STATUS_SKIPPED, patch["id"], patch["step"], name, patch["title"],
                            "уже применено"))
            continue

        found = text.count(before)
        if found == 0:
            results.append((STATUS_ERROR, patch["id"], patch["step"], name, patch["title"],
                            "блок 'before' НЕ НАЙДЕН -- скорее всего автор мода изменил этот "
                            "код (обновление W3EE?) либо файл уже правили вручную"))
            continue
        if found > 1:
            results.append((STATUS_ERROR, patch["id"], patch["step"], name, patch["title"],
                            "блок 'before' найден %d раз -- правка неоднозначна, применять "
                            "нельзя" % found))
            continue

        entry[0] = text.replace(before, after, 1)
        entry[3] = True
        results.append((STATUS_APPLIED, patch["id"], patch["step"], name, patch["title"], ""))

    # --- запись ---
    write_errors = []
    if not dry_run:
        dirty = [p for p, e in loaded.items() if e and e[3]]
        if dirty:
            say("--- Бэкап (до любой записи) ---")
            for path in sorted(dirty):
                ok, note = make_backup(path)
                say("  %s %s -- %s" % ("[ok]   " if ok else "[ОШИБКА]",
                                       os.path.basename(path), note))
                if not ok:
                    write_errors.append((path, note))
            say()

            blocked = {path for path, _ in write_errors}
            say("--- Запись ---")
            for path in sorted(dirty):
                if path in blocked:
                    say("  [пропущен] %s -- нет бэкапа, писать не буду"
                        % os.path.basename(path))
                    continue
                text, bom, codec, _ = loaded[path]
                try:
                    write_file(path, text, bom, codec)
                    say("  [записан]  %s" % os.path.basename(path))
                except Exception as error:
                    say("  [ОШИБКА]   %s -- %s" % (os.path.basename(path), error))
                    write_errors.append((path, str(error)))
            say()

            # правки в файлах, которые не удалось записать, применёнными не считаются
            failed_paths = {path for path, _ in write_errors}
            if failed_paths:
                patch_by_id = {p["id"]: p for p in selected}
                fixed = []
                for row in results:
                    status, pid, step, name, title, note = row
                    if status == STATUS_APPLIED and patch_by_id[pid]["file"] in failed_paths:
                        fixed.append((STATUS_ERROR, pid, step, name, title,
                                      "правка посчитана, но файл записать не удалось"))
                    else:
                        fixed.append(row)
                results = fixed

    # --- отчёт ---
    label = {STATUS_APPLIED: "[применено]", STATUS_SKIPPED: "[пропущено]",
             STATUS_ERROR: "[ОШИБКА   ]"}
    if dry_run:
        label[STATUS_APPLIED] = "[ляжет    ]"

    say("--- Построчный отчёт ---")
    current_step = None
    for status, pid, step, name, title, note in results:
        if step != current_step:
            current_step = step
            say()
            say("  ШАГ %d" % step)
        line = "    %s %-5s %-28s %s" % (label[status], pid, name, title)
        say(line)
        if note:
            say("                        -> %s" % note)

    applied = sum(1 for r in results if r[0] == STATUS_APPLIED)
    skipped = sum(1 for r in results if r[0] == STATUS_SKIPPED)
    errors = sum(1 for r in results if r[0] == STATUS_ERROR)

    say()
    say("=" * 72)
    if dry_run:
        say("ИТОГ ПРОБНОГО ПРОГОНА: ляжет %d, пропущено (уже применено) %d, ошибок %d"
            % (applied, skipped, errors))
        say("Ничего не записано. Для реального применения уберите --dry-run.")
    else:
        say("ИТОГ: применено %d, пропущено (уже применено) %d, ошибок %d"
            % (applied, skipped, errors))
    say("=" * 72)

    if errors:
        say()
        say("Есть ошибки. Каждая помечена выше словом ОШИБКА с пояснением.")
        say("Чаще всего это значит, что мод W3EE обновился и код в нём изменился --")
        say("тогда такую правку надо накладывать вручную, см. ЧТО-ЭТО.md.")
    elif not dry_run and applied:
        say()
        say("Готово. Запустите игру. Дошла до главного меню -- скрипты скомпилировались.")
        say("Выпало окно с красным текстом об ошибке компиляции -- откатывайтесь:")
        say("  Откатить правки.bat")

    return 1 if errors else 0


# --------------------------------------------------------------------------- точка входа

def main():
    setup_console()

    parser = argparse.ArgumentParser(
        description="Применяет правки W3EE из patches.json.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--steps", default="",
                        help="какие шаги применять, через запятую, например 1,2,3. "
                             "По умолчанию все.")
    parser.add_argument("--ids", default="",
                        help="точечный выбор правок по номеру, через запятую, "
                             "например 1.3,1.4. Складывается с --steps.")
    parser.add_argument("--dry-run", action="store_true",
                        help="только проверить совпадение блоков, ничего не писать")
    parser.add_argument("--revert", action="store_true",
                        help="вернуть все файлы из бэкапов .orig_w3ee_tweaks")
    args = parser.parse_args()

    patches = load_patches()
    if patches is None:
        return 2

    if args.revert:
        if args.steps:
            say("ЗАМЕЧАНИЕ: при откате --steps не учитывается.")
            say("           Бэкап хранит первозданный файл целиком, поэтому возврат")
            say("           одного файла снимает все правки всех шагов в нём.")
            say()
        if refuse_if_game_running(dry_run=False):
            return 3
        return do_revert(patches)

    steps = parse_steps(args.steps)
    if steps is False:
        return 2

    if refuse_if_game_running(dry_run=args.dry_run):
        return 3

    ids = [x.strip() for x in args.ids.split(",") if x.strip()]
    return apply_patches(patches, steps, args.dry_run, ids)


if __name__ == "__main__":
    sys.exit(main())
