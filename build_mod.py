# -*- coding: utf-8 -*-
"""
Собирает отдельный мод modAardShatter поверх W3EE Redux.

Версия 1: разрыв Аардом (люди по стойке+HP, монстры по добиванию) + слоу-мо
по шансу + разнообразие финишеров. Латники (обёртка CanDismember с out-параметрами)
вынесены во вторую очередь — сначала надо убедиться, что @wrapMethod компилируется.

Чужие файлы НЕ копируются: используются аннотации Script Extensions.
"""
import os, sys, shutil, subprocess

GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
DOCS = os.path.join(os.environ["USERPROFILE"], "Documents", "The Witcher 3")
MOD  = os.path.join(GAME, "mods", "modAardShatter")
SCR  = os.path.join(MOD, "content", "scripts", "local")
CFG  = os.path.join(GAME, "bin", "config", "r4game", "user_config_matrix", "pc")

T = "\t"


def say(s=""):
    print(s, flush=True)


def head(s):
    say(); say("=" * 66); say("  " + s); say("=" * 66)


def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq witcher3.exe"],
                             capture_output=True, text=True, timeout=25).stdout
        return "witcher3.exe" in out.lower()
    except Exception:
        return False


def write_ws(path, text):
    """скрипты: UTF-16 LE с BOM, CRLF, табы"""
    data = text.replace("\n", "\r\n").encode("utf-16")   # utf-16 даёт BOM FF FE
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


