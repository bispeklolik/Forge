# -*- coding: utf-8 -*-
"""
modAssimAlcohol — алкоголь считается источником набора токсинов для Ассимиляции
(Glyphword 46/47/48 из W3EE Redux).

Суть: W3EE заводит "источник" (элемент toxicityEntries) только в эликсирной ветке
playerWitcher.ws:8302-8304. Вино/пиво идут ванильной веткой CR4Player.ConsumeItem
(modW3EE\\...\\r4Player.ws:12172-12177), где токсичность вливается прямо в стат через
GainStat и запись не создаётся. Мод вешает @wrapMethod(CR4Player) ConsumeItem и
после вызова оригинала заводит запись сам.

Кладётся ОТДЕЛЬНЫМ модом, чтобы не трогать чужой r4Player.ws (14k строк, не
смерджен, потеряется при обновлении W3EE).

⚠️ .ws пишется в UTF-16 LE + BOM, ТАБЫ, БЕЗ кириллицы (как build_lab.py).
Запуск:  python build_assim.py            — установить в игру
         python build_assim.py --dry DIR  — только собрать файл в DIR, игру не трогать
"""
import os, sys, re

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
DOCS = os.path.join(os.environ["USERPROFILE"], "Documents", "The Witcher 3")
MOD = os.path.join(GAME, "mods", "modAssimAlcohol")
PRIORITY = 22

WS = """// modAssimAlcohol - alcohol counts as a toxicity source for Assimilation.
//
// W3EE Redux counts "sources of toxicity gain" as the length of the array
// toxicityEntries inside W3Effect_Toxicity (modW3EE ...\\effects\\drain\\
// toxicity.ws:439). Glyphword 48 reads that length twice: the toxicity drain
// bonus (toxicity.ws:593-595, +5% per source, recalculated every tick) and the
// mutagen synergy (toxicity.ws:446 -> PlayerAbilityManager.ws:786-789, applied
// as ability stacks when the length changes).
//
// The array gets exactly one producer in the whole build: DrinkPreparedPotion
// (mod0000_MergedFiles ...\\playerWitcher.ws:8302-8304). Wine and beer take the
// other road - CR4Player.ConsumeItem (modW3EE ...\\r4Player.ws:12172-12177),
// which is the untouched vanilla block: it pours toxicity straight into the
// stat with GainStat and registers nothing. So the glyphword cannot see booze.
//
// This mod wraps ConsumeItem and registers the source itself. Nothing in
// modW3EE is edited, so Script Merger has nothing to merge: the wrap rides on
// top of whatever version of ConsumeItem is compiled.
//
// SETTINGS - the three ALC_* functions below, nothing else needs touching.

// How long one drink stays a "source", in seconds. 10 is the duration the data
// already gives alcohol (blob0 -> gameplay\\items\\def_item_edibles.xml:65-68,
// ability alco_toxicity: duration 10, toxicity 1). 30 would match the visible
// EET_Drunkenness buff (gameplay\\abilities\\effects.xml:184-186).
@addMethod(CR4Player) function ALC_SourceLife() : float
{
\treturn 10.f;
}

// true  - alcohol behaves like an elixir: the instant toxicity is handed back
//         and the entry feeds the same amount in over ALC_SourceLife seconds.
//         Total toxicity per drink is unchanged, only its timing.
// false - alcohol keeps its instant toxicity and the entry carries a token
//         amount (0.05) purely as a counter. Smallest possible footprint.
@addMethod(CR4Player) function ALC_SpreadToxicity() : bool
{
\treturn true;
}

// false - literal reading of the order: every mug is its own source.
// true  - only the first drink of a drunken spell counts (no source while
//         EET_Drunkenness is already up). Cheap guard against mug spamming.
@addMethod(CR4Player) function ALC_OncePerDrunk() : bool
{
\treturn false;
}

@wrapMethod(CR4Player) function ConsumeItem( itemId : SItemUniqueId ) : bool
{
\tvar toxBuff : W3Effect_Toxicity;
\tvar isAlco, wasDrunk, ok : bool;
\tvar toxBefore, toxAfter, gained, life : float;

\t// read the item BEFORE the original runs: ConsumeItem removes the item
\t// (r4Player.ws:12185) and the id can go invalid on the last one in a stack
\tisAlco = inv.IsIdValid(itemId)
\t\t&& inv.ItemHasTag(itemId, 'Alcohol')
\t\t&& CalculateAttributeValue(inv.GetItemAttributeValue(itemId, 'toxicity')) > 0.f;
\twasDrunk = HasBuff(EET_Drunkenness);
\ttoxBefore = GetStat(BCS_Toxicity, true);

\tok = wrappedMethod(itemId);

\tif( !ok || !isAlco )
\t\treturn ok;
\tif( ALC_OncePerDrunk() && wasDrunk )
\t\treturn ok;

\t// what the drink actually put in, capped toxicity bar included
\ttoxAfter = GetStat(BCS_Toxicity, true);
\tgained = toxAfter - toxBefore;
\tif( gained <= 0.f )
\t\treturn ok;

\t// the buff is born inside the original call, on the toxicity rising
\t// (PlayerAbilityManager.ws:541-543), so it can only be fetched now
\ttoxBuff = (W3Effect_Toxicity)GetBuff(EET_Toxicity);
\tif( !toxBuff )
\t\treturn ok;

\t// never zero: UpdateEntries and GetToxicityGain divide by it
\t// (toxicity.ws:541 and :643)
\tlife = MaxF(1.f, ALC_SourceLife());

\tif( ALC_SpreadToxicity() )
\t{
\t\t// order matters: the entry goes in first. DrainToxicity calls
\t\t// OnToxicityChanged, which drops the whole EET_Toxicity buff when the
\t\t// stat is back to zero AND the array is empty (PlayerAbilityManager.ws:537)
\t\ttoxBuff.AddToxicityEntry(EET_Drunkenness, gained, life);
\t\tabilityManager.DrainToxicity(gained);
\t}
\telse
\t{
\t\t// counter-only source. 0.05 over 10s = 0.005 gain per second, which stays
\t\t// above the 0.001 floor Assimilation I tests in toxicity.ws:620, so the
\t\t// drain is not frozen while the source lives
\t\ttoxBuff.AddToxicityEntry(EET_Drunkenness, 0.05f, life);
\t}

\treturn ok;
}

// Debug readout: how many sources the toxicity effect holds right now.
exec function alcsrc()
{
\tvar toxBuff : W3Effect_Toxicity;
\tvar msg : string;
\tvar n : int;

\ttoxBuff = (W3Effect_Toxicity)thePlayer.GetBuff(EET_Toxicity);
\tif( toxBuff )
\t\tn = toxBuff.GetToxicityEntryCount();

\tmsg = "sources: " + IntToString(n)
\t\t+ "   toxicity: " + FloatToString(thePlayer.GetStat(BCS_Toxicity));
\tif( thePlayer.HasAbility('Glyphword 48 _Stats', true) )
\t\tmsg += "   Assimilation III ON";

\ttheGame.GetGuiManager().ShowNotification(msg, 6000);
}
"""

