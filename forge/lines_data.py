# -*- coding: utf-8 -*-
"""Реестр строк конструктора — 26 пар из живых пулов W3EE Redux.

Извлечено из def_item_quality.xml (blob0 модаW3EE) 15.08.2026 — значения
ФИКСИРОВАНЫ на середине редуксовского диапазона [min..max]: движку нечего
роллить, сейв-скам мёртв. Состав пулов сверен с gameParams.ws:994-1021
(Master_Cavalry Редукс сам закомментировал — не включён; Magical_StrongCrits
числится и в мастерворке и в магии — здесь один раз).

Поля: (id, редукс-имя, наша абилка, junk, [(атрибут, тип, значение)...], ru, en)
  тип: mult | add | base — как в исходном XML
  junk: True = чистый минус, марка; каждая марка на вещи открывает +1 слот
        плюс-строки (база 2, потолок 4)
"""

LINES = [
    # -- общие: крошечные чистые плюсы (Редукс даёт их обычным вещам) ---------
    (1,  "Common_PoiseDamage",   "FRG_L_PoiseDamage",   False,
     [("poise_damage", "mult", 0.1)],
     "Увесистый", "Weighty"),
    (2,  "Common_ArmorPen",      "FRG_L_ArmorPen",      False,
     [("armor_reduction", "mult", 0.04)],
     "Гранёный", "Faceted"),
    (3,  "Common_CounterBonus",  "FRG_L_CounterBonus",  False,
     [("counter_damage_bonus", "mult", 0.1)],
     "Ответный", "Riposte"),
    (4,  "Common_CriticalBonus", "FRG_L_CriticalBonus", False,
     [("critical_hit_damage_bonus", "add", 0.1)],
     "Хлёсткий", "Keen"),

    # -- мастерские: плюс всегда в связке с минусом ---------------------------
    (5,  "Master_Heft",          "FRG_L_Heft",          False,
     [("attack_power", "mult", 0.3), ("attack_speed", "mult", -0.05)],
     "Тяжёлая рука", "Heft"),
    (6,  "Master_CrushBlocks",   "FRG_L_CrushBlocks",   False,
     [("damage_through_blocks", "mult", 0.5), ("attack_speed", "mult", -0.02)],
     "Крушитель блоков", "Block Crusher"),
    (7,  "Master_Conserve",      "FRG_L_Conserve",      False,
     [("attack_stamina_cost_bonus", "mult", 0.2), ("parry_stamina_cost_bonus", "mult", 0.2), ("attack_power", "mult", -0.05)],
     "Бережливость", "Conserve"),
    (8,  "Master_Needle",        "FRG_L_NeedleM",       False,
     [("attack_power_fast_style", "mult", -0.05), ("armor_reduction_fast_style", "mult", 0.2)],
     "Игла", "Needle"),
    (9,  "Master_Calculated",    "FRG_L_Calculated",    False,
     [("counter_damage_bonus", "mult", 0.3), ("parry_stamina_cost_bonus", "mult", 0.2), ("attack_speed", "mult", -0.05)],
     "Расчётливость", "Calculated"),
    (10, "Magical_StrongCrits",  "FRG_L_StrongCrits",   False,
     [("critical_hit_damage_bonus", "add", 0.2), ("critical_hit_chance", "add", 0.1), ("armor_reduction", "mult", -0.05)],
     "Жестокие криты", "Strong Crits"),
    (11, "Master_Butcher",       "FRG_L_Butcher",       False,
     [("dismember_stamina_gain", "add", 30.0), ("attack_power_heavy_style", "mult", 0.2), ("armor_reduction", "mult", -0.05)],
     "Мясник", "Butcher"),
    (12, "Master_Light",         "FRG_L_Light",         False,
     [("attack_stamina_cost_bonus", "mult", 0.2), ("poise_damage", "mult", -0.05)],
     "Лёгкость", "Light Touch"),

    # -- магические ------------------------------------------------------------
    (13, "Magical_Needle",       "FRG_L_NeedleG",       False,
     [("attack_power_fast_style", "mult", 0.2), ("attack_speed_fast_style", "mult", -0.05), ("armor_reduction", "mult", 0.1)],
     "Чародейская игла", "Arcane Needle"),
    (14, "Magical_Precision",    "FRG_L_Precision",     False,
     [("attack_speed", "mult", 0.1), ("critical_hit_chance", "add", 0.1), ("attack_power", "mult", -0.05)],
     "Точность", "Precision"),
    (15, "Magical_Sting",        "FRG_L_Sting",         False,
     [("armor_reduction", "mult", -0.05), ("poise_damage", "mult", 0.3), ("critical_hit_damage_bonus", "add", 0.2)],
     "Жало", "Sting"),
    (16, "Magical_Celerity",     "FRG_L_Celerity",      False,
     [("attack_speed", "mult", 0.1), ("attack_power", "mult", 0.05), ("attack_stamina_cost_bonus", "mult", 0.2)],
     "Проворство", "Celerity"),
    (17, "Magical_CleanSlice",   "FRG_L_CleanSlice",    False,
     [("attack_speed", "mult", 0.1), ("armor_reduction", "mult", 0.1), ("poise_damage", "mult", -0.1)],
     "Чистый срез", "Clean Slice"),
    (18, "Magical_Crush",        "FRG_L_Crush",         False,
     [("attack_power_heavy_style", "mult", 0.2), ("attack_speed_heavy_style", "mult", -0.05), ("poise_damage", "mult", 0.2)],
     "Сокрушение", "Crush"),
    (19, "Magical_Spellslinger", "FRG_L_Spellslinger",  False,
     [("spell_power", "mult", 0.1), ("vigor_regen", "mult", 0.3), ("attack_power", "mult", -0.05)],
     "Чароплёт", "Spellslinger"),
    (20, "Magical_Cleave",       "FRG_L_Cleave",        False,
     [("attack_power_heavy_style", "mult", 0.1), ("damage_through_blocks", "mult", 0.4), ("shield_disarm_chance", "mult", 0.2), ("attack_speed", "mult", -0.05)],
     "Рассечение", "Cleave"),
    (21, "Magical_Ram",          "FRG_L_Ram",           False,
     [("poise_damage", "mult", 0.3), ("shield_disarm_chance", "mult", 0.3), ("attack_speed", "mult", -0.05)],
     "Таран", "Ram"),

    # -- хлам: чистые минусы, валюта слотов ------------------------------------
    (22, "Common_Shitstained",   "FRG_L_Shitstained",   True,
     [("poison_resistance_perc", "base", -0.1), ("bonus_money", "add", -0.3)],
     "Засаленный", "Shitstained"),
    (23, "Common_Rusted",        "FRG_L_Rusted",        True,
     [("bleeding_resistance_perc", "base", -0.1), ("injury_resist", "mult", -0.1)],
     "Ржавый", "Rusted"),
    (24, "Common_IllFitting",    "FRG_L_IllFitting",    True,
     [("evade_speed", "mult", -0.1), ("safe_dodge_angle_bonus", "add", -10.0), ("graze_damage_reduction", "mult", -0.01)],
     "Неудобный", "Ill-Fitting"),
    (25, "Common_Chafing",       "FRG_L_Chafing",       True,
     [("attack_speed", "mult", -0.1), ("poise_bonus", "add", -5.0), ("movement_stamina_efficiency", "mult", -0.2)],
     "Натирающий", "Chafing"),
    (26, "Common_Flamboyant",    "FRG_L_Flamboyant",    True,
     [("damage_from_behind_def", "mult", -0.5)],
     "Вычурный", "Flamboyant"),
]

