// Mutations.ws  --  Mutation Fixes, an add-on for W3EE Redux
//
// Two different problems live here, and they are kept strictly apart.
//
// A. THE INSECTOID EXCHANGE RATE IS A BUG.
//    The tooltip hardcodes "0.25 seconds worth of drain per point" twice
//    (playerWitcher.ws:5105-5106) while the code delivers 0.1
//    (W3EE - Combat.ws:5311, W3EE - Effects.ws:490, against the -0.2/second base
//    at toxicity.ws:609). The multiplier cancels, so the error is a constant
//    2.5x at every skill level. Default here is 0.25 - the number the game
//    already claims.
//
// B. THE SPECTER INTENSITY NUMBER IS NOT A BUG.
//    Mutation 1 adds +0.5 to sign intensity at playerWitcher.ws:10800-10801 and
//    the compression on line 10826 runs AFTER it:
//        sp = 1 + (sp - 1) * MinF(1, 1/sp)
//    That compression is a documented house rule - the author states publicly
//    that "stacking sign intensity is less effective" and that intensity has
//    "diminished scaling like attack speed and efficiencies". Every source is
//    compressed, not just the mutation. The mechanic is intended.
//
//    What it produces, though, is a tooltip promising +50% while a built sign
//    character receives about +7%, and a character sheet that prints the
//    uncompressed 50 because the display path skips the curve. The player pays a
//    real, uncompressed -50% melee penalty for it.
//
//    So the DEFAULT here changes nothing: it only stops the tooltip lying.
//    The bypass slider is opt-in, because turning it up is rebalancing somebody
//    else's mod, and that should be the player's decision rather than ours.
//
//    The argument for offering it at all: compression exists to stop bonuses
//    being STACKED. A mutation cannot be stacked - there is one slot. Applying
//    anti-stacking math to a source that is unstackable by construction is the
//    rule firing outside its purpose.
//
// Nothing here is written to the save. No W3EE file is copied or edited.


// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

function MUTF_Str( varName : name, fallback : string ) : string
{
	var s : string;

	s = theGame.GetInGameConfigWrapper().GetVarValue('W3EERedux_Mutations', varName);
	if( s == "" )
		return fallback;

	return s;
}

function MUTF_Int( varName : name, fallback : int ) : int
{
	var s : string;

	s = MUTF_Str(varName, "");
	if( s == "" )
		return fallback;

	return StringToInt(s);
}

function MUTF_Float( varName : name, fallback : float ) : float
{
	var s : string;

	s = MUTF_Str(varName, "");
	if( s == "" )
		return fallback;

	return StringToFloat(s);
}

function MUTF_Bool( varName : name, fallback : bool ) : bool
{
	var s : string;

	s = MUTF_Str(varName, "");
	if( s == "" )
		return fallback;

	if( s == "true" || s == "1" )
		return true;

	return false;
}


// ---------------------------------------------------------------------------
// A. Insectoid - the Adrenaline bar sets how fast toxins are purged
//
// WHAT IT WAS
//   The mutation froze the passive toxicity drain outright and paid it back in
//   lumps: one lump per point of Stamina spent, one per point of Adrenaline
//   gained (toxicity.ws:253, abilityManager.ws:439, W3EE - Effects.ws:486).
//   Two systems, and the Adrenaline half was close to dead weight:
//     * Adrenaline is never granted for Signs, crossbow or bombs - the gain
//       path returns early for anything that is not melee;
//     * one light attack is worth 1 point of Adrenaline against 10 points of
//       Stamina, so even when it fired it was an order of magnitude thinner;
//     * under the Necrophage mutation (EPMT_Mutation3), which is the one people
//       pair with this through Metamorphosis, the decay timer is switched off
//       and being hit calls RemoveAdrenaline and returns BEFORE the hook - so
//       the fattest source of all (5 points) pays nothing and the bar simply
//       pins and stops moving. "It fills once per fight and that is that."
//
// WHAT IT IS NOW
//   One mechanic instead of two. The Adrenaline bar is no longer a source of
//   one-off payments - it is a dial on the drain rate itself:
//
//       purge speed = normal speed x ( floor + (top - floor) x bar% )
//
//   An empty bar is slower than an ordinary witcher, a full bar is faster. The
//   break-even point at the defaults below sits at a fifth of the bar, so any
//   real fight crosses it, and an empty bar means "slowly", never "never" -
//   being stuck at full toxicity with nothing to do about it was the original
//   complaint and the floor exists to make that impossible.
//
//   A state, not an event: currentAdrenaline is the drawn value and chases the
//   pool at +6/-10 a second, so the multiplier already moves smoothly.
//
// NOTE, NOT A BUG
//   drainVal also feeds the toxicity fever: at 100% toxicity the damage taken
//   is proportional to the net figure, so a limp bar burns as well as failing
//   to purge. That is the cost of the trade and it is deliberate.
// ---------------------------------------------------------------------------

