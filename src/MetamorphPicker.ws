// MetamorphPicker.ws  --  Metamorphosis Picker, an add-on for W3EE Redux
// Metamorphosis (EPMT_Mutation12) switches ON every researched mutation at once.
// This module lets the player switch single mutations OFF, right inside the
// in-game mutation screen. No copied files, no swf, no new localization keys.
//
// WHAT IS STORED
//   One game fact, "ASH_MetaOff", holding a bitmask of the mutations that are
//   switched OFF under Metamorphosis. Bit (N-1) belongs to EPMT_MutationN, N=1..11.
//   Highest possible value is 2047, safely inside the ~16 bit signed range a single
//   fact entry holds (proof: the sign fixup in W3EE - Big Facts.ws:24-29).
//   Mask 0 means "nothing switched off" == stock W3EE behaviour. An old save, a new
//   game and a player who never touches this all behave exactly as before, so no
//   migration flag and no first-run detection are needed.
//
// WHY A FACT AND NOT A saved var
//   Facts live inside the save file and are proven to survive save/load (mapMenu.ws
//   keeps its filter that way, W3EE - States.ws keeps fireplace coordinates that
//   way). They also add NOTHING to the save schema, so removing this module later
//   cannot damage a save. A saved var added through @addField has no such proof.
//
// THREE WRAPPERS, NOTHING ELSE
//   W3PlayerWitcher.IsMutationActive             - the gameplay filter
//   W3PlayerWitcher.SetEquippedMutation          - turns a menu click into a toggle
//   CR4CharacterMenu.CreateMutationFlashDataObj  - paints the [+] / [-] marks
//
// NOTE ON THE FACT NAME
//   The fact is still called "ASH_MetaOff" for the sake of saves made while this
//   was part of the AardShatter bundle. Renaming it would silently reset every
//   choice already made, which is worse than an unfashionable name.


// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

function MMPK_Str( varName : name, fallback : string ) : string
{
	var s : string;

	s = theGame.GetInGameConfigWrapper().GetVarValue('W3EERedux_MetamorphPicker', varName);
	if( s == "" )
		return fallback;

	return s;
}

function MMPK_Bool( varName : name, fallback : bool ) : bool
{
	var s : string;

	s = MMPK_Str(varName, "");
	if( s == "" )
		return fallback;

	if( s == "true" || s == "1" )
		return true;

	return false;
}


// ---------------------------------------------------------------------------
// Storage
// ---------------------------------------------------------------------------

function MMPK_MetaMaskGet() : int
{
	return FactsQuerySum("ASH_MetaOff");
}

function MMPK_MetaMaskSet( mask : int )
{
	if( mask == 0 )
		FactsRemove("ASH_MetaOff");
	else
		FactsSet("ASH_MetaOff", mask, -1);
}

// Bit (N-1) for EPMT_MutationN. WitcherScript has no shift operator - vanilla
// multiplies instead (actor.ws uses _shift8 / _shift16), so we do the same.
// Anything outside slots 1..11 returns 0, which reads back as "not switched off".
function MMPK_MetaBit( mutationType : EPlayerMutationType ) : int
{
	var i, idx, bit : int;

	idx = (int)mutationType;
	if( idx < (int)EPMT_Mutation1 || idx > (int)EPMT_Mutation11 )
		return 0;

	bit = 1;
	for( i = (int)EPMT_Mutation1; i < idx; i += 1 )
		bit = bit * 2;

	return bit;
}

function MMPK_MetaMaskHas( mask : int, mutationType : EPlayerMutationType ) : bool
{
	var bit : int;

	bit = MMPK_MetaBit(mutationType);
	if( bit == 0 )
		return false;

	return ( mask & bit ) != 0;
}


// ---------------------------------------------------------------------------
// Rules
// ---------------------------------------------------------------------------