# =====================================================================
CORE = """// AardShatter - Core.ws
// Helpers shared by all modules. ASH_ prefix avoids name clashes.

function ASH_Str( varName : name, fallback : string ) : string
{
\tvar s : string;

\ts = theGame.GetInGameConfigWrapper().GetVarValue('AardShatter', varName);
\tif( s == "" )
\t\treturn fallback;

\treturn s;
}

function ASH_Int( varName : name, fallback : int ) : int
{
\tvar s : string;

\ts = ASH_Str(varName, "");
\tif( s == "" )
\t\treturn fallback;

\treturn StringToInt(s);
}

function ASH_Float( varName : name, fallback : float ) : float
{
\tvar s : string;

\ts = ASH_Str(varName, "");
\tif( s == "" )
\t\treturn fallback;

\treturn StringToFloat(s);
}

function ASH_Bool( varName : name, fallback : bool ) : bool
{
\tvar s : string;

\ts = ASH_Str(varName, "");
\tif( s == "" )
\t\treturn fallback;

\tif( s == "true" || s == "1" )
\t\treturn true;

\treturn false;
}

// Identify Aard by the projectile that caused the damage.
// GetSignType() is blind to the heavy (alternate) cast, causer is not.
function ASH_IsAard( action : W3DamageAction ) : bool
{
\tif( (W3AardProjectile)action.causer )
\t\treturn true;

\treturn false;
}

// Igni is recognised the same way as Aard - by the projectile that caused it.
function ASH_IsIgni( action : W3DamageAction ) : bool
{
	if( (W3IgniProjectile)action.causer )
		return true;

	return false;
}

// Size / boss / gore-model gate.
// frost = true asks for frost wounds instead of explosion wounds.
function ASH_CanShatter( npc : CNewNPC, frost : bool ) : bool
{
\tvar dismComp : CDismembermentComponent;
\tvar wounds   : array<name>;

\tif( !npc )
\t\treturn false;

\tif( npc.IsHuge() )
\t\treturn false;

\tif( npc.WillBeUnconscious() )
\t\treturn false;

\tif( npc.HasTag('IsBoss') || npc.HasTag('MonsterHuntTarget') || npc.HasTag('olgierd_gpl') || npc.HasTag('PlayerWolfCompanion') )
\t\treturn false;

\tif( npc.HasAbility('Boss') || npc.HasAbility('SkillBoss') || npc.HasAbility('InstantKillImmune') || npc.HasAbility('DisableDismemberment') )
\t\treturn false;

\tif( npc.HasTag('DisableDismemberment') )
\t\treturn false;

\tdismComp = (CDismembermentComponent)npc.GetComponentByClassName('CDismembermentComponent');
\tif( !dismComp )
\t\treturn false;

\tif( frost )
\t\tdismComp.GetWoundsNames( wounds, WTF_Frost );
\telse
\t\tdismComp.GetWoundsNames( wounds, WTF_Explosion );

\treturn wounds.Size() > 0;
}

// Same bans as ASH_CanShatter but WITHOUT requiring explosion wound models.
// Used where a plain cut dismemberment is an acceptable fallback.
function ASH_CanBeTornApart( npc : CNewNPC ) : bool
{
\tif( !npc )
\t\treturn false;

\tif( npc.IsHuge() )
\t\treturn false;

\tif( npc.WillBeUnconscious() )
\t\treturn false;

\tif( npc.HasTag('IsBoss') || npc.HasTag('MonsterHuntTarget') || npc.HasTag('olgierd_gpl') || npc.HasTag('PlayerWolfCompanion') )
\t\treturn false;

\tif( npc.HasAbility('Boss') || npc.HasAbility('SkillBoss') || npc.HasAbility('DisableDismemberment') )
\t\treturn false;

\tif( npc.HasTag('DisableDismemberment') )
\t\treturn false;

\treturn true;
}

// Does this creature actually own explosion wound models?
function ASH_HasBoomWounds( npc : CNewNPC ) : bool
{
\tvar dismComp : CDismembermentComponent;
\tvar wounds   : array<name>;

\tif( !npc )
\t\treturn false;

\tdismComp = (CDismembermentComponent)npc.GetComponentByClassName('CDismembermentComponent');
\tif( !dismComp )
\t\treturn false;

\tdismComp.GetWoundsNames( wounds, WTF_Explosion );
\treturn wounds.Size() > 0;
}

// Optional slow motion on a successful shatter.
// Reuses the engine's existing InstantKill timescale source, so removal is done
// by the stock RemoveInstantKillSloMo timer - no @addMethod needed.
function ASH_TrySloMo()
{
\tvar chance   : int;
\tvar scale    : float;
\tvar duration : float;

\tchance = ASH_Int('SloMoChance', 35);

\tif( chance <= 0 || RandRange(100) >= chance )
\t{
\t\ttheGame.RemoveTimeScale( theGame.GetTimescaleSource( ETS_InstantKill ) );
\t\treturn;
\t}

\tscale = ASH_Float('SloMoScale', 0.30);
\tif( scale < 0.05f || scale > 1.f )
\t\tscale = 0.30;

\tduration = ASH_Float('SloMoTime', 0.50);
\tif( duration <= 0.f || duration > 3.f )
\t\tduration = 0.50;

\ttheGame.SetTimeScale( scale, theGame.GetTimescaleSource( ETS_InstantKill ), 32, true, true );
\tthePlayer.AddTimer( 'RemoveInstantKillSloMo', duration * scale );
}

function ASH_AddAnim( out arr : array<name>, animName : name )
{
\tif( animName == '' )
\t\treturn;

\tif( arr.Contains(animName) )
\t\treturn;

\tarr.PushBack(animName);
}
"""