// The bar as the player sees it, 0.0 .. 1.0 .
//
// GetValue() is the wrong getter: it divides by a hard 100 rather than by the
// maximum, so with the Wolf set (cap 150) it returns up to 1.5. The pair the
// HUD puts into the bar is GetDisplayCount()/GetMaxDisplayCount(). Both are
// int, so both casts are mandatory - integer division would pin this at zero.
//
// Out of combat there is no object at all: OnCombatFinished clears the cached
// pointer at once (playerWitcher.ws:3850) and a timer removes the buff eight
// seconds later, and before the first fight after a load there was never one.
// Calling a method on that NULL is a script error that kills the whole
// function, so both lookups are guarded - W3EE guards them the same way in the
// character sheet (CharacterStatsPopup.ws:672).
function MUTF_InsAdrPerc() : float
{
	var adr : W3Effect_CombatAdrenaline;
	var cap : int;

	adr = GetWitcherPlayer().GetAdrenalineEffect();
	if( !adr )
		adr = (W3Effect_CombatAdrenaline)thePlayer.GetBuff( EET_CombatAdr );

	if( !adr )
		return 0.f;

	cap = adr.GetMaxDisplayCount();
	if( cap <= 0 )
		return 0.f;

	return ClampF( ((float)adr.GetDisplayCount()) / ((float)cap), 0.f, 1.f );
}

// Both ends of the dial, as multiples of the normal drain rate. Stored in
// hundredths so the sliders stay plain integers.
function MUTF_InsFloor() : float
{
	return ((float)Clamp( MUTF_Int('AdrFloor', 50), 0, 200 )) / 100.f;
}

function MUTF_InsTop() : float
{
	return ((float)Clamp( MUTF_Int('AdrTop', 300), 0, 500 )) / 100.f;
}

// What the stock drain gets multiplied by.
//
//   1.0        - the mutation is not in play, or we are out of combat, or
//                meditating: leave W3EE's own number alone;
//   0.0        - the mod is switched off in the menu: reproduce the stock
//                freeze exactly, because the patch removed it from W3EE itself
//                and without this the mutation would simply do nothing;
//   floor..top - live: the Adrenaline bar sets the speed.
function MUTF_InsDrainFactor() : float
{
	var w : W3PlayerWitcher;
	var lo, hi : float;

	w = GetWitcherPlayer();
	if( !w || !w.IsMutationActive( EPMT_Mutation5 ) )
		return 1.f;

	if( w.GetCurrentStateName() == 'W3EEMeditation' )
		return 1.f;

	if( !MUTF_Bool('Enabled', true) )
		return 0.f;

	if( MUTF_Bool('CombatOnly', true) && !w.IsInCombat() )
		return 1.f;

	lo = MUTF_InsFloor();
	hi = MUTF_InsTop();
	if( hi < lo )
		hi = lo;

	return lo + ( hi - lo ) * MUTF_InsAdrPerc();
}

// The one hook. GetToxicityDrain() is public and has exactly four callers: the
// per-second drain in toxicity.ws:251, the character sheet twice
// (CharacterStatsPopup.ws:896/904 - which now shows the live figure, a bonus),
// and the two old lump payments, which are switched off just below.
@wrapMethod(W3Effect_Toxicity) function GetToxicityDrain() : float
{
	return wrappedMethod() * MUTF_InsDrainFactor();
}


// The two old lump payments, switched off.
//
// They are not merely redundant now - they read the same getter we just
// wrapped, so leaving them on would apply the Adrenaline percentage a second
// time on top of itself. With the mod off they fall through to stock.

@wrapMethod(W3EECombatHandler) function Mutation5DrainToxFromStamina( value : float )
{
	if( MUTF_Bool('Enabled', true) )
		return;

	wrappedMethod( value );
}

@wrapMethod(W3Effect_CombatAdrenaline) function Mutation5DrainToxFromAdrenaline( value : float )
{
	if( MUTF_Bool('Enabled', true) )
		return;

	wrappedMethod( value );
}


