# -*- coding: utf-8 -*-
"""
Собирает правки механики AardShatter и дописывает их в patches.json (шаг 6).

Якоря НЕ перепечатываются вручную — скрипт находит их в живых файлах и строит
блоки before/after из настоящих байтов. Это исключает ошибку в табах.
"""
import json, os, sys, io

G = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
COMBAT = os.path.join(G, r"mods\modW3EE\content\scripts\local\W3EE - Combat.ws")
DMG    = os.path.join(G, r"mods\modW3EE\content\scripts\game\gameplay\damage\damageManagerProcessor.ws")
OPTS   = os.path.join(G, r"mods\modW3EE\content\scripts\local\W3EE - Options.ws")
XML    = os.path.join(G, r"bin\config\r4game\user_config_matrix\pc\W3EnhancedEdition.xml")
HERE   = os.path.dirname(os.path.abspath(__file__))

T = "\t"
patches = []
errors = []


def read(path):
    raw = open(path, "rb").read()
    if raw[:2] == b"\xff\xfe":
        return raw.decode("utf-16"), "utf16"
    if raw[:3] == b"\xef\xbb\xbf":
        return raw[3:].decode("utf-8"), "utf8-bom"
    return raw.decode("utf-8"), "utf8-nobom"


def lines_of(txt):
    return txt.split("\r\n")


def add(pid, title, path, before, after, enc, note):
    txt, _ = read(path)
    n = txt.count(before)
    if n != 1:
        errors.append("%s: якорь встречается %d раз (нужен 1)" % (pid, n))
        return
    if after in txt:
        errors.append("%s: правка уже применена" % pid)
        return
    # В patches.json блоки хранятся с ОДИНАРНЫМ \n — apply.py сам подставит
    # перевод строки файла (строка 257). Если записать CRLF, получится \r\r\n.
    patches.append({"step": 6, "id": pid, "title": title, "file": path,
                    "encoding": enc,
                    "before": before.replace("\r\n", "\n"),
                    "after": after.replace("\r\n", "\n"),
                    "note": note})
    print("   [ok] %-5s %-46s +%d строк" % (pid, title[:46],
                                            after.count("\r\n") - before.count("\r\n")))


def find_line(ls, marker, expect=1):
    hits = [i for i, l in enumerate(ls) if marker in l]
    if len(hits) != expect:
        errors.append("маркер %r найден %d раз (ждали %d)" % (marker, len(hits), expect))
        return None
    return hits[0]


print("=== СБОРКА ПРАВОК AardShatter ===\n")

# ---------- A1: замена нокдауна на разлёт ----------
txt, enc = read(COMBAT)
ls = lines_of(txt)
# якорь по СОЧЕТАНИЮ строк: одиночный MultiplyAllDamageBy встречается 6 раз
cand = [k for k in range(len(ls) - 3)
        if "action.MultiplyAllDamageBy(2.f);" in ls[k]
        and "IsImmuneToBuff(EET_Knockdown)" in ls[k + 1]
        and "EET_LongStagger" in ls[k + 2]
        and ls[k + 3].strip() == "else"]
if len(cand) != 1:
    errors.append("A1: сочетание строк найдено %d раз (нужен 1)" % len(cand))
    i = None
else:
    i = cand[0]
if i is not None:
    before = "\r\n".join(ls[i:i + 4])
    if True:
        ind = ls[i][:len(ls[i]) - len(ls[i].lstrip(T))]
        after = "\r\n".join([
            ls[i],
            ind + "//AardShatter - Aard blows a broken-poise target apart instead of knocking it down",
            ind + "if( AardShatterAllowed(actorVictim, action) )",
            ind + "{",
            ind + T + "action.SetInstantKill();",
            ind + T + "action.SetForceExplosionDismemberment();",
            ind + "}",
            ind + "else " + ls[i + 1].lstrip(T),
            ls[i + 2],
            ls[i + 3],
        ])
        add("6.A1", "AardShatter: gib instead of knockdown", COMBAT, before, after, enc,
            "Аард при сломе стойки разносит цель вместо нокдауна")