# =====================================================================
SIGNS = """// AardShatter - Signs.ws
// PATH A: the NEXT sign hit on an already poise-broken target may tear it
//         apart. Chance grows as the target loses health; on a miss W3EE's
//         normal knockdown happens instead.
// PATH B: anything a sign delivers the killing blow to.

@wrapMethod(W3EECombatHandler) function DealPoiseDamage( actorVictim : CActor, action : W3DamageAction )
{
	var npcVictim     : CNewNPC;
	var npcPoise      : W3Effect_NPCPoise;
	var playerAtt     : W3PlayerWitcher;
	var shatterAction : W3DamageAction;
	var hpLimit, hpNow : float;
	var chance        : int;
	var allowed       : bool;

	wrappedMethod( actorVictim, action );

	// W3EE sets getShouldIgniExplode = true and never clears it, so one Eruption
	// glyphword kills every finisher until the game restarts. Clear it on any hit
	// that is not an Igni hit - W3EE re-arms it itself when it needs to.
	if( ASH_Bool('FixIgniLatch', true) )
	{
		if( !ASH_IsIgni(action) )
			getShouldIgniExplode = false;
	}

	allowed = false;
	if( ASH_IsAard(action) && ASH_Bool('HumanPoise', true) )
		allowed = true;
	else if( ASH_IsIgni(action) && ASH_Bool('IgniPoise', true) )
		allowed = true;

	if( !allowed )
		return;

	if( action.WasDodged() )
		return;

	playerAtt = (W3PlayerWitcher)action.attacker;
	if( !playerAtt )
		return;

	npcVictim = (CNewNPC)actorVictim;
	if( !npcVictim || !npcVictim.IsAlive() || !npcVictim.IsHuman() )
		return;

	// the poise must ALREADY be broken - this is the follow-up hit, not the one
	// that broke it
	npcPoise = (W3Effect_NPCPoise)actorVictim.GetBuff(EET_NPCPoise);
	if( !npcPoise || !npcPoise.IsPoiseBroken() )
		return;

	// a body already lying down cannot play the dismember animation
	if( npcVictim.HasBuff(EET_Knockdown) || npcVictim.HasBuff(EET_HeavyKnockdown) )
		return;

	// hard ceiling: never shatter above this health (100 = no ceiling)
	hpLimit = ((float)ASH_Int('HumanHP', 100)) / 100.f;
	hpNow   = npcVictim.GetHealthPercents();
	if( hpNow < 0.f || hpNow >= hpLimit )
		return;

	if( !ASH_CanShatter(npcVictim, false) )
		return;

	// chance grows with MISSING health: 70% left -> 30%, 30% left -> 70%
	chance = RoundMath( (1.f - hpNow) * 100.f * ((float)ASH_Int('ShatterScale', 100)) / 100.f );
	if( chance <= 0 || RandRange(100) >= chance )
		return;

	// separate damage action, exactly like the shipped Glyphword 3 code
	shatterAction = new W3DamageAction in theGame.damageMgr;
	shatterAction.Initialize( playerAtt, npcVictim, this, "AardShatter", EHRT_None, CPS_Undefined, false, false, true, false );
	shatterAction.SetInstantKill();
	shatterAction.SetForceExplosionDismemberment();
	shatterAction.SetIgnoreInstantKillCooldown();
	theGame.damageMgr.ProcessAction( shatterAction );
	delete shatterAction;

	ASH_TrySloMo();
}

@wrapMethod(W3EECombatHandler) function GetSignSkillDismember( action : W3DamageAction ) : bool
{
	var npcVictim : CNewNPC;
	var playerAtt : W3PlayerWitcher;

	if( wrappedMethod(action) )
		return true;

	npcVictim = (CNewNPC)action.victim;
	if( !npcVictim )
		return false;

	// PATH A - our own spawned shatter action, recognised by the forced flag
	if( action.HasForceExplosionDismemberment() )
		return true;

	playerAtt = (W3PlayerWitcher)action.attacker;
	if( !playerAtt )
		return false;

	if( ASH_IsAard(action) )
	{
		if( !ASH_Bool('KillShatter', true) )
			return false;
	}
	else if( ASH_IsIgni(action) )
	{
		if( !ASH_Bool('IgniKill', true) )
			return false;
	}
	else
	{
		return false;
	}

	if( !ASH_CanBeTornApart(npcVictim) )
		return false;

	if( npcVictim.IsHuman() && !ASH_Bool('KillShatterHumans', true) )
		return false;

	ASH_TrySloMo();
	return true;
}
"""

