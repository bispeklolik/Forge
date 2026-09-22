// DynRagdolls.ws  --  Dynamic Ragdolls settings, an add-on for W3EE Redux
//
// The Dynamic Ragdolls And Death Animations mod (kingslayer997, v2.59) ships
// a vanilla-based damageManagerProcessor.ws. Its gameplay blocks were hand-
// merged on top of the W3EE version into mod0000_MergedFiles (the merge is
// reproducible: D:\Apps\w3ee-tweaks\merge_ragdolls_final.py). This add-on
// holds only the SETTINGS those merged blocks read - sliders and toggles in
// the W3EE Redux Add-ons menu. No settings menu ships with the mod itself.
//
// Vars (group W3EERedux_DynRagdolls):
//   RagdollChance    0..100  free ragdoll death chance, %  (mod hardcoded 10)
//   ForceScale      50..300  ragdoll impulse strength, %   (100 = mod value)
//   MuteCorpses     toggle   stop corpse screams on sign hits
//   DropWeapons     toggle   drop weapons on non-sword deaths
//   DeadlyCounter   toggle   Mutation 3 under 25% vitality forces a finisher
//   FistsNoDismember toggle  fists and fistfights never dismember


// ---------------------------------------------------------------------------
// Settings readers. Empty value (menu not initialized yet) = mod defaults.
// ---------------------------------------------------------------------------

function DRGD_Str( varName : name, fallback : string ) : string
{
	var s : string;

	s = theGame.GetInGameConfigWrapper().GetVarValue('W3EERedux_DynRagdolls', varName);
	if( s == "" )
		return fallback;
	return s;
}

function DRGD_On( varName : name ) : bool
{
	return DRGD_Str( varName, "true" ) == "true";
}

function DRGD_Int( varName : name, fallback : int ) : int
{
	return StringToInt( DRGD_Str( varName, IntToString( fallback ) ), fallback );
}
