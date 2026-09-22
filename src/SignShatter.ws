// SignShatter.ws  --  Sign Shatter, an add-on for W3EE Redux
//
// PATH A: the NEXT sign hit on an already poise-broken target may tear it apart.
//         The chance grows as the target loses health; on a miss W3EE's normal
//         knockdown happens instead.
// PATH B: anything a sign delivers the killing blow to is torn apart outright.
//
// Everything below is self-contained: this mod owns what SIGNS do to a body and
// nothing else. Swords are the business of a different mod, so the two never
// need each other to work.


// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

function SSHT_Str( varName : name, fallback : string ) : string
{
	var s : string;

	s = theGame.GetInGameConfigWrapper().GetVarValue('W3EERedux_SignShatter', varName);
	if( s == "" )
		return fallback;

	return s;
}

function SSHT_Int( varName : name, fallback : int ) : int
{
	var s : string;

	s = SSHT_Str(varName, "");
	if( s == "" )
		return fallback;

	return StringToInt(s);
}

function SSHT_Float( varName : name, fallback : float ) : float
{
	var s : string;

	s = SSHT_Str(varName, "");
	if( s == "" )
		return fallback;

	return StringToFloat(s);
}

function SSHT_Bool( varName : name, fallback : bool ) : bool
{
	var s : string;

	s = SSHT_Str(varName, "");
	if( s == "" )
		return fallback;

	if( s == "true" || s == "1" )
		return true;

	return false;
}


// ---------------------------------------------------------------------------
// Recognising a sign
//
// By the projectile that caused the damage, NOT by GetSignType(): that one is
// blind to the heavy (alternate) cast, causer is not.
// ---------------------------------------------------------------------------

function SSHT_IsAard( action : W3DamageAction ) : bool
{
	if( (W3AardProjectile)action.causer )
		return true;

	return false;
}

function SSHT_IsIgni( action : W3DamageAction ) : bool
{
	if( (W3IgniProjectile)action.causer )
		return true;

	return false;
}

// Burning is the fire Igni leaves behind, so it belongs here rather than in a
// mod of its own. Every damage-over-time tick carries the EFFECT as its causer
// (effectManager.ws:987 passes it straight into Initialize), which is the same
// shape as the two projectile checks above. The attacker stays whoever set the
// target alight, so the player-attacker gate further down still does its job.
function SSHT_IsBurning( action : W3DamageAction ) : bool
{
	if( (W3Effect_Burning)action.causer )
		return true;

	return false;
}


// ---------------------------------------------------------------------------
// Who may be torn apart
// ---------------------------------------------------------------------------

// Hard bans only. No requirement for explosion wound models, so a plain cut is
// an acceptable fallback for creatures that lack them.
function SSHT_CanBeTornApart( npc : CNewNPC ) : bool
{
	if( !npc )
		return false;

	if( npc.IsHuge() )
		return false;

	if( npc.WillBeUnconscious() )
		return false;

	if( npc.HasTag('IsBoss') || npc.HasTag('MonsterHuntTarget') || npc.HasTag('olgierd_gpl') || npc.HasTag('PlayerWolfCompanion') )
		return false;

	if( npc.HasAbility('Boss') || npc.HasAbility('SkillBoss') || npc.HasAbility('DisableDismemberment') )
		return false;

	if( npc.HasTag('DisableDismemberment') )
		return false;

	return true;
}

// Same bans PLUS a check that the creature actually owns the wound models the
// explosion needs. Used by path A, which has no fallback to fall back on.
function SSHT_CanShatter( npc : CNewNPC ) : bool
{
	var dismComp : CDismembermentComponent;
	var wounds   : array<name>;

	if( !SSHT_CanBeTornApart(npc) )
		return false;

	if( npc.HasAbility('InstantKillImmune') )
		return false;

	dismComp = (CDismembermentComponent)npc.GetComponentByClassName('CDismembermentComponent');
	if( !dismComp )
		return false;

	dismComp.GetWoundsNames( wounds, WTF_Explosion );

	return wounds.Size() > 0;
}

// Does the sign that just killed this NPC want to tear it apart? Shared by the
// two places that have to agree on the answer.
function SSHT_SignKillWants( action : W3DamageAction, npc : CNewNPC ) : bool
{
	var playerAtt : W3PlayerWitcher;

	if( !npc )
		return false;

	// HARD BANS FIRST, before anything below can say yes.
	//
	// The forced-explosion flag below is NOT ours alone: W3EE raises it too, for
	// the Obliteration runeword, the Purgation glyphword, Winter Blade and Phantom
	// Weapon. Checking the flag before the bans would let any of those tear apart
	// a boss, a monster-hunt target, a quest-protected NPC, or someone whose death
	// is meant to be an unconscious knockout - a broken quest, not a gore effect.
	if( !SSHT_CanBeTornApart(npc) )
		return false;

	// our own spawned shatter action, recognised by the forced flag
	if( action.HasForceExplosionDismemberment() )
		return true;

	playerAtt = (W3PlayerWitcher)action.attacker;
	if( !playerAtt )
		return false;

	if( SSHT_IsAard(action) )
	{
		if( !SSHT_Bool('KillShatter', true) )
			return false;
	}
	else if( SSHT_IsIgni(action) )
	{
		if( !SSHT_Bool('IgniKill', true) )
			return false;
	}
	else if( SSHT_IsBurning(action) )
	{
		if( !SSHT_Bool('BurnKill', true) )
			return false;
	}
	else
	{
		return false;
	}

	if( npc.IsHuman() && !SSHT_Bool('KillShatterHumans', true) )
		return false;

	return true;
}


