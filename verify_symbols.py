# -*- coding: utf-8 -*-
"""
Статическая сверка мода modAardShatter с настоящим кодом игры.
Ищем каждый использованный символ в скриптах W3EE и ванили,
чтобы не ловить ошибки компиляции по одной за запуск.
"""
import os, re, io

G = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
ROOTS = [os.path.join(G, "mods", "modW3EE", "content", "scripts"),
         os.path.join(G, "mods", "mod0000_MergedFiles", "content", "scripts"),
         os.path.join(G, "content", "content0", "scripts")]

# что ищем -> каким шаблоном
CHECKS = [
    ("ОБЁРТКИ - сигнатуры обязаны совпадать", [
        ("DealPoiseDamage",            r"function\s+DealPoiseDamage\s*\("),
        ("GetSignSkillDismember",      r"function\s+GetSignSkillDismember\s*\("),
        ("GetFinisherAnimsForDirection", r"function\s+GetFinisherAnimsForDirection\s*\("),
        ("class W3EECombatHandler",    r"class\s+W3EECombatHandler"),
    ]),
    ("ТИПЫ", [
        ("W3SyncAnimationManager", r"class\s+W3SyncAnimationManager"),
        ("W3Effect_NPCPoise",      r"class\s+W3Effect_NPCPoise"),
        ("CDismembermentComponent", r"class\s+CDismembermentComponent"),
        ("W3AardProjectile",       r"class\s+W3AardProjectile"),
        ("CR4FinisherDLC",         r"(class|struct)\s+CR4FinisherDLC"),
    ]),
    ("МЕТОДЫ И ПОЛЯ", [
        ("IsPoiseBroken",          r"function\s+IsPoiseBroken\s*\("),
        ("GetWasPoiseBroken",      r"function\s+GetWasPoiseBroken\s*\("),
        ("IsHuge",                 r"function\s+IsHuge\s*\("),
        ("WillBeUnconscious",      r"function\s+WillBeUnconscious\s*\("),
        ("GetWoundsNames",         r"function\s+GetWoundsNames\s*\("),
        ("GetHealthPercents",      r"function\s+GetHealthPercents\s*\("),
        ("GetCombatIdleStance",    r"function\s+GetCombatIdleStance\s*\("),
        ("DealsAnyDamage",         r"function\s+DealsAnyDamage\s*\("),
        ("SetInstantKill",         r"function\s+SetInstantKill\s*\("),
        ("SetForceExplosionDismemberment", r"function\s+SetForceExplosionDismemberment\s*\("),
        ("HasForceExplosionDismemberment", r"function\s+HasForceExplosionDismemberment\s*\("),
        ("GetComponentByClassName", r"function\s+GetComponentByClassName\s*\("),
        ("dlcFinishersLeftSide",   r"dlcFinishersLeftSide\s*:"),
        ("finisherAnimName",       r"finisherAnimName\s*:"),
        ("GetTimescaleSource",     r"function\s+GetTimescaleSource\s*\("),
        ("RemoveTimeScale",        r"function\s+RemoveTimeScale\s*\("),
        ("SetTimeScale",           r"function\s+SetTimeScale\s*\("),
        ("RemoveInstantKillSloMo", r"RemoveInstantKillSloMo"),
        ("GetSyncAnimManager",     r"function\s+GetSyncAnimManager\s*\("),
        ("GetInGameConfigWrapper", r"function\s+GetInGameConfigWrapper\s*\("),
        ("GetVarValue",            r"function\s+GetVarValue\s*\("),
    ]),
    ("КОНСТАНТЫ", [
        ("EET_NPCPoise",           r"EET_NPCPoise"),
        ("EET_CounterStrikeHit",   r"EET_CounterStrikeHit"),
        ("EET_SwordBehead",        r"EET_SwordBehead"),
        ("ETS_InstantKill",        r"ETS_InstantKill"),
        ("WTF_Explosion",          r"WTF_Explosion"),
        ("WTF_Frost",              r"WTF_Frost"),
    ]),
    ("ГЛОБАЛЬНЫЕ ФУНКЦИИ", [
        ("StringToInt",   r"function\s+StringToInt\s*\("),
        ("StringToFloat", r"function\s+StringToFloat\s*\("),
        ("RandRange",     r"function\s+RandRange\s*\("),
        ("GetWitcherPlayer", r"function\s+GetWitcherPlayer\s*\("),
    ]),
]


def read(path):
    raw = open(path, "rb").read()
    if raw[:2] == b"\xff\xfe":
        return raw.decode("utf-16", "replace")
    return raw.decode("utf-8", "replace")


print("читаю скрипты игры...", flush=True)
blob = []
files = 0
for root in ROOTS:
    for base, _d, fs in os.walk(root):
        for fn in fs:
            if fn.lower().endswith(".ws"):
                try:
                    blob.append(read(os.path.join(base, fn)))
                    files += 1
                except Exception:
                    pass
BIG = "\n".join(blob)
print("файлов: %d, символов: %d\n" % (files, len(BIG)))

bad = []
for title, items in CHECKS:
    print("=" * 62)
    print("  " + title)
    print("=" * 62)
    for name, pat in items:
        n = len(re.findall(pat, BIG))
        mark = "OK " if n else "!! "
        print("   [%s] %-34s вхождений: %d" % (mark, name, n))
        if not n:
            bad.append(name)
    print()

print("=" * 62)
if bad:
    print("  НЕ НАЙДЕНО (потенциальные ошибки компиляции): %d" % len(bad))
    for b in bad:
        print("     -", b)
else:
    print("  ВСЕ СИМВОЛЫ НАЙДЕНЫ")
print("=" * 62)