# ---- нарезка школ и реликтов (v1.1) ------------------------------------------
# forge/cut_data.json генерит build_cut.py: 250+ строк-пар из карточных
# профилей доноров. Единый реестр = LINES (1..26, пулы) + CUT (27+).
import io as _io
import json as _json
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))
try:
    CUT = _json.load(_io.open(_os.path.join(_HERE, "cut_data.json"),
                              encoding="utf-8"))
except Exception:
    CUT = []
# ⛔ ОТСТАВНЫЕ СТРОКИ (24.09): строка, чьи статы изменила перерезка, уходит
# «на пенсию» под СВОИМ id и с ИСХОДНЫМИ статами. Её абилку FRG_C_<id> несут
# уже выкованные клинки, её жетон может лежать в сумке — поэтому она
# ОБЪЯВЛЯЕТСЯ дальше (абилка, карточка, текст), но не чеканится и не
# предлагается: жетоны при загрузке меняются на новые строки донора.
try:
    CUT_RETIRED = _json.load(_io.open(_os.path.join(_HERE, "cut_retired.json"),
                                      encoding="utf-8"))
except Exception:
    CUT_RETIRED = []
# ⛔ реестр отставных несущий: пропал файл при живой отметке прилива —
# старые клинки игрока потеряли бы свойства (движок не найдёт абилку)
if not CUT_RETIRED and _os.path.exists(_os.path.join(_HERE, "cut_hwm.json")):
    raise SystemExit("cut_retired.json пропал, а cut_hwm.json есть — сборку не продолжаю")