// Optional: the vanilla damage reduction, put back.
//
// In vanilla this mutation also softened repeated hits - the first opened a
// window, every hit inside it dealt reduced vitality damage. W3EE commented the
// whole block out (playerWitcher.ws:2943-2957), which is why the mutation grants
// no combat stat at all. Off by default: switching it on is a balance change.
//
// The percentage is a slider rather than the vanilla ability attribute because
// that attribute lives inside a packed bundle and cannot be read from here.

@wrapMethod(W3PlayerWitcher) function ReduceDamage( out damageData : W3DamageAction )
{
	var windowWasOpen : bool;
	var reduction     : float;

	wrappedMethod( damageData );

	if( !MUTF_Bool('Enabled', true) || !MUTF_Bool('DmgRedOn', false) )
		return;

	if( !IsMutationActive( EPMT_Mutation5 ) )
		return;

	if( damageData.IsDoTDamage() )
		return;

	windowWasOpen = HasBuff( EET_Mutation5 );

	AddEffectDefault( EET_Mutation5, this, "", false );
	AddTimer( 'Mutation5Disable', MUTF_Float('DmgRedWindow', 5.f), false );

	if( windowWasOpen )
	{
		reduction = ((float)Clamp( MUTF_Int('DmgRedPerc', 15), 0, 90 )) / 100.f;
		damageData.processedDmg.vitalityDamage *= 1.f - reduction;
	}
}


// ---------------------------------------------------------------------------
// B. Specter - sign intensity
//
// The compression, verbatim from playerWitcher.ws:10826:
//     sp = 1 + (sp - 1) * MinF(1, 1/sp)
// which is the identity below 1 and 2 - 1/sp above it. Both directions are
// needed: forward to re-compress, backward to recover what the value was before
// the curve touched it.
// ---------------------------------------------------------------------------

function MUTF_Compress( v : float ) : float
{
	if( v <= 1.f )
		return v;

	return 2.f - 1.f / v;
}

function MUTF_Uncompress( v : float ) : float
{
	if( v <= 1.f )
		return v;

	// the curve approaches 2 asymptotically and never reaches it
	if( v >= 1.999f )
		return 1000.f;

	return 1.f / ( 2.f - v );
}

// How much of the mutation's bonus escapes the curve, 0.0 .. 1.0 .
function MUTF_SignBypass() : float
{
	if( !MUTF_Bool('Enabled', true) )
		return 0.f;

	return ((float)Clamp( MUTF_Int('SignBypass', 0), 0, 100 )) / 100.f;
}

// What the player would have without the mutation, given the compressed value
// they have with it. Used by both the bypass and the honest tooltip.
function MUTF_WithoutSpecter( compressed : float ) : float
{
	var raw : float;

	raw = MUTF_Uncompress( compressed ) - 0.5f;
	if( raw < 0.f )
		raw = 0.f;

	return MUTF_Compress( raw );
}

// Set while the tooltip is measuring, so the bypass below stands aside and the
// measurement always starts from the stock value. Without it the number would
// depend on whether the bypass slider happens to be up.
@addField(W3PlayerWitcher)
public var MUTF_descMode : bool;

@wrapMethod(W3PlayerWitcher) function GetTotalSignSpellPower( signSkill : ESkill ) : SAbilityAttributeValue
{
	var sp        : SAbilityAttributeValue;
	var bypass    : float;
	var without   : float;
	var fullValue : float;

	sp = wrappedMethod( signSkill );

	if( MUTF_descMode )
		return sp;

	bypass = MUTF_SignBypass();
	if( bypass <= 0.f )
		return sp;

	if( !IsMutationActive( EPMT_Mutation1 ) )
		return sp;

	if( sp.valueMultiplicative <= 0.f )
		return sp;

	// At full bypass the promised "+50%" becomes 50% of the intensity actually
	// delivered, rather than +0.5 poured in upstream of the curve and mostly
	// eaten by it.
	without   = MUTF_WithoutSpecter( sp.valueMultiplicative );
	fullValue = without * 1.5f;

	if( fullValue > sp.valueMultiplicative )
		sp.valueMultiplicative = sp.valueMultiplicative + bypass * ( fullValue - sp.valueMultiplicative );

	return sp;
}


// ---------------------------------------------------------------------------
// Honest descriptions
//
// Same technique as everywhere in this set: the game builds these strings in
// code and pushes fixed numbers into them, so a wrapper rebuilds the affected
// ones with numbers computed live.
// ---------------------------------------------------------------------------

