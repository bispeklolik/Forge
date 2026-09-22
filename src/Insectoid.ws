// Insectoid.ws  --  Insectoid Mutation Fix, an add-on for W3EE Redux
//
// THE BUG
//   The Insectoid mutation (EPMT_Mutation5) stops toxicity from draining and
//   instead burns it when you spend Stamina or gain Adrenaline. Its own tooltip
//   states the exchange rate twice:
//
//       "Per point of Stamina spent: 0.25 seconds worth of drain"
//       "Per point of Adrenaline gained: 0.25 seconds worth of drain"
//
//   Those two numbers are hardcoded literals pushed into the description
//   (playerWitcher.ws:5105-5106). The code does something else:
//
//       DrainToxicity( value / -10.f * GetToxicityDrain() )
//         W3EE - Combat.ws:5311, W3EE - Effects.ws:490
//
//   With a base drain of -0.2 per second (toxicity.ws:609), one point removes
//   0.02 x multiplier of toxicity, and a second of normal drain removes
//   0.2 x multiplier. So one point is worth 0.1 seconds - not 0.25. The tooltip
//   overstates the mutation by two and a half times, and the multiplier cancels
//   out, so the error is the same at every skill level.
//
//   The result is a mutation that occupies a slot, gives no combat stat at all
//   (the vanilla damage reduction half is commented out at playerWitcher.ws:2943)
//   and returns less than its own description promises.
//
// WHAT THIS DOES
//   Makes the exchange rate a setting, defaulting to 0.25 seconds per point -
//   the number the game already claims. That alone is a 2.5x buff. The slider
//   goes further for anyone who wants it.
//
//   The description is rewritten to state the rate actually in force, so the
//   tooltip and the slider always agree.
//
//   Nothing else about the mutation is touched.


// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

function INSC_Str( varName : name, fallback : string ) : string
{
	var s : string;

	s = theGame.GetInGameConfigWrapper().GetVarValue('W3EERedux_Insectoid', varName);
	if( s == "" )
		return fallback;

	return s;
}

function INSC_Int( varName : name, fallback : int ) : int
{
	var s : string;

	s = INSC_Str(varName, "");
	if( s == "" )
		return fallback;

	return StringToInt(s);
}

function INSC_Bool( varName : name, fallback : bool ) : bool
{
	var s : string;

	s = INSC_Str(varName, "");
	if( s == "" )
		return fallback;

	if( s == "true" || s == "1" )
		return true;

	return false;
}

function INSC_Float( varName : name, fallback : float ) : float
{
	var s : string;

	s = INSC_Str(varName, "");
	if( s == "" )
		return fallback;

	return StringToFloat(s);
}

// Seconds of normal drain bought by one point, as the player set it.
// Stored in hundredths so the slider can be a plain integer.
function INSC_Seconds() : float
{
	return ((float)Clamp( INSC_Int('Rate', 25), 0, 200 )) / 100.f;
}

// What to multiply the stock argument by.
//
// Stock spends `value / 10` of a second's worth per point, so a rate of 0.1
// reproduces stock exactly and the default 0.25 is 2.5 times that. Returning
// 1.0 when the mod is off keeps the wrapper a no-op.
function INSC_Factor() : float
{
	if( !INSC_Bool('Enabled', true) )
		return 1.f;

	return INSC_Seconds() * 10.f;
}


// ---------------------------------------------------------------------------
// The two drain paths
//
// Both compute `value / -10 * drain`, so scaling the argument scales the result
// by exactly the same amount - no constant of W3EE's is duplicated here.
//
// The adrenaline one is private; private methods can be wrapped.
// ---------------------------------------------------------------------------

@wrapMethod(W3EECombatHandler) function Mutation5DrainToxFromStamina( value : float )
{
	wrappedMethod( value * INSC_Factor() );
}

@wrapMethod(W3Effect_CombatAdrenaline) function Mutation5DrainToxFromAdrenaline( value : float )
{
	wrappedMethod( value * INSC_Factor() );
}


// ---------------------------------------------------------------------------
// Optional: the vanilla damage reduction, put back
//
// In vanilla this mutation also softened repeated hits: the first hit opened a
// window, and every hit landing while that window was open dealt reduced
// vitality damage. W3EE commented the whole block out (playerWitcher.ws:2943-2957),
// which is why the mutation grants no combat stat at all.
//
// This restores the SHAPE of it, off by default, because switching it on is a
// balance change rather than a fix. The percentage is a slider rather than the
// vanilla ability attribute: that attribute lives inside a packed bundle, so it
// cannot be read from here to confirm its value.
//
// The window is re-opened by every qualifying hit and closed by W3EE's own
// Mutation5Disable timer, exactly as the commented-out original did.
// ---------------------------------------------------------------------------

@wrapMethod(W3PlayerWitcher) function ReduceDamage( out damageData : W3DamageAction )
{
	var windowWasOpen : bool;
	var reduction     : float;

	wrappedMethod( damageData );

	if( !INSC_Bool('DmgRedOn', false) )
		return;

	if( !IsMutationActive( EPMT_Mutation5 ) )
		return;

	if( damageData.IsDoTDamage() )
		return;

	windowWasOpen = HasBuff( EET_Mutation5 );

	AddEffectDefault( EET_Mutation5, this, "", false );
	AddTimer( 'Mutation5Disable', INSC_Float('DmgRedWindow', 5.f), false );

	if( windowWasOpen )
	{
		reduction = ((float)Clamp( INSC_Int('DmgRedPerc', 15), 0, 90 )) / 100.f;
		damageData.processedDmg.vitalityDamage *= 1.f - reduction;
	}
}


// ---------------------------------------------------------------------------
// Honest description
//
// The stock builder pushes the literal "0.25" twice. We push the rate that is
// actually in force, into the same localized string, so the tooltip cannot
// drift away from the slider.
// ---------------------------------------------------------------------------

@wrapMethod(W3PlayerWitcher) function GetMutationLocalizedDescription( mutationType : EPlayerMutationType ) : string
{
	var pam    : W3PlayerAbilityManager;
	var params : array<string>;
	var rate   : string;
	var locKey : name;

	if( mutationType == EPMT_Mutation5 && INSC_Bool('Enabled', true) && INSC_Bool('FixDesc', true) )
	{
		pam = (W3PlayerAbilityManager)abilityManager;
		if( pam )
		{
			locKey = pam.GetMutationDescriptionLocalizationKey( mutationType );
			if( locKey != '' )
			{
				rate = FloatToStringPrec( INSC_Seconds(), 2 );
				params.PushBack( rate );
				params.PushBack( rate );
				return GetLocStringByKeyExtWithParams( NameToString(locKey),,,params );
			}
		}
	}

	return wrappedMethod( mutationType );
}