for _r in CUT_RETIRED:
    _r["retired"] = True
    # старая «проклятая» строка несла вампиризм проклятья сама — клинку с
    # ней чары не добавляют второй (иначе вышло бы +20%)
    _r["vamp_line"] = bool(_r.get("cursed"))
    _r["relic"] = True       # обычных свойств нет ни у кого (ГД 23.09)
    _r["cursed"] = False     # вампиризм проклятья живёт в чарах (ГД 24.09)
CUT = CUT + CUT_RETIRED

# ⛔ Кузнице не поддаются (решение ГД 24.09): тяжёлые двуручные топоры,
# молоты и булавы W3EE — «слишком жирные плюсы», разобрать/изучить их
# через кузницу нельзя вовсе. Вся семья имени: X / X_crafted / NGP X.
NO_FORGE_BASES = ["geralt_axe_01", "geralt_axe_02", "geralt_axe_03",
                  "geralt_hammer_01", "geralt_hammer_02", "geralt_hammer_03",
                  "geralt_mace_01", "geralt_mace_02", "geralt_mace_03"]


def no_forge_family():
    out = []
    for b in NO_FORGE_BASES:
        out += [b, b + "_crafted", "NGP " + b, "NGP " + b + "_crafted"]
    return out


def is_no_forge(name):
    return name in set(no_forge_family())

# Плоские урон-добавки карточек доноров (build_cut → flat_data.json):
# {донор: {"num": N, "rows": [[атрибут, тип, значение]...]}}. Абилка в DLC —
# FRG_FD_<num>, вешается на клинок реликтовым улучшением (жетон урона несёт
# ВЕСЬ урон донора, дизайн-док §3).
try:
    FLAT = _json.load(_io.open(_os.path.join(_HERE, "flat_data.json"),
                               encoding="utf-8"))
except Exception:
    FLAT = {}


def flat_ability(donor):
    return "FRG_FD_%d" % FLAT[donor]["num"]


# ---- БРОНЯ (этап Б) -----------------------------------------------------------
# Базовая защита брони донора (build_cut → armor_data.json): в W3EE броня —
# КАРТОЧНЫЙ стат (автоген брони выключен), поэтому переносится абилкой
# FRG_AD_<num>; штрафы тиров — снимаемые FRG_AP1..3 (-15/-10/-5% armor).
try:
    ARMOR = _json.load(_io.open(_os.path.join(_HERE, "armor_data.json"),
                                encoding="utf-8"))
except Exception:
    ARMOR = {}


def armor_ability(donor):
    return "FRG_AD_%d" % ARMOR[donor]["num"]


def armor_res_ability(donor):
    """Сопротивления и повадки веса — СВОЙ жетон (решение 05.09: облик /
    статы / показатели брони / уникальный бонус — четыре разных элемента)."""
    return "FRG_RS_%d" % ARMOR[donor]["num"]


def armor_has_res(donor):
    return bool(ARMOR.get(donor, {}).get("skel"))


ARMOR_TIER_PENALTY = [(1, "FRG_AP1", -0.15), (2, "FRG_AP2", -0.10),
                      (3, "FRG_AP3", -0.05)]

# Пул-строки брони Redux (armor_pools.json, 45): id фиксированно 2001+,
# сортировка по (пул, абилка) — файл статичен, номера навсегда.
_POOL_RU = {
    "ExtraPockets": "Лишние карманы", "ThickPadding": "Плотный поддоспешник",
    "Lightweight": "Облегчённая выделка", "Hefted": "Утяжеление",
    "Warding": "Обережные руны", "Tenacious": "Живучесть",
    "Ferocious": "Свирепость", "Fragrant": "Пропитка от ядов",
    "TightlyFitted": "Точная подгонка", "Eager": "Рвение",
    "Noble": "Благородная отделка", "Stalwart": "Несокрушимость",
    "Trickster": "Плутовство", "WellFitted": "Ладный крой",
    "WellTempered": "Добрая закалка",
}
_WEIGHT_RU = {"Light": "лёгк.", "Medium": "средн.", "Heavy": "тяж."}
ARMOR_POOL_BASE = 2001