# =====================================================================
FINISHERS = """// AardShatter - Finishers.ws
// W3EE replaced the vanilla random finisher pool with a direction-based one,
// which collapses to a single animation when standing still. This widens it back.

@wrapMethod(W3EECombatHandler) function GetFinisherAnimsForDirection() : array<name>
{
\tvar arr        : array<name>;
\tvar i, size    : int;
\tvar mode       : int;
\tvar leftStance : bool;
\tvar syncMgr    : W3SyncAnimationManager;

\t// the original may be invoked ONLY ONCE per wrapper - keep its result
\tarr  = wrappedMethod();
\tmode = ASH_Int('FinVariety', 1);

\t// mode 0 - leave W3EE's direction-based pool exactly as it is
\tif( mode <= 0 )
\t\treturn arr;

\t// Headtaker deliberately wants its own single animation
\tif( GetWitcherPlayer() && GetWitcherPlayer().HasBuff(EET_SwordBehead) )
\t\treturn arr;

\t// mode 1+ - drop W3EE's direction pool and rebuild the vanilla one,
\t// so the game picks at random again instead of by movement key
\tarr.Clear();

\tleftStance = thePlayer.GetCombatIdleStance() <= 0.f;
\tsyncMgr    = theGame.GetSyncAnimManager();

\tif( leftStance || mode >= 2 )
\t{
\t\tASH_AddAnim(arr, 'man_finisher_02_lp');
\t\tASH_AddAnim(arr, 'man_finisher_04_lp');
\t\tASH_AddAnim(arr, 'man_finisher_06_lp');
\t\tASH_AddAnim(arr, 'man_finisher_07_lp');
\t\tASH_AddAnim(arr, 'man_finisher_08_lp');

\t\tif( syncMgr )
\t\t{
\t\t\tsize = syncMgr.dlcFinishersLeftSide.Size();
\t\t\tfor( i = 0; i < size; i += 1 )
\t\t\t\tASH_AddAnim(arr, syncMgr.dlcFinishersLeftSide[i].finisherAnimName);
\t\t}
\t}

\tif( !leftStance || mode >= 2 )
\t{
\t\tASH_AddAnim(arr, 'man_finisher_01_rp');
\t\tASH_AddAnim(arr, 'man_finisher_03_rp');
\t\tASH_AddAnim(arr, 'man_finisher_05_rp');

\t\tif( syncMgr )
\t\t{
\t\t\tsize = syncMgr.dlcFinishersRightSide.Size();
\t\t\tfor( i = 0; i < size; i += 1 )
\t\t\t\tASH_AddAnim(arr, syncMgr.dlcFinishersRightSide[i].finisherAnimName);
\t\t}
\t}

\tif( arr.Size() == 0 )
\t\tASH_AddAnim(arr, 'man_finisher_01_rp');

\treturn arr;
}
"""

# =====================================================================
DISMEMBER = """// AardShatter - Dismember.ws
// W3EE refuses dismemberment for several reasons, and all of them sit ABOVE the
// sign branch: heavy armour, battle mace in hand, wooden weapon, arrows.
// Any one of them blocks swords AND our sign shatter alike, and from outside we
// cannot tell which one fired. So we do not guess: if the original said no and
// the victim is a normal human, we say yes.
// A wrapper can only turn false into true, so this can never be worse than stock.

@wrapMethod(W3DamageManagerProcessor) function CanDismember( wasFrozen : bool, out dismemberExplosion : bool, out weaponName : name ) : bool
{
	var npcVictim : CNewNPC;
	var result    : bool;

	result = wrappedMethod( wasFrozen, dismemberExplosion, weaponName );
	npcVictim = (CNewNPC)actorVictim;

	if( result )
	{
		// Signs can ONLY be dismembered in explosion mode: the alternative path in
		// ProcessDismemberment needs an attack action, and a sign has none.
		if( ASH_IsAard(action) || ASH_IsIgni(action) || action.HasForceExplosionDismemberment() )
			dismemberExplosion = true;

		return true;
	}

	if( !npcVictim )
		return false;

	// hard bans stay hard: huge, bosses, quest-protected, going unconscious
	if( !ASH_CanBeTornApart(npcVictim) )
		return false;

	// our own spawned shatter action overrides every soft refusal
	if( action.HasForceExplosionDismemberment() )
	{
		dismemberExplosion = true;
		return true;
	}

	if( !ASH_Bool('ArmorDism', true) )
		return false;

	// only humans - monsters keep W3EE's own rules
	if( !actorVictim.IsHuman() )
		return false;

	if( RandRange(100) >= ASH_Int('ArmorChance', 100) )
		return false;

	if( ASH_IsAard(action) || ASH_IsIgni(action) )
		dismemberExplosion = true;

	return true;
}
"""