// A mutation is pickable only if it is a real slot 1..11 AND already researched.
// Treating an unresearched mutation as "not participating" is what makes a
// mutation respec heal itself: PlayerAbilityManager.ws:3540 and :4347 reset the
// equipped mutation through the ability manager, bypassing our wrapper, but the
// stale bits then belong to mutations that no longer count anyway.
function MMPK_MetaIsPickable( witcher : W3PlayerWitcher, mutationType : EPlayerMutationType ) : bool
{
	var idx : int;

	idx = (int)mutationType;
	if( idx < (int)EPMT_Mutation1 || idx > (int)EPMT_Mutation11 )
		return false;

	return witcher.IsMutationResearched( mutationType );
}

// How many pickable mutations are ON right now, and how many exist at all.
function MMPK_MetaCountOn( witcher : W3PlayerWitcher, out total : int ) : int
{
	var i, mask, on : int;

	mask = MMPK_MetaMaskGet();
	total = 0;
	on = 0;

	for( i = (int)EPMT_Mutation1; i <= (int)EPMT_Mutation11; i += 1 )
	{
		if( MMPK_MetaIsPickable(witcher, i) )
		{
			total += 1;
			if( !MMPK_MetaMaskHas(mask, i) )
				on += 1;
		}
	}

	return on;
}

// Kolaris' Mutation Rework turned nearly every mutation into a live query - the
// vanilla "equip applies a buff" code is commented out all over W3EE. So this is
// insurance, not a workload. RemoveBuff on an absent buff is a no-op, and the
// toggle can only happen out of combat (characterMenu.ws:681 blocks it in combat).
function MMPK_MetaDropBuffs( witcher : W3PlayerWitcher, mutationType : EPlayerMutationType )
{
	if( mutationType == EPMT_Mutation3 )
	{
		witcher.RemoveBuff( EET_Mutation3 );
	}
	else if( mutationType == EPMT_Mutation5 )
	{
		witcher.RemoveBuff( EET_Mutation5 );
	}
	else if( mutationType == EPMT_Mutation6 )
	{
		witcher.RemoveBuff( EET_HarmonyAard );
		witcher.RemoveBuff( EET_HarmonyAxii );
		witcher.RemoveBuff( EET_HarmonyQuen );
		witcher.RemoveBuff( EET_HarmonyIgni );
		witcher.RemoveBuff( EET_HarmonyYrden );
	}
	else if( mutationType == EPMT_Mutation10 )
	{
		witcher.RemoveBuff( EET_Mutation10 );
		witcher.StopEffect( 'mutation_10' );
	}
}


// ---------------------------------------------------------------------------
// Hot path cache
//
// Deliberately NOT 'saved'. The player entity is rebuilt on every load, so the
// flag comes back false and the mask is re-read from the fact belonging to the
// save that was just loaded. modLookAroundYouGeralt builds its whole init on this
// exact behaviour (camHeadTrack_Initialized, LookAroundYouGeralt.ws:209-212).
// ---------------------------------------------------------------------------

@addField(W3PlayerWitcher)
var MMPK_metaMask : int;

@addField(W3PlayerWitcher)
var MMPK_metaMaskRead : bool;


// ---------------------------------------------------------------------------
// 1. The gameplay filter.
//
// Subtractive only: we can turn a true into a false, never the other way round.
// Note that several call sites are else-if chains (playerWitcher.ws:2887,
// signEntity.ws:176, vitalityRegen.ws:147, W3EE - Effects.ws:3621) - switching a
// mutation off there hands control to the next branch, which is the plain vanilla
// fallback. That is the intended result, but it is not "nothing happens".
// ---------------------------------------------------------------------------

@wrapMethod(W3PlayerWitcher) function IsMutationActive( mutationType : EPlayerMutationType ) : bool
{
	var res : bool;

	res = wrappedMethod( mutationType );

	if( !res )
		return false;

	if( !MMPK_metaMaskRead )
	{
		MMPK_metaMask = MMPK_MetaMaskGet();
		MMPK_metaMaskRead = true;
	}

	// Cheapest possible exit for everyone who never used the feature.
	if( MMPK_metaMask == 0 )
		return true;

	if( mutationType == EPMT_Mutation12 )
		return true;

	if( GetEquippedMutationType() != EPMT_Mutation12 )
		return true;

	return !MMPK_MetaMaskHas( MMPK_metaMask, mutationType );
}