@wrapMethod(W3PlayerWitcher) function GetMutationLocalizedDescription( mutationType : EPlayerMutationType ) : string
{
	var pam      : W3PlayerAbilityManager;
	var params   : array<string>;
	var locKey   : name;
	var rate     : string;
	var sp       : SAbilityAttributeValue;
	var raw, without, withIt, bypass, delivered : float;

	if( MUTF_Bool('Enabled', true) && MUTF_Bool('FixDesc', true) )
	{
		pam = (W3PlayerAbilityManager)abilityManager;
		if( pam )
		{
			locKey = pam.GetMutationDescriptionLocalizationKey( mutationType );

			if( mutationType == EPMT_Mutation5 && locKey != '' )
			{
				rate = FloatToStringPrec( MUTF_InsFloor() * 100.f, 0 );
				params.PushBack( rate );
				rate = FloatToStringPrec( MUTF_InsTop() * 100.f, 0 );
				params.PushBack( rate );
				return GetLocStringByKeyExtWithParams( NameToString(locKey),,,params );
			}

			// Specter: three numbers. The sign-cost halving is literally true and
			// the melee penalty is applied raw, so only the middle one is rebuilt.
			// It is computed for Aard, the intensity of every sign being its own
			// figure once each sign's own bonuses are added.
			if( mutationType == EPMT_Mutation1 && locKey != '' )
			{
				// Measure from the STOCK value, with the bypass standing aside.
				MUTF_descMode = true;
				sp = GetTotalSignSpellPower( S_Magic_s01 );
				MUTF_descMode = false;

				// Reduce to the base WITHOUT the mutation. Subtract its +0.5 only
				// if it is actually switched on - otherwise there is nothing there
				// to subtract, and subtracting anyway lands further down the curve
				// where it is steeper, which is what made the tooltip read roughly
				// double while the mutation was off.
				raw = MUTF_Uncompress( sp.valueMultiplicative );
				if( IsMutationActive( EPMT_Mutation1 ) )
					raw = raw - 0.5f;
				if( raw < 0.f )
					raw = 0.f;

				without = MUTF_Compress( raw );
				withIt  = MUTF_Compress( raw + 0.5f );

				// The bypass moves the delivered value toward a true +50%, so the
				// tooltip has to move with it.
				bypass = MUTF_SignBypass();
				if( bypass > 0.f && without * 1.5f > withIt )
					withIt = withIt + bypass * ( without * 1.5f - withIt );

				if( without > 0.f )
				{
					delivered = ( withIt / without - 1.f ) * 100.f;

					params.PushBack( "50" );
					params.PushBack( FloatToStringPrec( delivered, 1 ) );
					params.PushBack( "50" );
					return GetLocStringByKeyExtWithParams( NameToString(locKey),,,params );
				}
			}
		}
	}

	return wrappedMethod( mutationType );
}


// ---------------------------------------------------------------------------
// The character sheet's "Sign Intensity" line
//
// GetTotalSpellPower applies the compression only when displayOnly is FALSE
// (playerWitcher.ws:10641). The character sheet calls it with TRUE
// (CharacterStatsPopup.ws:459), so the number on screen is the raw total from
// before the curve - 180% on screen is 144% in combat.
//
// That one call is the ONLY live caller of this function in the whole compile
// set; the other two are commented out. So correcting it here cannot touch
// combat, only the number the player reads.
// ---------------------------------------------------------------------------

@wrapMethod(W3PlayerWitcher) function GetTotalSpellPower( optional displayOnly : bool ) : SAbilityAttributeValue
{
	var sp      : SAbilityAttributeValue;
	var bypass  : float;
	var without : float;

	sp = wrappedMethod( displayOnly );

	if( !displayOnly )
		return sp;

	if( !MUTF_Bool('Enabled', true) || !MUTF_Bool('SheetHonest', true) )
		return sp;

	without = sp.valueMultiplicative;
	sp.valueMultiplicative = MUTF_Compress( sp.valueMultiplicative );

	// If the player raised the bypass, combat delivers more than the plain
	// curve would, and the sheet has to say so too.
	bypass = MUTF_SignBypass();
	if( bypass > 0.f && IsMutationActive( EPMT_Mutation1 ) )
	{
		without = MUTF_Compress( MaxF( 0.f, without - 0.5f ) );
		if( without * 1.5f > sp.valueMultiplicative )
			sp.valueMultiplicative = sp.valueMultiplicative + bypass * ( without * 1.5f - sp.valueMultiplicative );
	}

	return sp;
}