# =====================================================================
XML = """<?xml version="1.0" encoding="UTF-16"?>
<UserConfig>
\t<Group id="AardShatter" displayName="Mods.W3EE_w3ee.W3EE_addons.ash_menu">
\t\t<PresetsArray>
\t\t\t<Preset id="0" displayName="default">
\t\t\t\t<Entry varId="HumanPoise" value="true" />
\t\t\t\t<Entry varId="HumanHP" value="100" />
\t\t\t\t<Entry varId="ShatterScale" value="100" />
\t\t\t\t<Entry varId="KillShatter" value="true" />
\t\t\t\t<Entry varId="KillShatterHumans" value="true" />
\t\t\t\t<Entry varId="SloMoChance" value="35" />
\t\t\t\t<Entry varId="SloMoScale" value="0.30" />
\t\t\t\t<Entry varId="SloMoTime" value="0.50" />
\t\t\t\t<Entry varId="FinVariety" value="1" />
\t\t\t\t
				<Entry varId="IgniPoise" value="true" />
				<Entry varId="IgniKill" value="true" />
				<Entry varId="FixIgniLatch" value="true" />
				<Entry varId="ArmorDism" value="true" />
\t\t\t\t<Entry varId="ArmorChance" value="100" />
\t\t\t</Preset>
\t\t</PresetsArray>
\t\t<VisibleVars>
\t\t\t<Var overrideGroup="AardShatter" id="HumanPoise" displayName="ash_humanpoise" displayType="TOGGLE"/>
\t\t\t<Var overrideGroup="AardShatter" id="HumanHP" displayName="ash_humanhp" displayType="SLIDER;0;100;100"/>
\t\t\t<Var overrideGroup="AardShatter" id="ShatterScale" displayName="ash_shatterscale" displayType="SLIDER;0;200;200"/>
\t\t\t<Var overrideGroup="AardShatter" id="KillShatter" displayName="ash_killshatter" displayType="TOGGLE"/>
\t\t\t<Var overrideGroup="AardShatter" id="KillShatterHumans" displayName="ash_killshatterhumans" displayType="TOGGLE"/>
\t\t\t<Var overrideGroup="AardShatter" id="SloMoChance" displayName="ash_slomochance" displayType="SLIDER;0;100;100"/>
\t\t\t<Var overrideGroup="AardShatter" id="SloMoScale" displayName="ash_slomoscale" displayType="SLIDER;0.10;1.00;90"/>
\t\t\t<Var overrideGroup="AardShatter" id="SloMoTime" displayName="ash_slomotime" displayType="SLIDER;0.1;1.5;140"/>
\t\t\t<Var overrideGroup="AardShatter" id="FinVariety" displayName="ash_finvariety" displayType="SLIDER;0;2;2"/>
\t\t\t
			<Var overrideGroup="AardShatter" id="IgniPoise" displayName="ash_ignipoise" displayType="TOGGLE"/>
			<Var overrideGroup="AardShatter" id="IgniKill" displayName="ash_ignikill" displayType="TOGGLE"/>
			<Var overrideGroup="AardShatter" id="FixIgniLatch" displayName="ash_fixignilatch" displayType="TOGGLE"/>
			<Var overrideGroup="AardShatter" id="ArmorDism" displayName="ash_armordism" displayType="TOGGLE"/>
\t\t\t<Var overrideGroup="AardShatter" id="ArmorChance" displayName="ash_armorchance" displayType="SLIDER;0;100;100"/>
\t\t</VisibleVars>
\t</Group>
</UserConfig>
"""

# =====================================================================
head("СБОРКА МОДА modAardShatter")

if game_running():
    say("  ИГРА ЗАПУЩЕНА. Закройте её и запустите сборку снова.")
    sys.exit(3)

os.makedirs(SCR, exist_ok=True)
say("   папка: %s" % MOD)
say()

for fname, body in [("AardShatter - Core.ws", CORE),
                    ("AardShatter - Signs.ws", SIGNS),
                    ("AardShatter - Finishers.ws", FINISHERS),
                    ("AardShatter - Dismember.ws", DISMEMBER)]:
    n = write_ws(os.path.join(SCR, fname), body)
    say("   [ok] %-32s %6d Б  UTF-16 LE + BOM" % (fname, n))