try:
    _apools = _json.load(_io.open(_os.path.join(_HERE, "armor_pools.json"),
                                  encoding="utf-8"))
except Exception:
    _apools = []

# (id, redux-имя, наша абилка, вес Light/Medium/Heavy, stats, ru, en)
ARMOR_LINES = []
for _i, _p in enumerate(sorted(_apools, key=lambda x: (x["pool"], x["ability"]))):
    _base = _p["ability"].split("_")[-1]
    _weight = ("Light" if "_Light_" in _p["ability"] else
               "Medium" if "_Medium_" in _p["ability"] else "Heavy")
    _en_base = "".join((" " + ch if ch.isupper() else ch) for ch in _base).strip()
    ARMOR_LINES.append((
        ARMOR_POOL_BASE + _i, _p["ability"], "FRG_L_A%d" % (ARMOR_POOL_BASE + _i),
        _weight, [tuple(s) for s in _p["stats"]],
        "%s (%s)" % (_POOL_RU.get(_base, _base), _WEIGHT_RU[_weight]),
        "%s (%s)" % (_en_base, _weight.lower()),
    ))


def all_line_ids():
    return [rec[0] for rec in LINES] + [c["id"] for c in CUT]


# ---------------------------------------------------------------- ПОРОКИ ----
FLAW_BASE = 3001         # id-диапазон марок: 3001+ (пулы брони 2001+, нарезка <2000)

