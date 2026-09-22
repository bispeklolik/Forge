// DismemberAnyone.ws  --  Dismember Anyone, an add-on for W3EE Redux
//
// W3EE refuses dismemberment for several reasons: heavy armour, a battle mace in
// hand, a wooden weapon, arrows. Nilfgaardian soldiers in particular simply never
// come apart. From outside there is no way to tell which check fired, so this mod
// does not try to guess - if the original said no and the victim is an ordinary
// human, it says yes.
//
// A wrapper can only turn false into true, so the result is never worse than
// stock behaviour. Huge enemies, bosses and quest-protected NPCs stay protected.


// ---------------------------------------------------------------------------
// Requirement marker
//
// Unlike the other add-ons in this set, nothing in the logic below names a W3EE
// class - it wraps a vanilla one. Without this marker the mod would compile
// happily on a vanilla install and then misbehave quietly: the armour refusal it
// exists to override is a W3EE addition that vanilla does not have, and its
// settings page hangs off W3EE's own menu node, so it would have no parent to
// attach to and no way to be configured.
//
// Naming a W3EE-only class here turns that into a loud compile error naming this
// file, which is the whole point of building on script extensions.
// ---------------------------------------------------------------------------

function DSMA_RequiresW3EE()
{
	var handler : W3EECombatHandler;

	handler = NULL;
}


// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

function DSMA_Str( varName : name, fallback : string ) : string
{
	var s : string;

	s = theGame.GetInGameConfigWrapper().GetVarValue('W3EERedux_DismemberAnyone', varName);
	if( s == "" )
		return fallback;

	return s;
}

function DSMA_Int( varName : name, fallback : int ) : int
{
	var s : string;

	s = DSMA_Str(varName, "");
	if( s == "" )
		return fallback;

	return StringToInt(s);
}

function DSMA_Bool( varName : name, fallback : bool ) : bool
{
	var s : string;

	s = DSMA_Str(varName, "");
	if( s == "" )
		return fallback;

	if( s == "true" || s == "1" )
		return true;

	return false;
}


// ---------------------------------------------------------------------------
// Gates
// ---------------------------------------------------------------------------

function DSMA_CanBeTornApart( npc : CNewNPC ) : bool
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

// A sign has no attack action, so the weapon path in ProcessDismemberment cannot
// serve it - explosion mode has to be forced or the body falls down intact.
function DSMA_IsSign( action : W3DamageAction ) : bool
{
	if( (W3AardProjectile)action.causer )
		return true;

	if( (W3IgniProjectile)action.causer )
		return true;

	return false;
}


// ---------------------------------------------------------------------------

@wrapMethod(W3DamageManagerProcessor) function CanDismember( wasFrozen : bool, out dismemberExplosion : bool, out weaponName : name ) : bool
{
	var npcVictim : CNewNPC;
	var result    : bool;

	result = wrappedMethod( wasFrozen, dismemberExplosion, weaponName );

	if( result )
		return true;

	if( !DSMA_Bool('ArmorDism', true) )
		return false;

	npcVictim = (CNewNPC)actorVictim;
	if( !npcVictim )
		return false;

	// only humans - monsters keep W3EE's own rules
	if( !npcVictim.IsHuman() )
		return false;

	// hard bans stay hard: huge, bosses, quest-protected, going unconscious
	if( !DSMA_CanBeTornApart(npcVictim) )
		return false;

	if( RandRange(100) >= DSMA_Int('ArmorChance', 100) )
		return false;

	if( DSMA_IsSign(action) || action.HasForceExplosionDismemberment() )
		dismemberExplosion = true;

	return true;
}