// ---------------------------------------------------------------------------
// Optional slow motion
//
// Reuses the engine's existing InstantKill timescale source, so removal is done
// by the stock RemoveInstantKillSloMo timer - no @addMethod needed.
// ---------------------------------------------------------------------------

function SSHT_TrySloMo()
{
	var chance   : int;
	var scale    : float;
	var duration : float;

	chance = SSHT_Int('SloMoChance', 35);

	if( chance <= 0 || RandRange(100) >= chance )
	{
		theGame.RemoveTimeScale( theGame.GetTimescaleSource( ETS_InstantKill ) );
		return;
	}

	scale = SSHT_Float('SloMoScale', 0.30);
	if( scale < 0.05f || scale > 1.f )
		scale = 0.30;

	duration = SSHT_Float('SloMoTime', 0.50);
	if( duration <= 0.f || duration > 3.f )
		duration = 0.50;

	theGame.SetTimeScale( scale, theGame.GetTimescaleSource( ETS_InstantKill ), 32, true, true );
	thePlayer.AddTimer( 'RemoveInstantKillSloMo', duration * scale );
}


// ---------------------------------------------------------------------------
// PATH A - the follow-up hit on an already broken poise
// ---------------------------------------------------------------------------

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

	allowed = false;
	if( SSHT_IsAard(action) && SSHT_Bool('HumanPoise', true) )
		allowed = true;
	else if( SSHT_IsIgni(action) && SSHT_Bool('IgniPoise', true) )
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
	hpLimit = ((float)SSHT_Int('HumanHP', 100)) / 100.f;
	hpNow   = npcVictim.GetHealthPercents();
	if( hpNow < 0.f || hpNow >= hpLimit )
		return;

	if( !SSHT_CanShatter(npcVictim) )
		return;

	// chance grows with MISSING health: 70% left -> 30%, 30% left -> 70%
	chance = RoundMath( (1.f - hpNow) * 100.f * ((float)SSHT_Int('ShatterScale', 100)) / 100.f );
	if( chance <= 0 || RandRange(100) >= chance )
		return;

	// separate damage action, exactly like the shipped Glyphword 3 code
	shatterAction = new W3DamageAction in theGame.damageMgr;
	shatterAction.Initialize( playerAtt, npcVictim, this, "SignShatter", EHRT_None, CPS_Undefined, false, false, true, false );
	shatterAction.SetInstantKill();
	shatterAction.SetForceExplosionDismemberment();
	shatterAction.SetIgnoreInstantKillCooldown();
	theGame.damageMgr.ProcessAction( shatterAction );
	delete shatterAction;

	SSHT_TrySloMo();
}


// ---------------------------------------------------------------------------
// PATH B - the sign landed the killing blow
// ---------------------------------------------------------------------------

@wrapMethod(W3EECombatHandler) function GetSignSkillDismember( action : W3DamageAction ) : bool
{
	var npcVictim : CNewNPC;

	if( wrappedMethod(action) )
		return true;

	npcVictim = (CNewNPC)action.victim;
	if( !SSHT_SignKillWants( action, npcVictim ) )
		return false;

	SSHT_TrySloMo();
	return true;
}


// ---------------------------------------------------------------------------
// Making the refusal stick
//
// W3EE refuses dismemberment for several reasons that ALL sit above the sign
// branch: heavy armour, battle mace in hand, wooden weapon, arrows. From outside
// there is no way to tell which one fired, so we do not guess - if the original
// said no and a sign is responsible, we say yes.
//
// A wrapper can only turn false into true, so this is never worse than stock.
// ---------------------------------------------------------------------------

@wrapMethod(W3DamageManagerProcessor) function CanDismember( wasFrozen : bool, out dismemberExplosion : bool, out weaponName : name ) : bool
{
	var npcVictim : CNewNPC;
	var result    : bool;

	result = wrappedMethod( wasFrozen, dismemberExplosion, weaponName );
	npcVictim = (CNewNPC)actorVictim;

	if( result )
	{
		// A sign can ONLY be dismembered in explosion mode: the other path in
		// ProcessDismemberment needs an attack action, and a sign has none.
		// A burning tick has none either, for the same reason.
		if( SSHT_IsAard(action) || SSHT_IsIgni(action) || SSHT_IsBurning(action) || action.HasForceExplosionDismemberment() )
			dismemberExplosion = true;

		return true;
	}

	if( !SSHT_SignKillWants( action, npcVictim ) )
		return false;

	dismemberExplosion = true;
	return true;
}
