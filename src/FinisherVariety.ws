// FinisherVariety.ws  --  Finisher Variety, an add-on for W3EE Redux
//
// W3EE replaced the vanilla random finisher pool with a direction-based one, so
// the animation is chosen by whichever movement key is held. Standing still, that
// collapses to a single animation - the same stab in the chest, over and over.
//
// This restores the vanilla pool plus every finisher shipped with the DLCs, and
// lets the game pick at random again.


// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

function FVAR_Str( varName : name, fallback : string ) : string
{
	var s : string;

	s = theGame.GetInGameConfigWrapper().GetVarValue('W3EERedux_FinisherVariety', varName);
	if( s == "" )
		return fallback;

	return s;
}

function FVAR_Int( varName : name, fallback : int ) : int
{
	var s : string;

	s = FVAR_Str(varName, "");
	if( s == "" )
		return fallback;

	return StringToInt(s);
}

function FVAR_AddAnim( out arr : array<name>, animName : name )
{
	if( animName == '' )
		return;

	if( arr.Contains(animName) )
		return;

	arr.PushBack(animName);
}


// ---------------------------------------------------------------------------

@wrapMethod(W3EECombatHandler) function GetFinisherAnimsForDirection() : array<name>
{
	var arr        : array<name>;
	var i, size    : int;
	var mode       : int;
	var leftStance : bool;
	var syncMgr    : W3SyncAnimationManager;

	// the original may be invoked ONLY ONCE per wrapper - keep its result
	arr  = wrappedMethod();
	mode = FVAR_Int('Mode', 1);

	// mode 0 - leave W3EE's direction-based pool exactly as it is
	if( mode <= 0 )
		return arr;

	// Headtaker deliberately wants its own single animation
	if( GetWitcherPlayer() && GetWitcherPlayer().HasBuff(EET_SwordBehead) )
		return arr;

	// mode 1+ - drop W3EE's direction pool and rebuild the vanilla one,
	// so the game picks at random again instead of by movement key
	arr.Clear();

	leftStance = thePlayer.GetCombatIdleStance() <= 0.f;
	syncMgr    = theGame.GetSyncAnimManager();

	if( leftStance || mode >= 2 )
	{
		FVAR_AddAnim(arr, 'man_finisher_02_lp');
		FVAR_AddAnim(arr, 'man_finisher_04_lp');
		FVAR_AddAnim(arr, 'man_finisher_06_lp');
		FVAR_AddAnim(arr, 'man_finisher_07_lp');
		FVAR_AddAnim(arr, 'man_finisher_08_lp');

		if( syncMgr )
		{
			size = syncMgr.dlcFinishersLeftSide.Size();
			for( i = 0; i < size; i += 1 )
				FVAR_AddAnim(arr, syncMgr.dlcFinishersLeftSide[i].finisherAnimName);
		}
	}

	if( !leftStance || mode >= 2 )
	{
		FVAR_AddAnim(arr, 'man_finisher_01_rp');
		FVAR_AddAnim(arr, 'man_finisher_03_rp');
		FVAR_AddAnim(arr, 'man_finisher_05_rp');

		if( syncMgr )
		{
			size = syncMgr.dlcFinishersRightSide.Size();
			for( i = 0; i < size; i += 1 )
				FVAR_AddAnim(arr, syncMgr.dlcFinishersRightSide[i].finisherAnimName);
		}
	}

	if( arr.Size() == 0 )
		FVAR_AddAnim(arr, 'man_finisher_01_rp');

	return arr;
}