# ---------- A2: гейт-предикат ----------
txt, enc = read(COMBAT)
ls = lines_of(txt)
i = find_line(ls, "public function ProcessPoisebreak(")
if i is not None:
    before = "\r\n".join(ls[i:i + 2])
    gate = [
        T + "//AardShatter - gate for the Aard poise-break gib",
        T + "public function AardShatterAllowed( actorVictim : CActor, action : W3DamageAction ) : bool",
        T + "{",
        T*2 + "var npcVictim : CNewNPC;",
        T*2 + "var dismemberComp : CDismembermentComponent;",
        T*2 + "var wounds : array< name >;",
        T*2 + "var chance : int;",
        T*2 + "var hp, healthLimit : float;",
        T*2,
        T*2 + "if( !(W3AardProjectile)action.causer )",
        T*3 + "return false;",
        T*2,
        T*2 + "npcVictim = (CNewNPC)actorVictim;",
        T*2 + "if( !npcVictim )",
        T*3 + "return false;",
        T*2,
        T*2 + "chance = Options().AardShatterChance();",
        T*2 + "if( chance <= 0 )",
        T*3 + "return false;",
        T*2,
        T*2 + "if( npcVictim.IsHuge() || npcVictim.HasTag('IsBoss') || npcVictim.HasTag('MonsterHuntTarget') )",
        T*3 + "return false;",
        T*2,
        T*2 + "if( npcVictim.HasAbility('Boss') || npcVictim.HasAbility('SkillBoss') || npcVictim.HasAbility('DisableFinishers') )",
        T*3 + "return false;",
        T*2,
        T*2 + "if( npcVictim.IsImmuneToInstantKill() )",
        T*3 + "return false;",
        T*2,
        T*2 + "if( npcVictim.HasAbility('DisableDismemberment') || npcVictim.HasTag('DisableDismemberment') )",
        T*3 + "return false;",
        T*2,
        T*2 + "healthLimit = Options().AardShatterHealth();",
        T*2 + "hp = npcVictim.GetHealthPercents();",
        T*2 + "if( hp < 0.f || hp * 100.f > healthLimit )",
        T*3 + "return false;",
        T*2,
        T*2 + "if( RandRange(100) >= chance )",
        T*3 + "return false;",
        T*2,
        T*2 + "dismemberComp = (CDismembermentComponent)npcVictim.GetComponentByClassName( 'CDismembermentComponent' );",
        T*2 + "if( !dismemberComp )",
        T*3 + "return false;",
        T*2,
        T*2 + "dismemberComp.GetWoundsNames( wounds, WTF_Explosion );",
        T*2 + "if( wounds.Size() == 0 )",
        T*3 + "return false;",
        T*2,
        T*2 + "return true;",
        T + "}",
        T,
    ]
    after = "\r\n".join(gate + ls[i:i + 2])
    add("6.A2", "AardShatter: gate predicate", COMBAT, before, after, enc,
        "Предикат: только Аард, не huge, не босс, есть модели кусков, порог HP, бросок кубика")

# ---------- C1: ветка в CanDismember ----------
txt, enc = read(DMG)
ls = lines_of(txt)
i = find_line(ls, "else if (actorVictim.WillBeUnconscious())")
if i is not None:
    before = "\r\n".join(ls[i:i + 5])
    if "// W3EE - Begin" not in before or "dismember = false;" not in before:
        errors.append("C1: соседние строки не те")
    else:
        ind = ls[i][:len(ls[i]) - len(ls[i].lstrip(T))]
        after = "\r\n".join(ls[i:i + 4] + [
            ind + "//AardShatter - flagged in ProcessPoisebreak, must win over weapon and armour filters",
            ind + "else if( (W3AardProjectile)action.causer && action.HasForceExplosionDismemberment() )",
            ind + "{",
            ind + T + "dismember = true;",
            ind + T + "dismemberExplosion = true;",
            ind + "}",
            ls[i + 4],
        ])
        add("6.C1", "AardShatter: CanDismember branch", DMG, before, after, enc,
            "Без неё расчленение не вызовется — знак уходит в чужую ветку")