xml_path = os.path.join(CFG, "AardShatter.xml")
with open(xml_path, "wb") as f:
    f.write(XML.replace("\n", "\r\n").encode("utf-8"))
say("   [ok] %-32s %6d Б  UTF-8 без BOM" % ("AardShatter.xml", os.path.getsize(xml_path)))

# ---- списки меню: UTF-16 LE с BOM ----
head("Регистрация меню в списках")
for fl in ("dx12filelist.txt", "dx11filelist.txt"):
    p = os.path.join(CFG, fl)
    if not os.path.exists(p):
        say("   [!!] нет файла %s" % fl); continue
    raw = open(p, "rb").read()
    if raw[:2] != b"\xff\xfe":
        say("   [!!] %s не UTF-16 LE — не трогаю" % fl); continue
    txt = raw.decode("utf-16")
    if "AardShatter.xml" in txt:
        say("   [--] %s — уже прописан" % fl); continue
    if not os.path.exists(p + ".bak_aardshatter"):
        shutil.copyfile(p, p + ".bak_aardshatter")
    sep = "" if txt.rstrip().endswith(";") else ";"
    txt = txt.rstrip() + sep + "\r\nAardShatter.xml;"
    open(p, "wb").write(txt.encode("utf-16"))
    say("   [ok] %s — дописан (бэкап рядом)" % fl)

# ---- mods.settings ----
head("Регистрация мода в mods.settings")
ms = os.path.join(DOCS, "mods.settings")
raw = open(ms, "rb").read()
enc = "utf-8"
txt = raw.decode(enc, "replace")
if "[modAardShatter]" in txt:
    say("   [--] уже прописан")
else:
    if not os.path.exists(ms + ".bak_aardshatter"):
        shutil.copyfile(ms, ms + ".bak_aardshatter")
    block = "[modAardShatter]\r\nEnabled=1\r\nPriority=15\r\n"
    txt = txt.rstrip("\r\n") + "\r\n" + block
    open(ms, "wb").write(txt.encode(enc))
    say("   [ok] добавлена секция [modAardShatter], Priority=15")

# ---- засев значений в живой файл настроек ----
head("Засев значений по умолчанию в dx12user.settings")
DEFAULTS = [("HumanPoise", "true"), ("HumanHP", "50"),
            ("KillShatter", "true"), ("KillShatterHumans", "true"),
            ("SloMoChance", "35"), ("SloMoScale", "0.30"),
            ("SloMoTime", "0.50"), ("FinVariety", "1"),
            ("ShatterScale", "100"), ("IgniPoise", "true"), ("IgniKill", "true"), ("FixIgniLatch", "true"), ("ArmorDism", "true"), ("ArmorChance", "100")]

us = os.path.join(DOCS, "dx12user.settings")
raw = open(us, "rb").read().decode("utf-8", "replace")
if "[AardShatter]" in raw:
    say("   [--] секция уже есть — значения не трогаю")
else:
    if not os.path.exists(us + ".bak_aardshatter"):
        shutil.copyfile(us, us + ".bak_aardshatter")
    block = "[AardShatter]\r\n" + "".join("%s=%s\r\n" % kv for kv in DEFAULTS)
    raw = raw.rstrip("\r\n") + "\r\n" + block
    open(us, "wb").write(raw.encode("utf-8"))
    say("   [ok] добавлена секция [AardShatter], %d значений" % len(DEFAULTS))
    for k, v in DEFAULTS:
        say("        %-18s = %s" % (k, v))

head("ГОТОВО")
say("   Мод собран. Чужие файлы НЕ копировались — только аннотации @wrapMethod.")
say()
say("   Запустите игру:")
say("     - дошла до меню  -> Script Extensions работают, всё скомпилировалось")
say("     - красный экран  -> прочитайте ПЕРВУЮ строку списка ошибок и скажите мне")
say()
say("   Настройки: Опции -> Моды -> Aard Shatter")
