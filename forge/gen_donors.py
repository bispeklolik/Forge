# -*- coding: utf-8 -*-
"""Реестр доноров-мечей: ВСЕ носибельные steelsword/silversword.

Решение пользователя 21.08.2026 («почему с топоров и дубин не падают
жетоны?»): жертвуется ЛЮБОЙ носибельный клинок — мечи, топоры, булавы,
кирки, Netflix-сет, любое качество. Узкий реестр «только реликты 4-5»
похоронен. Исключения: NGP-копии (NG+ дубли тех же имён) и *_test-мусор.
"""
import io, json, os, sys

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from medallion import bundles as B
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"

cards = {}
for rel in ("mods\\modW3EE\\content", "content\\content0", "dlc\\dlcW3EE\\content",
            "dlc\\bob\\content", "dlc\\ep1\\content"):
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
                if not nm.endswith(".xml") or (
                        "gameplay/items" not in nm
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
                for it in r2.iter("item"):
                    n = it.get("name")
                    if not n or n in cards:
                        continue
                    # вспомогательное оружие (решение пользователя 01.09:
                    # «класс оружия привязан к заготовке — сделать заготовку
                    # вспомогательного и всё»): копья, топоры, булавы, посохи
                    if it.get("category") not in (
                            "steelsword", "silversword",
                            "secondary", "blunt1h", "staff2h", "spear2h",
                            "axe1h", "axe2h", "cleaver1h", "hammer2h",
                            "halberd2h"):
                        continue
                    cards[n] = {
                        "cat": it.get("category"),
                        "tpl": it.get("equip_template") or "",
                        "icon": it.get("icon_path") or "",
                    }

# хозяйственный хлам не входит в кузницу (жерди, вёсла, грабли, мётлы);
# сломанные дубли тоже. Caretaker Shovel — лопата Ключника из HoS, ОСТАЁТСЯ.
JUNK = {
    "Broom_Not_Work", "NPC Ghost pole", "NPC Laundry stick", "NPC Plank",
    "Long metal pole", "Paling", "Rake", "Scoop", "Oar", "Shepard Stick",
    "Shovel", "Caranthil Staff Broken", "Q1_brokenSpear",
    "Torch Blunt Burning",
}

donors = []
for n in sorted(cards):
    c = cards[n]
    if not c["tpl"] or not c["icon"]:
        continue                      # ненадеваемое / без иконки — не донор
    if n.startswith("NGP ") or n.endswith("_test") or n == "axe_test" or n == "mace_test":
        continue
    if n in JUNK:
        continue
    donors.append({"name": n, "cat": c["cat"], "icon": c["icon"]})

print("носибельных доноров:", len(donors), "из", len(cards), "карточек мечей")
tmp = os.path.join(HERE, "donors.json.tmp")
io.open(tmp, "w", encoding="utf-8").write(
    json.dumps(donors, ensure_ascii=False, indent=1))
os.replace(tmp, os.path.join(HERE, "donors.json"))
print("сохранено: forge/donors.json")