# ---------- E1: дефолты при первой настройке ----------
txt, enc = read(OPTS)
ls = lines_of(txt)
i = find_line(ls, "wrapper.SetVarValue('SCOptionCR', 'KHPF', 0);")
if i is not None:
    before = "\r\n".join(ls[i:i + 2])
    ind = ls[i][:len(ls[i]) - len(ls[i].lstrip(T))]
    after = "\r\n".join([
        ls[i],
        ind + "//AardShatter - Aard poise-break gib",
        ind + "wrapper.SetVarValue('SCOptionCR', 'AGChance', \"35\");",
        ind + "wrapper.SetVarValue('SCOptionCR', 'AGHealth', \"50\");",
        ls[i + 1],
    ])
    add("6.E1", "AardShatter: defaults for new installs", OPTS, before, after, enc,
        "Дефолты 35/50 для тех, кто ставит мод с нуля")

# ---------- D1: геттеры опций ----------
txt, enc = read(OPTS)
ls = lines_of(txt)
i = find_line(ls, "public function KDisableHumanPoiseFinish() : bool")
if i is not None:
    before = "\r\n".join(ls[i - 1:i + 5])
    if "GetVarValue('SCOptionCR', 'KHPF')" not in before:
        errors.append("D1: соседние строки не те")
    else:
        getters = [
            T + "//AardShatter - Aard poise-break gib options",
            T + "public function AardShatterChance() : int",
            T + "{",
            T*2 + "var value : string;",
            T*2,
            T*2 + "value = theGame.GetInGameConfigWrapper().GetVarValue('SCOptionCR', 'AGChance');",
            T*2 + "if( value == \"\" )",
            T*3 + "return 35;",
            T*2,
            T*2 + "return StringToInt( value );",
            T + "}",
            T,
            T + "public function AardShatterHealth() : float",
            T + "{",
            T*2 + "var value : string;",
            T*2,
            T*2 + "value = theGame.GetInGameConfigWrapper().GetVarValue('SCOptionCR', 'AGHealth');",
            T*2 + "if( value == \"\" )",
            T*3 + "return 50.f;",
            T*2,
            T*2 + "return StringToFloat( value );",
            T + "}",
            T,
        ]
        after = "\r\n".join(ls[i - 1:i + 5] + getters)
        add("6.D1", "AardShatter: option getters", OPTS, before, after, enc,
            "Геттеры с фолбэком 35/50, если ключей ещё нет в настройках")

# ---------- F1: два ползунка в меню ----------
txt, enc = read(XML)
ls = lines_of(txt)
i = find_line(ls, 'id="KHPF"')
if i is not None:
    before = "\r\n".join(ls[i:i + 2])
    if "</VisibleVars>" not in ls[i + 1]:
        errors.append("F1: за строкой KHPF не следует </VisibleVars>")
    else:
        ind = ls[i][:len(ls[i]) - len(ls[i].lstrip(T))]
        after = "\r\n".join([
            ls[i],
            ind + '<Var id="AGChance" displayName="Aard Shatter - Chance" displayType="SLIDER;0;100;100" />',
            ind + '<Var id="AGHealth" displayName="Aard Shatter - Target Health" displayType="SLIDER;0;100;100" />',
            ls[i + 1],
        ])
        add("6.F1", "AardShatter: two sliders in menu", XML, before, after, enc,
            "Ползунки шанса и порога здоровья в разделе Finishers")

# ---------- итог ----------
print()
if errors:
    print("ОШИБКИ — ничего не записано:")
    for e in errors:
        print("   -", e)
    sys.exit(1)

pj = os.path.join(HERE, "patches.json")
data = json.load(open(pj, encoding="utf-8"))
data = [p for p in data if p.get("step") != 6]
data.extend(patches)
json.dump(data, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Записано правок в patches.json (шаг 6): %d" % len(patches))
print("Порядок применения задан сверху вниз — внутри файла снизу вверх.")
