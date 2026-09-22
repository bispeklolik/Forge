# -*- coding: utf-8 -*-
"""Мерж Dynamic Ragdolls -> W3EE damageManagerProcessor.ws, С НАСТРОЙКАМИ.

Переносится ЯВНЫЙ список (никакого слепого автомержа):
 A. Стоп криков трупов при добивании знаками (ProcessAction) [MuteCorpses].
 B. 8 var-объявлений рэгдоллов (ProcessActionReaction).
 C. Главный блок: свободные рэгдолл-смерти [RagdollChance, ForceScale] +
    дроп оружия на не-мечевых смертях [DropWeapons] + Deadly Counter
    [DeadlyCounter] (вместо else{ if(!canPerformFinisher...).
 D. Кулаки никогда не расчленяют [FistsNoDismember] (хвост CanDismember).
 E. Страховка: нокаутируемым не режем раны (ProcessDismemberment).

Настройки читаются функциями DRGD_* из modW3EERedux_DynRagdolls
(src/DynRagdolls.ws, меню собирает split/build.py; группа
W3EERedux_DynRagdolls). Пустое значение = дефолты мода.

НЕ переносится: finisherChance 100->10 (в W3EE это опция FinishChance),
выбор ран для людей (W3EE решает Combat().GetDismembermentTypes),
нокаут-гард CanDismember (у W3EE уже есть), форс dismember=true.
Результат: mod0000_MergedFiles (выигрывает у всех по алфавиту).
Скрипт идемпотентен: всегда стартует от чистой modW3EE-версии."""
import io, os, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
w3 = io.open(GAME + r"\mods\modW3EE\content\scripts\game\gameplay\damage\damageManagerProcessor.ws",
             encoding="utf-16").read().split("\n")
mod = io.open(r"C:\Users\New\AppData\Local\Temp\claude\D------------------code\28bae1e4-4e92-4125-ba96-2ee0cd5bc769\scratchpad\ragdolls\modDynamicRagdollsAndDeathAnimations\content\scripts\game\gameplay\damage\damagemanagerprocessor.ws",
              encoding="utf-16").read().split("\n")
out = list(w3)


def find1(needle_sub):
    hits = [k for k, l in enumerate(out) if needle_sub in l]
    assert len(hits) == 1, (needle_sub, len(hits))
    return hits[0]


# --- C. главный блок (первым: ниже по файлу, индексы выше не сдвинет) ----------
i = find1("if( !canPerformFinisher && CanDismember( wasFrozen, dismemberExplosion, weaponName ) )")
assert out[i-1].strip() == "" and out[i-2].strip() == "{" and out[i-3].strip() == "else", \
    (out[i-3], out[i-2], out[i-1])
block = list(mod[2284:2468])
assert block[0].strip() == "{" and "else if( !canPerformFinisher" in block[-1]

# C1: шанс рэгдолла — ползунок (3 места: люди + 2 группы монстров)
n_ch = 0
for k, l in enumerate(block):
    if "RandRange(100) < 10 )" in l:
        block[k] = l.replace("RandRange(100) < 10 )",
                             "RandRange(100) < DRGD_Int( 'RagdollChance', 10 ) )")
        n_ch += 1
assert n_ch == 3, n_ch

# C2: дроп оружия — переключатель
k = next(k for k, l in enumerate(block)
         if "if( wasAlive && actorVictim && !actorVictim.WillBeUnconscious()" in l)
block[k] = block[k].replace("if( wasAlive &&",
                            "if( DRGD_On( 'DropWeapons' ) && wasAlive &&")

# C3: Deadly Counter — переключатель
k = next(k for k, l in enumerate(block)
         if "IsMutationActive( EPMT_Mutation3 )" in l)
assert block[k-1].strip() == "if( playerAttacker", block[k-1]
block[k-1] = block[k-1].replace("if( playerAttacker",
                                "if( DRGD_On( 'DeadlyCounter' ) && playerAttacker")

# C4: сила отброса — ползунок (после вычисления ragdollForce)
k = next(k for k, l in enumerate(block) if "ragdollForce = 120.0f;" in l)
assert block[k+1].strip() == "}", block[k+1]
block[k+2:k+2] = ["\t\t\t\tragdollForce = ragdollForce * DRGD_Int( 'ForceScale', 100 ) / 100.0f;"]