# (id, абилка, ru, en, статы, вес)  вес: 1 = лёгкая (+обычное место),
#                                          2 = тяжёлая (+реликтовое место)
# Пары «лёгкая/тяжёлая» идут подряд: одна ось — два жетона.
FLAWS = []
_FLAW_SPECS = [
    # --- вне боя: обслуживание и снаряжение --------------------------------
    ("Grimy", "Засаленный", "Grimy",
     "Жир и сажа въелись в сталь. Кромка садится быстрее, чем камень успевает её вернуть.",
     [("indestructible", "add", -0.30)],
     [("indestructible", "add", -0.45)]),
    ("Parched", "Пересушенный", "Parched",
     "Сталь пересушена и жадна. Всякая мазь уходит в поры и работает вполсилы.",
     [("oil_poison_effect", "mult", -0.06), ("oil_bleed_effect", "mult", -0.06),
      ("oil_falka_injury_chance", "mult", -0.06), ("oil_flammable_effect", "mult", -0.06)],
     [("oil_poison_effect", "mult", -0.10), ("oil_bleed_effect", "mult", -0.10),
      ("oil_falka_injury_chance", "mult", -0.10), ("oil_flammable_effect", "mult", -0.10)]),
    ("Rancid", "Прогорклый", "Rancid",
     "Сталь отдаёт прогорклым. Ведьмачья химия рядом с ней выгорает быстрее обычного.",
     [("potion_duration_bonus", "add", -0.07)],
     [("potion_duration_bonus", "add", -0.15)]),
    ("Greedy", "Жадный", "Greedy",
     "Сталь пьёт из хозяина. Порезы под ней затягиваются нехотя.",
     [("vitalityRegen", "add", -1.0), ("vitalityCombatRegen", "add", -1.0)],
     [("vitalityRegen", "add", -2.0), ("vitalityCombatRegen", "add", -2.0)]),

    # --- оборона: как держишь удар -----------------------------------------
    ("Flimsy", "Хлипкий", "Flimsy",
     "Тонкая безвольная полоса. Держать чужой клинок таким тяжелее, и часть удара доходит до тебя.",
     [("parry_stamina_cost_bonus", "mult", -0.15), ("damage_negation_defense", "mult", -0.12)],
     [("parry_stamina_cost_bonus", "mult", -0.35), ("damage_negation_defense", "mult", -0.30)]),
    ("Ungainly", "Развесистый", "Ungainly",
     "Клинок тяжело висит на бедре и цепляет всё подряд. Отскочить с ним — уже работа.",
     [("movement_stamina_efficiency", "mult", -0.12)],
     [("movement_stamina_efficiency", "mult", -0.30)]),
    ("Skittish", "Норовистый", "Skittish",
     "Баланс ушёл к острию. Начал замах — тебя из него выбьют там, где раньше ты бы устоял.",
     [("stagger_resist_bonus", "add", -0.10)],
     [("stagger_resist_bonus", "add", -0.20)]),
    ("Clotted", "Присохший", "Clotted",
     "Бурые разводы не сходят ни с клинка, ни с рук. Раны и отрава держатся дольше положенного.",
     [("bleed_stack_timer_reduction", "mult", -0.15),
      ("poison_stack_timer_reduction", "mult", -0.15)],
     [("bleed_stack_timer_reduction", "mult", -0.40),
      ("poison_stack_timer_reduction", "mult", -0.40)]),

    # --- ресурсы: чем платишь за приёмы ------------------------------------
    ("Overquenched", "Остуженный", "Overquenched",
     "Клинок остужен не в тот срок. В руке он не разгоняет кровь: кураж копится вяло.",
     [("focus_gain", "mult", -0.10)],
     [("focus_gain", "mult", -0.25)]),
    ("Stiff", "Тугой", "Stiff",
     "Тугой в замахе. Меч идёт как сквозь воду: на каждый удар уходит больше сил.",
     [("attack_stamina_cost_bonus", "mult", -0.07)],
     [("attack_stamina_cost_bonus", "mult", -0.15)]),
    ("Hollowed", "Порожний", "Hollowed",
     "Клинок порожний — держит форму, но не держит силу. Между Знаками приходится ждать дольше.",
     [("vigor_regen", "mult", -0.10)],
     [("vigor_regen", "mult", -0.20)]),

    # --- бой: что клинок оставляет в противнике ----------------------------
    ("Deadened", "Глухой", "Deadened",
     "Сталь глухая. Знак уходит в клинок и вязнет, а Квен садится тоньше обычного.",
     [("spell_power", "mult", -0.07)],
     [("spell_power", "mult", -0.15)]),
    ("Slick", "Гладкий", "Slick",
     "Кромка выведена слишком ровно, без злого зуба. Режет чисто — и потому не рвёт и не калечит.",
     [("injury_chance", "mult", -0.15)],
     [("injury_chance", "mult", -0.40), ("num_bleed_stacks", "add", -1)]),
    ("Weightless", "Невесомый", "Weightless",
     "Невесомый клинок. Бьёт остро, но не тяжело — врага от него не шатает.",
     [("poise_damage", "mult", -0.10)],
     [("poise_damage", "mult", -0.20)]),
]
# имя жетона обязано объяснять себя само: что это и что даёт
# обычных свойств нет (ГД 23.09): тяжёлый порок даёт ТРЕТЬЕ место, лёгкий —
# ничего (из выбора убран ещё 18.09, имя честно это говорит)
_RU_W = {1: "Порок: %s (лёгкий, места не даёт)", 2: "Порок: %s (+1 место под свойство)"}
_EN_W = {1: "Flaw: %s (light, gives no slot)", 2: "Flaw: %s (+1 property slot)"}
for _i, (_key, _ru, _en, _tip, _light, _heavy) in enumerate(_FLAW_SPECS):
    for _w, _stats in ((1, _light), (2, _heavy)):
        FLAWS.append((
            FLAW_BASE + _i * 2 + (_w - 1),        # id
            "FRG_F_%s%d" % (_key, _w),            # абилка
            _RU_W[_w] % _ru,                      # ru-имя жетона
            _EN_W[_w] % _en,                      # en-имя
            _stats,                               # статы
            _w,                                   # вес: 1 лёгкий / 2 тяжёлый
            _tip,                                 # подсказка (ru)
        ))


def flaw_by_id(fid):
    for rec in FLAWS:
        if rec[0] == fid:
            return rec
    return None


TOKEN_ITEM = "FRG Line Token"
LINE_LIMIT_BASE = 1      # плюс-строк на болванке без желобов и марок
LINE_LIMIT_MAX = 5       # жёсткий потолок: желоба IV (5) либо желоба + junk