# ---- сборка -----------------------------------------------------------------
body = WS.replace("\\t", "\t")
if "\\t" in body:
    raise SystemExit("буквальные \\t остались — не записываю")

bad = [w for w in ("def", "state", "enum", "in", "out", "default", "class",
                   "event", "timer", "entry", "saved", "quest", "single",
                   "final", "latent", "hint")
       if re.search(r"var\s+[^;:]*\b%s\b" % w, body)]
if bad:
    raise SystemExit("зарезервированное слово в имени переменной: " + ", ".join(bad))

cyr = [ln for ln in body.splitlines() if re.search(r"[А-Яа-яЁё]", ln)]
if cyr:
    raise SystemExit("кириллица в .ws: " + cyr[0])

dry = None
if "--dry" in sys.argv:
    dry = sys.argv[sys.argv.index("--dry") + 1]

d = os.path.join(dry if dry else MOD, "content", "scripts", "local")
os.makedirs(d, exist_ok=True)
p = os.path.join(d, "AssimAlcohol.ws")
data = body.replace("\n", "\r\n").encode("utf-16")
open(p, "wb").write(data)
print("   [ok] AssimAlcohol.ws  %d Б  UTF-16 LE + BOM  (табуляций: %d)"
      % (len(data), body.count("\t")))
print("        " + p)

if dry:
    print("   [--] сухой прогон: mods.settings не трогаю")
    raise SystemExit(0)

ms = os.path.join(DOCS, "mods.settings")
raw = open(ms, "rb").read().decode("utf-8", "replace")
if "[modAssimAlcohol]" in raw:
    print("   [--] уже прописан в mods.settings")
else:
    raw = raw.rstrip("\r\n") + "\r\n[modAssimAlcohol]\r\nEnabled=1\r\nPriority=%d\r\n" % PRIORITY
    open(ms, "wb").write(raw.encode("utf-8"))
    print("   [ok] прописан в mods.settings, Priority=%d" % PRIORITY)

print()
print("  ПРОВЕРКА В ИГРЕ (после перезапуска):")
print("     alcsrc()            сколько источников сейчас")
print("     выпить пиво         -> источников +1 на 10 секунд")
print("     надеть Glyphword 48 -> окно персонажа, синергия мутагенов +10% за источник")