out[i-2:i+1] = block
print("[C] главный блок: %d строк, шанс x3 + дроп + контрудар + сила" % len(block))

# --- B. var-объявления ----------------------------------------------------------
i = find1("var bleedCustomEffect")
VARS = mod[2230:2238]
assert "ragdollFxEnt" in VARS[-1] and "hitDir" in VARS[0]
out[i+1:i+1] = VARS
print("[B] 8 var-строк после W3EE:%d" % (i+1))

# --- A. стоп криков трупов [MuteCorpses] ---------------------------------------
i = find1("InitializeActionVars(act);")
SCREAM = list(mod[48:57])
assert "Stop corpse screams" in SCREAM[0] and SCREAM[-1].strip() == "}"
k = next(k for k, l in enumerate(SCREAM) if "if( actorVictim && !actorVictim.IsAlive() )" in l)
SCREAM[k] = SCREAM[k].replace("if( actorVictim &&",
                              "if( DRGD_On( 'MuteCorpses' ) && actorVictim &&")
out[i+1:i+1] = [""] + SCREAM
print("[A] стоп криков (с переключателем) после W3EE:%d" % (i+1))

# --- D. кулаки не расчленяют [FistsNoDismember] --------------------------------
i = find1("private function CanDismember( wasFrozen : bool, out dismemberExplosion : bool, out weaponName : name ) : bool")
depth = 0
end = -1
for k in range(i, len(out)):
    depth += out[k].count("{") - out[k].count("}")
    if depth == 0 and k > i + 2:
        end = k
        break
ret = -1
for k in range(end, i, -1):
    if out[k].strip() == "return dismember;":
        ret = k
        break
assert ret > 0, "return dismember не найден"
FISTS = [
    "",
    "\t\t// Fists / fist-fight never dismember (Dynamic Ragdolls, kingslayer997)",
    "\t\tif( DRGD_On( 'FistsNoDismember' ) && playerAttacker",
    "\t\t\t&& ( playerAttacker.inv.IsItemFists( weaponId )",
    "\t\t\t\t|| thePlayer.IsWeaponHeld( 'fist' )",
    "\t\t\t\t|| thePlayer.IsInFistFightMiniGame()",
    "\t\t\t\t|| thePlayer.IsFistFightMinigameEnabled() ) )",
    "\t\t{",
    "\t\t\tdismember = false;",
    "\t\t}",
]
out[ret:ret] = FISTS
print("[D] кулачный гард (с переключателем) перед return dismember (W3EE:%d)" % (ret+1))

# --- E. нокаут — без ран --------------------------------------------------------
fn = find1("private function ProcessDismemberment(wasFrozen : bool, dismemberExplosion : bool )")
i = next(k for k in range(fn, fn + 40)
         if "dismembermentComp = (CDismembermentComponent)" in out[k])
GUARD = [
    "\t\t// Knockout / guards get up - no wounds (Dynamic Ragdolls, kingslayer997)",
    "\t\tif( actorVictim.WillBeUnconscious() )",
    "\t\t\treturn;",
    "",
]
out[i:i] = GUARD
print("[E] нокаут-гард перед W3EE:%d" % (i+1))

# --- контроль -------------------------------------------------------------------
merged = "\n".join(out)
assert merged.count("{") == merged.count("}"), "СКОБКИ НЕ СХОДЯТСЯ"
for var in ("doHumanRagdoll", "skipArmRagdoll", "ragdollImpulse", "usedWoundCheck"):
    assert merged.count(var) >= 2, var
assert merged.count("DRGD_On") == 4 and merged.count("DRGD_Int") == 4, \
    (merged.count("DRGD_On"), merged.count("DRGD_Int"))
assert "gash_01" not in merged, "просочился wound-selection"
assert "finisherChance = 10;" not in merged, "просочился finisherChance"
assert "Free ragdoll deaths" in merged and "Stop corpse screams" in merged

dst = GAME + r"\mods\mod0000_MergedFiles\content\scripts\game\gameplay\damage"
os.makedirs(dst, exist_ok=True)
io.open(dst + r"\damageManagerProcessor.ws", "w", encoding="utf-16").write(merged)
print("[ok] mod0000_MergedFiles записан: %d строк (W3EE было %d)" % (len(out), len(w3)))