# «Клеймо мастера» — капелька за возню (решение пользователя 15.08.2026):
# ОДИН маленький ЧИСТЫЙ плюс по выбору, БЕЗ минуса и БЕЗ занятия слота строки.
# Честность: Редукс сам раздаёт такие крошечные чистые плюсы common-луту
# бесплатно (пул WEAPON_COMMON) — мы даём такой же, но по выбору и за деньги.
# Одно клеймо на вещь. Значения = common-пул дословно.
TEMPER = [
    (1, "FRG_T_Weighty",  [("poise_damage", "mult", 0.075)],
     "Клеймо: увесистое",  "Mark: weighty"),
    (2, "FRG_T_Faceted",  [("armor_reduction", "mult", 0.03)],
     "Клеймо: гранёное",   "Mark: faceted"),
    (3, "FRG_T_Riposte",  [("counter_damage_bonus", "mult", 0.075)],
     "Клеймо: ответное",   "Mark: riposte"),
    (4, "FRG_T_Keen",     [("critical_hit_damage_bonus", "add", 0.075)],
     "Клеймо: хлёсткое",   "Mark: keen"),
]

BLANK_DURABILITY = 125   # против 100 у 595 из 602 мечей игры: кована на совесть

# «ПУТЬ КЛИНКА» — ступени качества (дизайн-док v2 ОДОБРЕН старшим ГД 21.08.2026).
# Тир хранится ЧИСЛОМ на экземпляре (FRG_Tier); абилки FRG_Q2..Q4 несут ТОЛЬКО
# quality add 1 каждая: урон растёт РОДНОЙ формулой качества W3EE (штраф стопок
# -7/-5/-3/0 для качеств 1..4), подпись и цвет пересчитываются движком сами.
# Все рецепты у ПОДМАСТЕРЬЯ (решение старшего ГД: гейт мастерства уже зашит в
# доноров — гроссмейстерский меч сначала куётся у гроссмейстера).
# (тир, абилка +1 качества, дефицит стопок, [(кол-во, материал)...], ru, en)
TIERS = [
    (1, "",       7, [],
     "Обычный клинок",                 "Common blade"),
    (2, "FRG_Q2", 5, [(2, "Dark iron ingot")],
     "Улучшение I: мастерская работа", "Upgrade I: masterwork forging"),
    (3, "FRG_Q3", 3, [(2, "Dark steel ingot"), (1, "Meteorite ingot")],
     "Улучшение II: магическая работа", "Upgrade II: magical forging"),
    (4, "FRG_Q4", 0, [(1, "Dwimeryte ingot"), (1, "Monstrous essence")],
     "Улучшение III: реликтовая работа", "Upgrade III: relic forging"),
]
TIER_PRICES = {2: 50, 3: 100, 4: 150}

# «Урон как валюта» (решения пользователя 15.08.2026, вторая итерация):
# классы-карточки болванок — лишняя возня; вместо них ОДНА болванка на
# категорию, а урон-штраф вешается УРОВНЯМИ прямо на экземпляр — снимаемой
# абилкой, у мастера, в любой момент и в обе стороны.
#
# Иммерсивно: мастер вытачивает в клинке ЖЕЛОБА ПОД ГРАВИРОВКУ — жертвуешь
# массой клинка, получаешь места под строки. Уровень желобов = база слотов:
#   без желобов  0%  урона  1 слот
#   I   −5%             2 слота
#   II  −10%            3
#   III −15%            4
#   IV  −20%            5
# (уровень, абилка, штраф_урона, ru, en)
DMG_MARKS = [
    (1, "FRG_D_1", -0.05, "Желоба под гравировку I",   "Engraving grooves I"),
    (2, "FRG_D_2", -0.10, "Желоба под гравировку II",  "Engraving grooves II"),
    (3, "FRG_D_3", -0.15, "Желоба под гравировку III", "Engraving grooves III"),
    (4, "FRG_D_4", -0.20, "Желоба под гравировку IV",  "Engraving grooves IV"),
]


def stat_text(attrs):
    """Человекочитаемая строка статов: '+22% attack power, -7% attack speed'."""
    parts = []
    for attr, typ, val in attrs:
        if typ in ("mult",) or (typ in ("add", "base") and -1 < val < 1):
            num = "%+d%%" % round(val * 100)
        else:
            num = "%+g" % val
        parts.append("%s %s" % (num, attr.replace("_", " ")))
    return ", ".join(parts)


