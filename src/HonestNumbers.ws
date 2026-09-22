// HonestNumbers.ws  --  Honest Numbers, an add-on for W3EE Redux
//
// The character sheet prints figures the game does not deliver. An audit of 100
// of its rows found 49 honest and 51 lying, though the 51 collapse into far
// fewer defects because the sheet repeats itself.
//
// Most of those defects live inside the display file itself, in global functions
// that cannot be wrapped - only replaced wholesale, which would fork W3EE's UI
// logic and silently freeze it at today's version. This mod deliberately fixes
// ONLY what can be corrected through a getter, so that not one line of W3EE is
// copied or replaced.
//
// Both getters below are display-only in this build. That was verified by
// listing every caller, not assumed:
//
//   GetSingleSignSpellPower  - 5 callers, all of them CharacterStatsPopup.ws
//   GetOffenseStatsList      - 3 live callers: characterMenu.ws:3872,
//                              inventoryMenu.ws:1601, CharacterStatsPopup.ws:1292.
//                              W3EE dropped vanilla's combat call, so nothing in
//                              a fight reads it any more.
//
// Consequently neither wrapper can change combat. They change what the screen
// says about it.
//
// NOT FIXED HERE, and worth knowing: the attack-speed rows hide the battle
// mace / battleaxe bonus behind a returnOnly flag, exactly like the sign-power
// bug. It is NOT corrected, because W3EE - Combat.ws:1877 calls that same getter
// with the same flag inside a live combat calculation - correcting the getter
// would quietly change the fight.


// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

function HNUM_Str( varName : name, fallback : string ) : string
{
	var s : string;

	s = theGame.GetInGameConfigWrapper().GetVarValue('W3EERedux_HonestNumbers', varName);
	if( s == "" )
		return fallback;

	return s;
}

function HNUM_Bool( varName : name, fallback : bool ) : bool
{
	var s : string;

	s = HNUM_Str(varName, "");
	if( s == "" )
		return fallback;

	if( s == "true" || s == "1" )
		return true;

	return false;
}


// ---------------------------------------------------------------------------
// The five per-sign intensity rows
//
// The sheet asks GetSingleSignSpellPower, which returns only that sign's OWN
// gear bonus above zero, and prints it as 100 + v*100. So a character with 180%
// global intensity and no sign-specific gear sees five rows of "100%" while
// every sign actually fires at 144% - and a piece of Aard gear worth +0.15 reads
// as fifteen points when its real worth after the diminishing curve is four.
//
// Combat asks GetTotalSignSpellPower, which includes the global multiplier AND
// applies the curve. Returning that total minus one makes the sheet's own
// "100 + v*100" print the delivered figure, with no change to the display file.
// ---------------------------------------------------------------------------

@wrapMethod(W3PlayerWitcher) function GetSingleSignSpellPower( signSkill : ESkill ) : SAbilityAttributeValue
{
	var sp    : SAbilityAttributeValue;
	var total : SAbilityAttributeValue;

	sp = wrappedMethod( signSkill );

	if( !HNUM_Bool('Enabled', true) || !HNUM_Bool('SignRows', true) )
		return sp;

	total = GetTotalSignSpellPower( signSkill );

	// the row renders 100 + v*100, so hand it total-1 to make it print total
	sp.valueMultiplicative = total.valueMultiplicative - 1.f;

	return sp;
}


// ---------------------------------------------------------------------------
// Sword damage, corrected for blade wear
//
// GetOffenseStatsList reads raw weapon damage and never applies the durability
// factor that combat applies on every swing. At 50% durability the multiplier is
// 0.75 and at 0% it is 0.50, so the sheet can show exactly double what lands -
// on the very number a player uses to choose between two swords, and it drifts
// silently between visits to a grindstone.
//
// Damage per second is linear in damage, so scaling both by the same factor is
// correct without knowing how W3EE computes the rate. Critical CHANCE is a
// probability and is deliberately left alone.
// ---------------------------------------------------------------------------

@wrapMethod(W3PlayerWitcher) function GetOffenseStatsList( optional hackMode : int ) : SPlayerOffenseStats
{
	var stats : SPlayerOffenseStats;
	var item  : SItemUniqueId;
	var inv   : CInventoryComponent;
	var mult  : float;

	stats = wrappedMethod( hackMode );

	if( !HNUM_Bool('Enabled', true) || !HNUM_Bool('Durability', true) )
		return stats;

	inv = GetInventory();
	if( !inv )
		return stats;

	if( GetItemEquippedOnSlot( EES_SteelSword, item ) )
	{
		mult = theGame.params.GetDurabilityMultiplier( inv.GetItemDurabilityRatio(item), true );
		if( mult > 0.f && mult < 1.f )
		{
			stats.steelFastDmg       *= mult;
			stats.steelFastCritDmg   *= mult;
			stats.steelFastDPS       *= mult;
			stats.steelStrongDmg     *= mult;
			stats.steelStrongCritDmg *= mult;
			stats.steelStrongDPS     *= mult;
		}
	}

	if( GetItemEquippedOnSlot( EES_SilverSword, item ) )
	{
		mult = theGame.params.GetDurabilityMultiplier( inv.GetItemDurabilityRatio(item), true );
		if( mult > 0.f && mult < 1.f )
		{
			stats.silverFastDmg       *= mult;
			stats.silverFastCritDmg   *= mult;
			stats.silverFastDPS       *= mult;
			stats.silverStrongDmg     *= mult;
			stats.silverStrongCritDmg *= mult;
			stats.silverStrongDPS     *= mult;
		}
	}

	return stats;
}
