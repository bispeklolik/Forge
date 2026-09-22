# -*- coding: utf-8 -*-
"""
Правит описание «Мутации инсектоида» (skill_desc_mutation_5) в modReduxW3EE,
чтобы текст соответствовал шагу 7 из patches.json (мутация работает только в бою).

    py -3 patch_mut5_text.py            применить
    py -3 patch_mut5_text.py --revert   вернуть из бэкапа

Безопасность: w3strings.exe --test-encoder на этих файлах даёт побайтово
идентичный результат, значит распаковка/запаковка ничего не теряет.
Перед первой записью рядом кладётся <имя>.orig_w3ee_tweaks.
"""
import io, os, shutil, subprocess, sys, tempfile

HERE   = os.path.dirname(os.path.abspath(__file__))
EXE    = os.path.join(HERE, "tools", "w3strings", "w3strings.exe")
GAME   = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
MODC   = os.path.join(GAME, "mods", "modReduxW3EE", "content")
SUFFIX = ".orig_w3ee_tweaks"
STRING_ID = "2118472675"

NEW = {
 "ru": '-В бою токсины не выводятся сами — их сжигает ярость.<br>+Скорость выведения идёт за полосой адреналина: пустая даёт $S$% от обычной, полная — $S$%.<br>+Вне боя токсины выводятся как обычно.',
 "en": 'In combat your body no longer purges toxins on its own - fury burns them instead.<br>Purge speed follows the Adrenaline bar: an empty bar gives $S$% of the normal rate, a full bar $S$%.<br>Out of combat toxins are purged normally.',
}


def game_running():
    try:
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL).decode("cp866", "replace")
    except Exception:
        return False
    return "witcher3.exe" in out.lower()


def run(*args):
    p = subprocess.run([EXE] + list(args), capture_output=True)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


def revert():
    n = 0
    for lang in NEW:
        path = os.path.join(MODC, lang + ".w3strings")
        bak = path + SUFFIX
        if os.path.exists(bak):
            shutil.copy2(bak, path)
            print("  [\u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0435\u043d\u043e] %s.w3strings" % lang)
            n += 1
        else:
            print("  [\u0431\u044d\u043a\u0430\u043f\u0430 \u043d\u0435\u0442] %s.w3strings" % lang)
    return 0 if n else 1


def patch_one(lang, tmp):
    path = os.path.join(MODC, lang + ".w3strings")
    if not os.path.exists(path):
        print("  [\u043d\u0435\u0442 \u0444\u0430\u0439\u043b\u0430] %s" % path)
        return False

    work = os.path.join(tmp, lang + ".w3strings")
    shutil.copy2(path, work)

    rc, out = run("--decode", work)
    csv = work + ".csv"
    if rc != 0 or not os.path.exists(csv):
        print("  [\u041e\u0428\u0418\u0411\u041a\u0410 decode] %s\n%s" % (lang, out))
        return False

    lines = io.open(csv, encoding="utf-8").read().split("\n")
    hit = 0
    for i, ln in enumerate(lines):
        if ln.startswith(STRING_ID + "|"):
            head = ln.split("|")[:3]
            if head[-1] or True:
                if ln.split("|", 3)[3] == NEW[lang]:
                    print("  [\u0443\u0436\u0435 \u0441\u0442\u043e\u0438\u0442] %s.w3strings" % lang)
                    return True
            lines[i] = "|".join(head) + "|" + NEW[lang]
            hit += 1
    if hit != 1:
        print("  [\u041e\u0428\u0418\u0411\u041a\u0410] %s: \u0441\u0442\u0440\u043e\u043a\u0430 %s \u043d\u0430\u0439\u0434\u0435\u043d\u0430 %d \u0440\u0430\u0437" % (lang, STRING_ID, hit))
        return False

    io.open(csv, "w", encoding="utf-8", newline="").write("\n".join(lines))
    rc, out = run("--encode", csv, "--force-ignore-id-space-check-i-know-what-i-am-doing")
    enc = csv + ".w3strings"
    if rc != 0 or not os.path.exists(enc):
        print("  [\u041e\u0428\u0418\u0411\u041a\u0410 encode] %s\n%s" % (lang, out))
        return False

    bak = path + SUFFIX
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    shutil.copy2(enc, path)
    print("  [\u0437\u0430\u043f\u0438\u0441\u0430\u043d\u043e] %s.w3strings" % lang)
    return True


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if not os.path.exists(EXE):
        print("\u043d\u0435\u0442 w3strings.exe: %s" % EXE)
        return 2
    if "--revert" in sys.argv:
        print("=== \u041e\u0422\u041a\u0410\u0422 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u044f \u043c\u0443\u0442\u0430\u0446\u0438\u0438 ===")
        return revert()
    if game_running():
        print("\u0418\u0433\u0440\u0430 \u0437\u0430\u043f\u0443\u0449\u0435\u043d\u0430 (witcher3.exe). \u0417\u0430\u043a\u0440\u043e\u0439\u0442\u0435 \u0435\u0451 \u0438 \u043f\u043e\u0432\u0442\u043e\u0440\u0438\u0442\u0435.")
        return 2
    print("=== \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u041c\u0443\u0442\u0430\u0446\u0438\u0438 \u0438\u043d\u0441\u0435\u043a\u0442\u043e\u0438\u0434\u0430 ===")
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for lang in ("ru", "en"):
            ok = patch_one(lang, tmp) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