# ---- короткие подписи статов для компактного ховера окна ----------------------
# Ховер-тултип ингредиента рисует ОДНУ строку — длинные английские простыни
# обрезались («выбрать нереально»). Статы уходят в ЛОКАЛИЗАЦИЮ (там можно
# кириллицу) максимально короско: «+30% скв.блок, −8% скор.»
# Подписи — КАНОН русской локализации игры (мост en<->ru по id строк,
# scratchpad/canon_ru.json): не выдумывать слова, где игра уже перевела.
# Где канона в игре нет (Redux-статы) — понятное слово без изобретательства.
_SHORT_RU = {
    "attack_power": "Сила атаки", "attack_speed": "Скорость атаки",
    "armor_reduction": "Пробитие доспеха",
    "critical_hit_chance": "Шанс крит. удара",
    "critical_hit_damage_bonus": "Урон при крит. ударе",
    "damage_from_behind_off": "Урон со спины",
    "damage_from_behind_def": "Защита спины", "injury_chance": "Шанс увечья",
    "poise_damage": "Урон по стойкости", "poise_bonus": "Стойкость",
    "spell_power": "Мощь Знаков", "focus_gain": "Получение адреналина",
    "adrenaline_gain": "Получение адреналина",
    "attack_stamina_cost_bonus": "Выносливость атак",
    "parry_stamina_cost_bonus": "Выносливость парирования",
    "counter_damage_bonus": "Урон контратак",
    "damage_through_blocks": "Урон сквозь блок",
    "shield_disarm_chance": "Шанс обезоружить",
    "vigor_regen": "Восстановление энергии", "lifesteal": "Вампиризм",
    "buff_apply_chance": "Шанс эффекта",
    "dismember_chance_mult": "Шанс расчленения",
    "dismember_stamina_gain": "Энергия за расчленение",
    "attack_power_fast_style": "Сила быстрых атак",
    "attack_power_heavy_style": "Сила мощных атак",
    "attack_speed_fast_style": "Скорость быстрых атак",
    "attack_speed_heavy_style": "Скорость мощных атак",
    "armor_reduction_fast_style": "Пробитие быстрых атак",
    "spell_power_aard": "Мощь Аарда", "spell_power_igni": "Мощь Игни",
    "spell_power_yrden": "Мощь Ирдена", "spell_power_quen": "Мощь Квена",
    "spell_power_axii": "Мощь Аксия",
    "human_exp_bonus_when_fatal": "Опыт за людей",
    "nonhuman_exp_bonus_when_fatal": "Опыт за чудовищ",
    "instant_kill_chance": "Шанс мгновенного убийства",
    "evade_speed": "Скорость уклонения",
    "safe_dodge_angle_bonus": "Угол уклонения",
    "graze_damage_reduction": "Скользящий урон",
    "movement_stamina_efficiency": "Выносливость бега",
    "poison_resistance_perc": "Сопротивление ядам",
    "bleeding_resistance_perc": "Сопротивление кровотечению",
    "burning_resistance_perc": "Сопротивление огню",
    "slashing_resistance_perc": "Сопротивление рубящим ударам",
    "piercing_resistance_perc": "Сопротивление колющим ударам",
    "bludgeoning_resistance_perc": "Сопротивление ударному урону",
    "elemental_resistance_perc": "Сопротивление стихиям",
    "injury_resist": "Защита от увечий", "bonus_money": "Деньги с трупов",
    "indestructible": "Прочность", "carryweight_bonus": "Грузоподъёмность",
    "armor_speed": "Скорость (доспех)",
    "armor_regen_penalty": "Энергия (доспех)",
    "armor_stamina_efficiency": "Выносливость (доспех)",
    "staminaRegen_armor_mod": "Восстановление выносливости", "weight": "Вес",
    "item_level_min": "Мин. уровень", "item_level_max": "Макс. уровень",
    "SlashingDamage": "Рубящий урон", "SilverDamage": "Урон серебром",
    "ElementalDamage": "Урон стихиями", "PoisonDamage": "Урон ядом",
    "FireDamage": "Урон огнём", "ShockDamage": "Урон шоком",
    "PiercingDamage": "Колющий урон", "BludgeoningDamage": "Ударный урон",
    "RendingDamage": "Рвущий урон", "FrostDamage": "Урон холодом",
    # --- статы ПОРОКОВ (23.08): термины игровые, без выдумок ---------------
    "oil_poison_effect": "Действие ядовитых масел",
    "oil_bleed_effect": "Действие кровопускающих масел",
    "oil_falka_injury_chance": "Действие крови Фальки",
    "oil_flammable_effect": "Действие горючих масел",
    "potion_duration_bonus": "Длительность эликсиров",
    "vitalityRegen": "Восстановление здоровья",
    "vitalityCombatRegen": "Восстановление здоровья в бою",
    "damage_negation_defense": "Поглощение урона при блоке",
    "stagger_resist_bonus": "Устойчивость в замахе",
    "bleed_stack_timer_reduction": "Скорость заживления ран",
    "poison_stack_timer_reduction": "Скорость выведения яда",
    "num_bleed_stacks": "Глубина ран",
    "toxicity": "Предел токсичности",
    "toxicity_drain": "Выведение токсинов",
    "delayReduction": "Задержка восстановления",
    "delayReductionPoise": "Задержка возврата стойкости",
    "staminaRegen": "Восстановление выносливости",
    "action_speed": "Скорость действий",
    # --- всплыли после разреза жирных профилей (25.08) ---------------------
    "vitality": "Здоровье",
    "disarm_chance": "Шанс обезоруживания",
    "attack_stamina_cost": "Стоимость атак",
    "attack_power_horseback": "Сила атаки верхом",
    "armor_reduction_heavy_style": "Пробитие мощных атак",
    "attack_speed_fast_style_bonus": "Скорость быстрых атак",
    "quen_chance_on_projectile": "Квен от стрел",
    "instant_kill_chance_mult": "Шанс мгновенного убийства",
    "bonus_herb_chance": "Шанс лишних трав",
    "dismember_chance": "Шанс расчленения",
    "returned_silver_damage_mult": "Возврат урона серебром",
    "vitalityCombatRegen": "Восстановление здоровья в бою",
    "focus": "Адреналин",
    "stamina": "Выносливость",
    "essence": "Сущность",
}
_FX_SHORT_RU = {
    "PoisonEffect": "Отравление", "BleedingEffect": "Кровотечение",
    "ConfusionEffect": "Помутнение", "BurningEffect": "Горение",
    "StaggerEffect": "Потеря равновесия", "FreezingEffect": "Заморозка",
    "KnockdownEffect": "Нокдаун", "BlindnessEffect": "Ослепление",
    "SwarmEffect": "Рой",
    # эффекты, всплывшие в нарезке 25.08 (были обрывками «lowdown», «rozen»)
    "SlowdownFrostEffect": "Обморожение",
    "FrozenEffect": "Заморозка",
    "HypnotizedEffect": "Гипноз",
    "ParalyzedEffect": "Паралич",
    "ImmobilizeEffect": "Обездвиживание",
}


