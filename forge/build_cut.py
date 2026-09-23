# -*- coding: utf-8 -*-
"""НАРЕЗКА ШКОЛ И РЕЛИКТОВ (v1.1) — карточные профили доноров режутся на
строки-пары «плюс + его родной минус».

Правила (зафиксированы в вольте, witcher3-redux-balance-grammar):
  - пара неразрывна: взял плюс — получил его минус;
  - связка эффекта (XxxEffect + buff_apply_chance + desc_*_mult) — ОДИН плюс;
  - базовый урон (SlashingDamage/SilverDamage/ElementalDamage/PoisonDamage),
    вес и качество в строки НЕ идут;
  - ⚠️ правило красной команды: плюс attack_power — максимум в ОДНОЙ строке
    на категорию во всём реестре (иначе стакание строк соберёт то, что пулы
    запрещают); лишние attack_power-плюсы в строки не попадают;
  - кап 3 строки с одного профиля; плюсы сверх минусов раздаются по строкам
    (не больше 2 плюсов на строку), безминусные хвосты идут отдельной строкой
    только если профиль вообще без минусов (чистые вещи так и устроены).

Выход: forge/cut_data.json — реестр нарезанных строк, который lines_data
подхватывает в единый реестр (id 27+).
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from medallion import bundles as B
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"

DONORS = json.load(io.open(os.path.join(HERE, "donors.json"), encoding="utf-8"))
try:
    ARMOR_DONORS = json.load(io.open(os.path.join(HERE, "donors_armor.json"),
                                     encoding="utf-8"))
except Exception:
    ARMOR_DONORS = []

# armor — базовый стат брони (аналог SlashingDamage): в строки не идёт,
# переносится жетоном защиты через абилку FRG_AD (см. armor_data.json).
# item_level — служебное, в строки не идёт и в баланс не считается.
SKIP_ATTRS = {"weight", "quality", "armor",
              "item_level_min", "item_level_max",
              "SlashingDamage", "SilverDamage",
              "ElementalDamage", "PoisonDamage", "BludgeoningDamage",
              "PiercingDamage", "RendingDamage", "FireDamage", "FrostDamage",
              "ShockDamage"}

# ⛔ ПУСТО С 17.09. Раньше сюда была записана прочность: её выбрасывали
# насильно, «мод затевался, чтобы её заменять», и заодно уценяли минусы
# на долю выброшенного. Итог — копию донора нельзя было собрать: ни
# плюса, ни честных штрафов (-28% вместо -50%).
# Требование ГД: базовая сборка копии обязана давать вещь ОДИН В ОДИН, а
# «поменять бесполезный плюс на полезный» — это выбор игрока (не взял эту
# строку, взял другую), а не наше решение за него.
# Механика уценки минусов ниже жива и включится сама, если сюда когда-
# нибудь снова что-то положат.
WASTE_PLUS = set()
EFFECT_GLUE = {"buff_apply_chance"}

# Плоские урон-статы карточки: то, чем реликты реально различаются по урону
# с руки (+854 серебра у Красного Волка 2, +428 режущего у туссентского,
# +100 «эфирного» у Объятий проклятого). Едут с ЖЕТОНОМ УРОНА.
# Правило общее: ЛЮБОЙ атрибут *Damage со значением >1 — плоская добавка.
def is_flat_dmg(attr, val):
    return (attr.endswith("Damage") and abs(val) > 1) or \
           (attr == "armor_reduction" and abs(val) > 1)

# Уникальные механики: строка с такой — «реликтовая» независимо от цифр.
UNIQUE_ATTRS = {"lifesteal", "instant_kill_chance",
                "human_exp_bonus_when_fatal", "nonhuman_exp_bonus_when_fatal"}


def line_is_relic(stats, quality=0):
    """РЕЛИКТОВАЯ строка — на клинок влезает максимум ОДНА (как рунное слово).

    Одобрено старшим ГД 21.08.2026 (дизайн-док v2, Р-2): капов на значения НЕТ,
    синтетических минусов НЕТ; противовес структурный — жирное и безминусное
    эксклюзивно.

    ⚠️ ПЕРЕСМОТР 23.08.2026 (старший ГД): «Реликтовыми можно считать ТОЛЬКО те,
    которые идут без минуса с жирным плюсом». Строка с минусом платит уже своим
    минусом — брать с неё вторую плату эксклюзивностью нечестно (двойной налог).
    Итог: реликт = НЕТ МИНУСА и (уникальная механика | эффект-связка | одиночный
    плюс >= 50% | сумма плюсов >= 20%). Бывшие реликты с минусом переезжают в
    обычные и больше не эксклюзивны — их можно ставить по несколько.
    Плоские значения (>1) — не проценты, в сумму не идут."""
    plus_sum, has_minus, uniq = 0.0, False, False
    for a, t, v in stats:
        if t == "effect" or a in EFFECT_GLUE or a.startswith("desc_"):
            uniq = True
            continue
        if v < 0:
            has_minus = True
            continue
        if a in UNIQUE_ATTRS:
            uniq = True
        if v <= 1.0:
            plus_sum += v
            if v >= 0.5:
                uniq = True
    # ⚠️ ПОЧИНКА 08.09: реликтовость — это ещё и ПРОИСХОЖДЕНИЕ. Формула
    # «чистый жирный плюс» отсекала настоящие реликты игры (Аэрондит,
    # Чёрный Единорог, Лазурная Ярость): их профиль с минусами, и при
    # нарезке минус достаётся каждой строке. Игрок разбирал реликты и
    # получал одни «обычные» свойства. Теперь: со СВОЕЙ вещи реликтового
    # качества (в Redux это quality 4) реликтовой считается СИЛЬНАЯ строка,
    # даже если она с минусом; слабую мелочь реликтом не объявляем.
    # ⚠️ 08.09, второй заход: РОВНО 4. Пятёрка в Redux — ведьмачье
    # снаряжение (Медведь/Волк/Грифон), а не реликт; с ней эксклюзивными
    # становились 78% всех строк, и кузница вставала колом.
    if quality == 4 and (uniq or plus_sum >= 0.15):
        return True
    return (not has_minus) and (uniq or plus_sum >= 0.2)


# ---- нерф верхушки (решение ГД 23.08) ----------------------------------------
STAT_CAP = 0.30      # потолок на ОДИН плюсовой стат
SUM_SOFT = 0.60      # порог мягкого сжатия суммы плюсов
SUM_DIV = 3.0        # во столько раз режется всё, что выше порога


def nerf_top(stats):
    """⚠️ НЕ ПРИМЕНЯЕТСЯ К НАРЕЗКЕ (решение ГД: «не надо нерфить разобранный
    бонус, надо понерфить сами мечи»). Формула переезжает в патч ВАНИЛЬНЫХ
    вещей — тогда и меч в руках, и жетон с него ослабнут заодно.

    Срезает ванильные выбросы: потолок на стат + мягкое сжатие суммы.

    Плоские значения (>1.5) — не проценты (урон, броня, стойкость), их не
    трогаем. Эффект-строки (is_ability) проходят как есть. Минусы не
    трогаем никогда: строка и так платит ими."""
    def is_pct(k, v):
        return k != "effect" and 0 < v <= 1.5

    capped = [(a, k, (min(v, STAT_CAP) if is_pct(k, v) else v))
              for a, k, v in stats]
    s = sum(v for a, k, v in capped if is_pct(k, v))
    if s <= SUM_SOFT:
        return capped
    ratio = (SUM_SOFT + (s - SUM_SOFT) / SUM_DIV) / s
    return [(a, k, (v * ratio if is_pct(k, v) else v)) for a, k, v in capped]


def is_effect_attr(tag):
    return tag.endswith("Effect")


def is_desc_attr(tag):
    return tag.startswith("desc_")


# ---- сбор абилок и карточек доноров ------------------------------------------
abil = {}
card_abils = {}
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
                nm = str(getattr(e, "name", e))
                # ⚠️ НЕ фильтровать по "def_": W3EE держит определения и в
                # dlc1_items.xml / kotw_armor.xml и т.п. — фильтр по пути
                _pth = nm.replace("\\", "/")
                if not nm.endswith(".xml") or (
                        "gameplay/items" not in _pth
                        and "gameplay/abilities" not in _pth):
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
                    if n and n not in card_abils and it.get("category") in (
                            "steelsword", "silversword", "armor", "pants",
                            "gloves", "boots",
                            # вспомогательное оружие (класс от заготовки)
                            "secondary", "blunt1h", "staff2h", "spear2h",
                            "axe1h", "axe2h", "cleaver1h", "hammer2h",
                            "halberd2h"):
                        _tags_node = it.find("tags")
                        card_abils[n] = {
                            "abil": [a.text.strip() for a in it.iter("a") if a.text],
                            "lockey": it.get("localisation_key_name") or "",
                            "tags": [s.strip() for s in
                                     (_tags_node.text or "").split(",")]
                                    if _tags_node is not None else [],
                        }

print("абилок:", len(abil), " карточек мечей:", len(card_abils))


def quality_of(donor):
    """Качество вещи по её абилкам (атрибут quality, type=add).
    ⚠️ В Redux РЕЛИКТ = 4 (пятёрка — «ведьмачье снаряжение»), это записано
    в вольте: своя добавленная единица превращала реликт донора (4) в 5.
    Реликтовость свойства — это ПРОИСХОЖДЕНИЕ, а не форма строки."""
    q = 0
    for a in card_abils.get(donor, {}).get("abil", []):
        node = abil.get(a)
        if node is None:
            continue
        for ch in node:
            if ch.tag == "quality":
                try:
                    q += int(float(ch.get("min") or 0))
                except (TypeError, ValueError):
                    pass
    return q


def profile_of(donor):
    """Все процентные статы профиля донора: [(attr, typ, val)], эффект-связки
    склеены в группы. Второй результат — «вес» выброшенных мусорных плюсов
    (доли 0..1), которым потом дисконтируются минусы."""
    rows = []
    waste = 0.0
    for a in card_abils.get(donor, {}).get("abil", []):
        node = abil.get(a)
        if node is None:
            continue
        for ch in node:
            if ch.tag == "tags" or ch.tag in SKIP_ATTRS \
                    or ch.tag.endswith("Damage"):
                continue
            try:
                v = float(ch.get("min") or 0)
            except (TypeError, ValueError):
                v = 0.0
            if ch.tag in WASTE_PLUS:
                if 0 < v <= 1.0:
                    waste += v
                continue
            typ = ch.get("type", "base")
            if is_effect_attr(ch.tag):
                rows.append((ch.tag, "effect", 1.0))
            elif v != 0:
                rows.append((ch.tag, typ, v))
    return rows, waste


MAX_PLUS_PER_LINE = 3      # плюсов в одной строке-жетоне
# ⛔ ДВА (решение ГД 23.09): «с меча максимум два жетона». Первое свойство
# идёт отдельной строкой, ВСЁ остальное — второй (ГД 24.09, интервью).
MAX_LINES_PER_DONOR = 2    # на сколько строк максимум рвём профиль


def cut_profile(rows, waste=0.0, whole=False):
    """Режет профиль на строки: [{plus: [...], minus: [...]}]. waste — доля
    выброшенных мусорных плюсов: минусы дисконтируются пропорционально.

    whole=True — НЕ резать вовсе, вернуть одну строку. Так берётся броня
    (требование ГД 18.09): у элемента брони все уникальные свойства
    снимаются ОДНИМ жетоном, без деления на куски и без разницы
    «реликтовое / нереликтовое». Резать на части имеет смысл только для
    оружия, где из кусков собирают свой клинок."""
    pluses, minuses = [], []
    glue = []          # эффект-связка собирается в один плюс
    for attr, typ, v in rows:
        if typ == "effect" or attr in EFFECT_GLUE or is_desc_attr(attr):
            glue.append((attr, typ, v))
            continue
        (pluses if v > 0 else minuses).append([(attr, typ, v)])
    if glue:
        pluses.insert(0, glue)

    if not pluses:
        return []

    # дисконт минусов: цена платилась и за выброшенный плюс — вычитаем его долю
    if waste > 0 and minuses:
        keep = sum(v for grp in pluses for _a, _t, v in grp if 0 < v <= 1.0)
        ratio = keep / (keep + waste) if keep > 0 else 0.0
        scaled = []
        for grp in minuses:
            g2 = [(a, t, round(v * ratio, 4)) for a, t, v in grp
                  if abs(v * ratio) >= 0.01]
            if g2:
                scaled.append(g2)
        minuses = scaled

    # ⛔ ЖИРНЫЕ ПРОФИЛИ РЕЖЕМ (решение ГД 25.08): число строк — по максимуму
    # из «сколько минусов» и «сколько нужно, чтобы плюсов в строке было не
    # больше MAX_PLUS_PER_LINE». Иначе профиль с одним минусом (двуручный
    # молот W3EE: 7 плюсов, минус один) слипался в одну всемогущую строку.
    lines = []
    if whole:
        # одна строка: все плюсы и все минусы вещи целиком
        return [{"plus": [s for grp in pluses for s in grp],
                 "minus": [s for grp in minuses for s in grp]}]
    n_min = max(len(minuses), 1) if minuses else 1
    n_fat = -(-len(pluses) // MAX_PLUS_PER_LINE)          # ceil
    n = max(n_min, n_fat)
    n = min(n, MAX_LINES_PER_DONOR, len(pluses))
    for i in range(n):
        lines.append({"plus": list(pluses[i]), "minus": []})
    # минусы делим ПРОПОРЦИОНАЛЬНО: цена профиля целиком не меняется,
    # но каждая отколотая строка платит свою долю
    if minuses:
        flat = [s for grp in minuses for s in grp]
        for a, ty, v in flat:
            share = round(v / n, 4)
            if abs(share) < 0.005:
                lines[0]["minus"].append((a, ty, round(v, 4)))
                continue
            for ln in lines:
                ln["minus"].append((a, ty, share))
    # «первое отдельно, остальные вместе» (ГД 24.09): хвост плюсов — в
    # ПОСЛЕДНЮЮ строку, а не вразнобой по всем
    for extra in pluses[n:]:
        lines[n - 1]["plus"].extend(extra)
    # не больше 2 плюс-групп визуально — мягкое правило, пропускаем жёсткую
    # проверку: связки уже сгруппированы
    return lines


# ---- нарезка всех доноров ----------------------------------------------------
# ⛔ СТАБИЛЬНОСТЬ id (переделано 24.09). Жетоны и абилки FRG_C_<id> живут на
# вещах игроков. Прежний ключ «(донор, номер строки)» при перерезке тихо
# отдавал старый id строке с ДРУГИМИ статами — клинок игрока менял цифры.
# Теперь ключ — СОДЕРЖИМОЕ: (донор, статы). Совпало точно — id прежний;
# иначе новый id выше «отметки прилива» (cut_hwm.json, только растёт).
# Прежняя строка без пары уходит в отставку (cut_retired.json, только
# растёт) и объявляется дальше с исходными статами. id не выдаётся дважды.
from lines_data import is_no_forge as _is_no_forge


def _statkey(stats):
    return tuple(sorted((a, t, round(float(v), 4)) for a, t, v in stats))


try:
    _old_cut = json.load(io.open(os.path.join(HERE, "cut_data.json"),
                                 encoding="utf-8"))
except Exception:
    _old_cut = []
try:
    _old_retired = json.load(io.open(os.path.join(HERE, "cut_retired.json"),
                                     encoding="utf-8"))
except Exception:
    _old_retired = []
try:
    _hwm = int(json.load(io.open(os.path.join(HERE, "cut_hwm.json"),
                                 encoding="utf-8"))["hwm"])
except Exception:
    _hwm = 0
_hwm = max([_hwm, 26] + [_c["id"] for _c in _old_cut]
           + [_c["id"] for _c in _old_retired])
_retired_ids = {_c["id"] for _c in _old_retired}
_prev_by_key = {}
for _c in _old_cut:
    _prev_by_key.setdefault((_c["donor"], _statkey(_c["stats"])), _c["id"])
_used_ids = set()


def assign_id(donor, stats):
    """id строки: прежний, если у донора была строка ровно с такими статами;
    иначе — новый, выше отметки прилива."""
    global _hwm
    rid = _prev_by_key.get((donor, _statkey(stats)))
    if rid is not None and rid not in _used_ids and rid not in _retired_ids:
        _used_ids.add(rid)
        return rid
    _hwm += 1
    _used_ids.add(_hwm)
    return _hwm


cut = []
# у брони плюс ОБЩЕГО урона не чеканится никогда (True = лимит уже исчерпан):
# четыре слота тела стакали бы то, что пулы брони не дают вовсе
ap_used = {"steelsword": False, "silversword": False,
           "armor": True, "pants": True, "gloves": True, "boots": True,
           # вспомогательное: свой плюс общего урона не чеканится — урон
           # такому оружию даёт мечевой жетон урона
           "secondary": True, "blunt1h": True, "staff2h": True,
           "spear2h": True, "axe1h": True, "axe2h": True,
           "cleaver1h": True, "hammer2h": True, "halberd2h": True}
skipped_ap = 0
orphan_minus = 0     # доноров, чьи минусы спасены из выброшенных кусков

# СКЕЛЕТ брони (решение пользователя 02.09, скрин доспеха Кота): броня,
# вес-класс, сопротивления и повадки веса завязаны друг на друга — едут
# ЦЕЛИКОМ в жетоне защиты, строками остаются только уникальные баффы
ARMOR_SKEL_ATTRS = {
    "slashing_resistance_perc", "piercing_resistance_perc",
    "bludgeoning_resistance_perc", "elemental_resistance_perc",
    "armor_speed", "armor_regen_penalty", "armor_stamina_efficiency",
    "staminaRegen_armor_mod",
}
_ARMOR_CATS = ("armor", "pants", "gloves", "boots")
_armor_skel = {}   # донор -> [(attr, typ, v), ...]

deferred = []      # строки, чей ap-плюс срезан красным правилом: id В КОНЕЦ,
                   # чтобы существующие номера (жетоны/абилки игроков) не съехали
for d in sorted(DONORS, key=lambda x: x["name"]) \
        + sorted(ARMOR_DONORS, key=lambda x: x["name"]):
    donor = d["name"]
    # тяжёлые двуручники W3EE кузнице не поддаются (ГД 24.09)
    if _is_no_forge(donor):
        continue
    rows, waste = profile_of(donor)
    # вампиризм проклятых реликтов (Плакальщица, Чёрный Единорог) живёт
    # теперь В САМИХ ЧАРАХ «Тёмное проклятье» (ГД 24.09) — строкой не режется
    if "SwordDarkCurseEffect" in card_abils.get(donor, {}).get("tags", []):
        rows = [r for r in rows if r[0] != "lifesteal"]
    if d["cat"] in _ARMOR_CATS:
        skel = [(a, t, round(v, 4)) for a, t, v in rows
                if a in ARMOR_SKEL_ATTRS]
        if skel:
            _armor_skel[donor] = skel
        rows = [r for r in rows if r[0] not in ARMOR_SKEL_ATTRS]
    if not rows:
        continue
    # броня — одним жетоном, оружие — как прежде
    lines = cut_profile(rows, waste, whole=d["cat"] in _ARMOR_CATS)

    # ⛔ СИРОТСКИЕ МИНУСЫ (сверка 18.09: два донора собирались легче
    # оригинала). Кусок, у которого после среза attack_power не осталось
    # других плюсов, выбрасывается — но его ДОЛЯ МИНУСОВ обязана остаться
    # в профиле, иначе копия теряет часть штрафов. Решаем судьбу кусков
    # заранее (на копии флага ap_used) и переливаем минусы выбывших в
    # первый выживший кусок. Выпуск ниже идёт в прежнем порядке — номера
    # жетонов не едут.
    _ap_probe = ap_used[d["cat"]]
    _dropped, _alive = [], []
    for _ln in lines:
        _has = any(a == "attack_power" and v > 0 for a, _t, v in _ln["plus"])
        if _has and _ap_probe:
            _rest = [p for p in _ln["plus"]
                     if not (p[0] == "attack_power" and p[2] > 0)]
            (_alive if _rest else _dropped).append(_ln)
            continue
        if _has:
            _ap_probe = True
        _alive.append(_ln)
    if _dropped and _alive:
        # одна ось — одна запись: две строки одного свойства в одной
        # абилке движок не обязан складывать, поэтому складываем сами
        _sum = {}
        for a, ty, v in _alive[0]["minus"]:
            _sum[(a, ty)] = _sum.get((a, ty), 0.0) + v
        for _ln in _dropped:
            for a, ty, v in _ln["minus"]:
                _sum[(a, ty)] = _sum.get((a, ty), 0.0) + v
            _ln["minus"] = []
        _alive[0]["minus"] = [(a, ty, round(v, 4)) for (a, ty), v in _sum.items()]
        orphan_minus += 1

    for ln in lines:
        has_ap_plus = any(a == "attack_power" and v > 0 for a, _t, v in ln["plus"])
        if has_ap_plus:
            if ap_used[d["cat"]]:
                # мягкое красное правило: режем только сам attack_power-плюс;
                # остальная строка (вампиризм Единорога!) чеканится, id в конце
                rest = [p for p in ln["plus"]
                        if not (p[0] == "attack_power" and p[2] > 0)]
                if rest:
                    deferred.append((d, {"plus": rest, "minus": ln["minus"]}))
                skipped_ap += 1
                continue
            ap_used[d["cat"]] = True
        stats = ln["plus"] + ln["minus"]
        rid = assign_id(donor, [(a, t, round(v, 4)) for a, t, v in stats])
        cut.append({
            "id": rid,
            "donor": donor,
            "cat": d["cat"],
            "lockey": card_abils.get(donor, {}).get("lockey", ""),
            "icon": d.get("icon", ""),
            "ability": "FRG_C_%d" % rid,
            "card": "frg_cut_%d" % rid,
            "stats": [(a, t, round(v, 4)) for a, t, v in stats],
            "junk": False,
            # ⛔ ОБЫЧНЫХ свойств больше нет (ГД 23.09): каждая строка реликтовая
            "relic": True,
            # проклятой сцепки больше нет: вампиризм живёт в самих чарах
            "cursed": False,
        })

# добор: строки с вырезанным ap-плюсом — id наследуются тем же реестром
for d, ln in deferred:
    donor = d["name"]
    stats = ln["plus"] + ln["minus"]
    rid = assign_id(donor, [(a, t, round(v, 4)) for a, t, v in stats])
    cut.append({
        "id": rid,
        "donor": donor,
        "cat": d["cat"],
        "lockey": card_abils.get(donor, {}).get("lockey", ""),
        "icon": d.get("icon", ""),
        "ability": "FRG_C_%d" % rid,
        "card": "frg_cut_%d" % rid,
        "stats": [(a, t, round(v, 4)) for a, t, v in stats],
        "junk": False,
        "relic": True,
        "cursed": False,
    })

print("нарезано строк:", len(cut), "с", len({c['donor'] for c in cut}), "доноров")
print("attack_power-плюсов срезано (красное правило):", skipped_ap,
      "| строк возвращено в хвост:", len(deferred))
print("строк всего (все реликтовые с 23.09):", len(cut))

# пулы брони живут с id 2001 — нарезка не должна дотянуться
assert max(c["id"] for c in cut) < 2000, "нарезка упёрлась в диапазон пулов брони!"

# ⛔ ОТСТАВКА (24.09): прежняя строка без точной пары уходит на пенсию под
# своим id с ИСХОДНЫМИ статами; файл отставных только растёт
_new_ids = {c["id"] for c in cut}
assert len(_new_ids) == len(cut), "id выдан дважды!"
assert not (_new_ids & _retired_ids), "выдан id отставной строки!"
_retired = list(_old_retired)
for _c in _old_cut:
    if _c["id"] not in _new_ids and _c["id"] not in _retired_ids:
        _r = dict(_c)
        _r.pop("retired", None)
        _retired.append(_r)
        _retired_ids.add(_c["id"])
_retired.sort(key=lambda c: c["id"])
print("строк в отставке:", len(_retired), "(новых за эту сборку:",
      len(_retired) - len(_old_retired), ")")
# правило ГД: с донора не больше двух строк (броня — одна)
_per = {}
for _c in cut:
    _per[_c["donor"]] = _per.get(_c["donor"], 0) + 1
for _dn, _k in _per.items():
    _cat = next(c["cat"] for c in cut if c["donor"] == _dn)
    assert _k <= (1 if _cat in _ARMOR_CATS else 2), "у %s строк: %d" % (_dn, _k)

for _nm, _data in (("cut_data.json", cut), ("cut_retired.json", _retired),
                   ("cut_hwm.json", {"hwm": _hwm})):
    tmp = os.path.join(HERE, _nm + ".tmp")
    io.open(tmp, "w", encoding="utf-8").write(
        json.dumps(_data, ensure_ascii=False, indent=1))
    os.replace(tmp, os.path.join(HERE, _nm))
print("сохранено: forge/cut_data.json, cut_retired.json, cut_hwm.json (прилив %d)" % _hwm)
if 2000 - _hwm < 300:
    print("⚠️ ВНИМАНИЕ: до диапазона пулов брони (2001) осталось %d id — следующая "
          "крупная перерезка упрётся в assert" % (2000 - _hwm))

# ---- И-3: конверт мира (осевые капы) -----------------------------------------
# «Кованая вещь не может нести на одной оси больше, чем самая щедрая вещь
# Redux на этой оси» (архитектурный инвариант, одобрен ГД). Кап вычисляется
# из данных и сам переедет за обновлением Redux.
try:
    _reach = json.load(io.open(os.path.join(HERE, "reachable.json"),
                               encoding="utf-8"))
except Exception:
    _reach = {}

_env = {}


def _env_feed(axes):
    for _a, _s in axes.items():
        if _s > _env.get(_a, [0, ""])[0]:
            _env[_a] = [round(_s, 4), _feed_donor]


import collections as _coll
_by_donor = _coll.defaultdict(lambda: _coll.defaultdict(float))
for _c in cut:
    if _reach and not _reach.get(_c["donor"], False):
        continue                      # призраки конверт не расширяют
    for _a, _k, _v in _c["stats"]:
        if _k == "effect" or abs(_v) > 1.5 or _v <= 0:
            continue
        _by_donor[_c["donor"]][_a] += _v
for _feed_donor, _axes in _by_donor.items():
    _env_feed(_axes)
# характеры: вещь Redux несёт ровно один — каждый входит как виртуальная вещь
from lines_data import LINES as _LINES
for _rec in _LINES:
    _feed_donor = "pool:" + _rec[1]
    _ax = _coll.defaultdict(float)
    for _a, _k, _v in _rec[4]:
        if _k != "effect" and 0 < _v <= 1.5:
            _ax[_a] += _v
    _env_feed(_ax)

_tmp = os.path.join(HERE, "axis_caps.json.tmp")
io.open(_tmp, "w", encoding="utf-8").write(
    json.dumps(_env, ensure_ascii=False, indent=1))
os.replace(_tmp, os.path.join(HERE, "axis_caps.json"))
print("конверт мира: %d осей -> forge/axis_caps.json" % len(_env))

# ---- плоские урон-добавки карточек доноров (едут с жетоном урона) -------------
# Номер абилки (FRG_FD_<num>) НАСЛЕДУЕТСЯ из прежнего flat_data.json: абилка
# живёт на клинках игрока по имени, перенумерация сломала бы навешенное.
try:
    _old_flat = json.load(io.open(os.path.join(HERE, "flat_data.json"),
                                  encoding="utf-8"))
except Exception:
    _old_flat = {}
_old_flat = {k: v for k, v in _old_flat.items() if isinstance(v, dict)}
_next_num = max([v.get("num", 0) for v in _old_flat.values()] + [0]) + 1

def _kin(name):
    """Родня по имени: «X» <-> «X_crafted» (у Redux статы часто живут
    только на одной из пары карточек)."""
    return name[:-8] if name.endswith("_crafted") else name + "_crafted"


flat = {}
for d in DONORS:
    rows = []
    for src in (d["name"], _kin(d["name"])):
        if rows:
            break                     # своё найдено — родня не нужна
        for a in card_abils.get(src, {}).get("abil", []):
            node = abil.get(a)
            if node is None:
                continue
            for ch in node:
                try:
                    v = float(ch.get("min") or 0)
                except (TypeError, ValueError):
                    continue
                if is_flat_dmg(ch.tag, v):
                    rows.append((ch.tag, ch.get("type", "base"), v))
    if rows:
        if d["name"] in _old_flat and "num" in _old_flat[d["name"]]:
            num = _old_flat[d["name"]]["num"]
        else:
            num = _next_num
            _next_num += 1
        flat[d["name"]] = {"num": num, "rows": rows}
print("доноров с плоскими урон-добавками:", len(flat))

tmp = os.path.join(HERE, "flat_data.json.tmp")
io.open(tmp, "w", encoding="utf-8").write(
    json.dumps(flat, ensure_ascii=False, indent=1))
os.replace(tmp, os.path.join(HERE, "flat_data.json"))
print("сохранено: forge/flat_data.json")

# ---- карточная защита доноров-брони (авто ген брони в W3EE выключен) ----------
# Номера FRG_AD_<num> наследуются между пересборками (как у плоских).
try:
    _old_armor = json.load(io.open(os.path.join(HERE, "armor_data.json"),
                                   encoding="utf-8"))
except Exception:
    _old_armor = {}
_old_armor = {k: v for k, v in _old_armor.items() if isinstance(v, dict)}
_next_anum = max([v.get("num", 0) for v in _old_armor.values()] + [0]) + 1

armor_data = {}
for d in ARMOR_DONORS:
    total = 0.0
    for src in (d["name"], _kin(d["name"])):
        if total > 0:
            break
        for a in card_abils.get(src, {}).get("abil", []):
            node = abil.get(a)
            if node is None:
                continue
            for ch in node:
                if ch.tag != "armor":
                    continue
                try:
                    total += float(ch.get("min") or 0)
                except (TypeError, ValueError):
                    pass
    if total > 0:
        if d["name"] in _old_armor and "num" in _old_armor[d["name"]]:
            num = _old_armor[d["name"]]["num"]
        else:
            num = _next_anum
            _next_anum += 1
        # ВЕС-КЛАСС едет с защитой (решение пользователя: «броню и класс — от
        # кота, облик — от медведя»): 1 лёгкая / 2 средняя / 3 тяжёлая
        _tags = card_abils.get(d["name"], {}).get("tags", [])
        weight = (1 if "LightArmor" in _tags else
                  2 if "MediumArmor" in _tags else
                  3 if "HeavyArmor" in _tags else 0)
        armor_data[d["name"]] = {"num": num, "armor": round(total, 2),
                                 "weight": weight, "cat": d["cat"],
                                 "skel": _armor_skel.get(d["name"], [])}
print("доноров брони с защитой:", len(armor_data))

tmp = os.path.join(HERE, "armor_data.json.tmp")
io.open(tmp, "w", encoding="utf-8").write(
    json.dumps(armor_data, ensure_ascii=False, indent=1))
os.replace(tmp, os.path.join(HERE, "armor_data.json"))
print("сохранено: forge/armor_data.json")

# показать пример нарезки школ
for probe in ("Lynx School steel sword 3", "Gryphon School steel sword 3",
              "Cheesecutter"):
    print("\n===", probe, "===")
    for c in cut:
        if c["donor"] == probe:
            print("  ", c["card"], c["stats"])
