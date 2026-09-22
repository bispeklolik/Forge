# -*- coding: utf-8 -*-
u"""ПРОВЕРКА: собирается ли донор ОДИН В ОДИН (требование ГД 17.09).

Складываем все строки, нарезанные с донора (cut_data.json), и сравниваем с
его настоящим профилем — суммой свойств ВСЕХ абилок его карточки.

Источник профиля тот же, что у нарезки (build_cut.py): сначала W3EE, потом
ваниль, первое определение побеждает. Сама проверка при этом независима —
она не повторяет нарезку, а смотрит на её результат.

Расхождения делятся на три вида:
  * ЗАДУМАНО  — плюс общего урона (attack_power) срезан «красным правилом»:
                он не чеканится у брони и вспомогательного оружия;
  * ОКРУГЛЕНИЕ — минус, поделённый между кусками, разошёлся меньше чем на 1%;
  * ОШИБКА    — всё остальное. Это и есть то, что игрок увидит как
                «собранная вещь не равна оригиналу».

Запуск:
    python verify_copy.py                  все доноры, сводка
    python verify_copy.py --detail         все доноры, каждое расхождение
    python verify_copy.py "Adversary Silver Sword" "Cheesecutter"
"""
import io, json, os, sys, collections
import xml.etree.ElementTree as ET

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from medallion import bundles as B

GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
HERE = os.path.dirname(os.path.abspath(__file__))

# то же, что build_cut.SKIP_ATTRS: урон и служебные поля едут не строками
SKIP = {"weight", "quality", "armor", "item_level_min", "item_level_max"}
# скелет брони (защита, резисты, повадки веса) едет жетоном ЗАЩИТЫ
ARMOR_SKEL = {"slashing_resistance_perc", "piercing_resistance_perc",
              "bludgeoning_resistance_perc", "elemental_resistance_perc",
              "armor_speed", "armor_regen_penalty", "armor_stamina_efficiency",
              "staminaRegen_armor_mod"}
ARMOR_CATS = ("armor", "pants", "gloves", "boots")
WEAR_CATS = ARMOR_CATS + ("steelsword", "silversword", "secondary", "blunt1h",
                          "staff2h", "spear2h", "axe1h", "axe2h", "cleaver1h",
                          "hammer2h", "halberd2h")
ROUND = 0.01     # минус, делённый между кусками, округляется до 4 знаков


def read_game():
    abil, cards = {}, {}
    for rel in ("mods\\modW3EE\\content", "content\\content0",
                "dlc\\dlcW3EE\\content", "dlc\\bob\\content", "dlc\\ep1\\content"):
        base = os.path.join(GAME, rel)
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if not d.startswith("~")]
            for f in files:
                if not f.endswith(".bundle"):
                    continue
                blob = os.path.join(root, f)
                try:
                    idx = B.read_index(blob)
                except Exception:
                    continue
                for e in idx:
                    nm = str(getattr(e, "name", e)).replace("\\", "/")
                    if not nm.endswith(".xml") or ("gameplay/items" not in nm
                                                  and "gameplay/abilities" not in nm):
                        continue
                    try:
                        raw = B.extract(blob, e)
                    except Exception:
                        continue
                    t = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") \
                        else raw.decode("utf-8", "replace")
                    try:
                        r2 = ET.fromstring(t)
                    except Exception:
                        continue
                    for ab in r2.iter("ability"):
                        abil.setdefault(ab.get("name"), ab)
                    for it in r2.iter("item"):
                        n = it.get("name")
                        if n and n not in cards and it.get("category") in WEAR_CATS:
                            cards[n] = {"cat": it.get("category"),
                                        "abil": [a.text.strip() for a in it.iter("a")
                                                 if a.text]}
    return abil, cards


def profile(donor, abil, cards):
    """Сумма свойств всех абилок карточки: (ось, тип) -> значение."""
    got = collections.defaultdict(float)
    card = cards.get(donor)
    if not card:
        return None
    for a in card["abil"]:
        node = abil.get(a)
        if node is None:
            continue
        for ch in node:
            if ch.tag == "tags" or ch.tag in SKIP or ch.tag.endswith("Damage"):
                continue
            if card["cat"] in ARMOR_CATS and ch.tag in ARMOR_SKEL:
                continue
            if ch.get("is_ability") == "true":
                got[(ch.tag, "effect")] = 1.0
                continue
            try:
                v = float(ch.get("min") or 0)
            except (TypeError, ValueError):
                continue
            if v:
                got[(ch.tag, ch.get("type", "base"))] += v
    return got


def main():
    cut = json.load(io.open(os.path.join(HERE, "cut_data.json"), encoding="utf-8"))
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    detail = "--detail" in sys.argv or bool(names)
    donors = names or sorted({c["donor"] for c in cut})

    print("читаю свойства из сборки...")
    abil, cards = read_game()
    print("абилок %d, карточек %d, доноров к проверке %d\n"
          % (len(abil), len(cards), len(donors)))

    tally = collections.Counter()
    bad_donors = []
    for donor in donors:
        orig = profile(donor, abil, cards)
        if orig is None:
            tally["нет карточки"] += 1
            continue
        mine = collections.defaultdict(float)
        for c in (c for c in cut if c["donor"] == donor):
            for a, ty, v in c["stats"]:
                if a in SKIP or a.endswith("Damage"):
                    continue
                if ty == "effect":
                    mine[(a, "effect")] = 1.0
                else:
                    mine[(a, ty)] += float(v)

        errors, planned = [], []
        for k in sorted(set(orig) | set(mine)):
            o, m = round(orig.get(k, 0.0), 4), round(mine.get(k, 0.0), 4)
            if abs(o - m) < ROUND:
                continue
            if k[0] == "attack_power" and o > 0 and m < o:
                planned.append((k, o, m))
            else:
                errors.append((k, o, m))
        if errors:
            tally["ОШИБКА"] += 1
            bad_donors.append((donor, errors))
        elif planned:
            tally["задумано (красное правило)"] += 1
        else:
            tally["один в один"] += 1

        if detail and (errors or planned):
            print("=== %s" % donor)
            for (a, ty), o, m in errors:
                print("   ОШИБКА   %-32s оригинал %8.4f | сборка %8.4f" % (a + " (" + ty + ")", o, m))
            for (a, ty), o, m in planned:
                print("   задумано %-32s оригинал %8.4f | сборка %8.4f" % (a + " (" + ty + ")", o, m))

    print("\nИТОГ по %d донорам:" % len(donors))
    for k, v in tally.most_common():
        print("   %-28s %d" % (k, v))
    if bad_donors and not detail:
        print("\nдоноры с ОШИБКАМИ (первые 25; полный список: --detail):")
        for d, errs in bad_donors[:25]:
            axes = ", ".join("%s %+.3f" % (k[0], m - o) for k, o, m in errs[:4])
            print("   %-36s %s" % (d, axes))
    return 1 if bad_donors else 0


if __name__ == "__main__":
    sys.exit(main())