def stat_short(attrs, ru):
    """Компактная строка статов: RU кириллицей (уходит в w3strings), EN — как
    есть. Эффект-связка сливается в одно: «Отравление (шанс +15%)»."""
    parts = []
    fx_names = []
    fx_chance = 0.0
    for attr, typ, val in attrs:
        if isinstance(attr, str) and attr.startswith("desc_"):
            continue
        if typ == "effect" or (isinstance(attr, str) and attr.endswith("Effect")):
            fx_names.append(_FX_SHORT_RU.get(attr, attr.replace("Effect", ""))
                            if ru else attr.replace("Effect", ""))
            continue
        if attr == "buff_apply_chance":
            fx_chance += val
            continue
        if typ in ("mult",) or (typ in ("add", "base") and -1 < val < 1):
            num = "%+d%%" % round(val * 100)
        else:
            num = "%+g" % val
        label = _SHORT_RU.get(attr, attr.replace("_", " ")) if ru \
            else attr.replace("_", " ")
        parts.append("%s %s" % (num, label))
    if fx_names:
        joined = "+".join(fx_names)
        if fx_chance > 0:
            joined += " (%s %+d%%)" % ("шанс" if ru else "chance",
                                       round(fx_chance * 100))
        parts.insert(0, joined)
    elif fx_chance > 0:
        parts.insert(0, "%+d%% %s" % (round(fx_chance * 100),
                                      "шанс эффектов" if ru else "effect chance"))
    return ", ".join(parts)