// ---------------------------------------------------------------------------
// 2. The click.
//
// characterMenu.ws:673-695 is the only path that reaches this method with a real
// id, and its guard `currentlyEquipped != mutationId` lets every non-Metamorphosis
// tile through while Metamorphosis is worn. After we return, the menu still runs
// setMutationBonusMode(true) (a no-op, it is already true) and
// UpdateAllMutationsData(), which repaints all 13 tiles for free.
// ---------------------------------------------------------------------------

@wrapMethod(W3PlayerWitcher) function SetEquippedMutation( mutationType : EPlayerMutationType ) : bool
{
	var mask, bit : int;

	if( GetEquippedMutationType() == EPMT_Mutation12 && MMPK_Bool('Enabled', true) )
	{
		// The Master node can never be equipped (PlayerAbilityManager.ws:3879-3882
		// refuses it), so its Activate press is dead space in vanilla. Use it as
		// "switch everything back on".
		if( mutationType == EPMT_MutationMaster )
		{
			MMPK_MetaMaskSet( 0 );
			MMPK_metaMask = 0;
			MMPK_metaMaskRead = true;
			return true;
		}

		if( MMPK_MetaIsPickable( this, mutationType ) )
		{
			bit = MMPK_MetaBit( mutationType );
			mask = MMPK_MetaMaskGet();

			if( ( mask & bit ) != 0 )
			{
				mask = mask & ( ~bit );
			}
			else
			{
				mask = mask | bit;
				MMPK_MetaDropBuffs( this, mutationType );
			}

			MMPK_MetaMaskSet( mask );
			MMPK_metaMask = mask;
			MMPK_metaMaskRead = true;
			return true;
		}
	}

	return wrappedMethod( mutationType );
}


// ---------------------------------------------------------------------------
// 3. The marks.
//
// Post-processing only: one wrappedMethod call, then two string fields on the
// object it returned. Kolaris' mutagen cost math (characterMenu.ws:878-894) and
// the isEquipped flag (890-893) are left completely untouched - isEquipped on
// purpose, see the design notes: hijacking it would turn the tile's prompt into
// "Deactivate", which fires OnUnequipMutation() with no argument and would strip
// Metamorphosis itself instead of unticking the mutation.
// ---------------------------------------------------------------------------

@wrapMethod(CR4CharacterMenu) function CreateMutationFlashDataObj( curMutationId : EPlayerMutationType ) : CScriptedFlashObject
{
	var mutationData : CScriptedFlashObject;
	var witcher : W3PlayerWitcher;
	var meta : SMutation;
	var label, descr, tag : string;
	var on, total : int;

	mutationData = wrappedMethod( curMutationId );

	if( !mutationData )
		return mutationData;

	witcher = GetWitcherPlayer();
	if( !witcher )
		return mutationData;

	if( !MMPK_Bool('Enabled', true) )
		return mutationData;

	// Marks only make sense while Metamorphosis is the worn mutation.
	if( witcher.GetEquippedMutationType() != EPMT_Mutation12 )
		return mutationData;

	descr = mutationData.GetMemberFlashString( "description" );

	// The Metamorphosis node itself carries the score line.
	if( curMutationId == EPMT_Mutation12 )
	{
		on = MMPK_MetaCountOn( witcher, total );
		if( descr != "" )
			mutationData.SetMemberFlashString( "description", descr + "<br><br>[+] " + on + " / " + total );

		return mutationData;
	}

	if( !MMPK_MetaIsPickable( witcher, curMutationId ) )
		return mutationData;

	if( MMPK_MetaMaskHas( MMPK_MetaMaskGet(), curMutationId ) )
		tag = "[-] ";
	else
		tag = "[+] ";

	// Guarded writes: if the getter ever comes back empty we skip the mark rather
	// than overwrite a field with a truncated value.
	label = mutationData.GetMemberFlashString( "name" );
	if( label != "" )
		mutationData.SetMemberFlashString( "name", tag + label );

	if( descr != "" )
	{
		meta = witcher.GetMutation( EPMT_Mutation12 );
		mutationData.SetMemberFlashString( "description", descr + "<br><br>" + tag + GetLocStringByKeyExt( meta.localizationNameKey ) );
	}

	return mutationData;
}