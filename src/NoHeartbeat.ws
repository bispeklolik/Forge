// NoHeartbeat.ws  --  No Heartbeat, an add-on for W3EE Redux
//
// W3EE starts a looping heartbeat as soon as your stamina drops below half, and
// speeds it up the more exhausted you are. Vanilla has no such loop at all - the
// heartloop sound bank is referenced nowhere outside W3EE - so this is purely a
// W3EE addition, and this add-on silences it.
//
// HOW IT WORKS
//   CR4HudModuleWolfHead.UpdateStamina starts the loop only while its private
//   flag isStaminaSoundPlaying is still false:
//
//       if( !isStaminaSoundPlaying && stamina <= max*0.5 && !IsCiri() )
//       {
//           isStaminaSoundPlaying = true;
//           load heartloop.bnk; play_heartloop;
//       }
//
//   So we set that flag to true BEFORE the original runs. The start branch then
//   never fires and the sound is never requested in the first place. That is why
//   this does not simply stop the loop after the fact: starting and immediately
//   cutting a looping sound clicks, and would do so on every stamina tick.
//
//   The other branch of the original merely pushes a rate parameter at a sound
//   that is not running, which does nothing, and on recovery above half stamina
//   it clears the flag and sends stop_heartloop - also a no-op. Nothing else in
//   the game reads this flag: all five of its mentions live inside this one
//   function.


// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

function NHBT_Str( varName : name, fallback : string ) : string
{
	var s : string;

	s = theGame.GetInGameConfigWrapper().GetVarValue('W3EERedux_NoHeartbeat', varName);
	if( s == "" )
		return fallback;

	return s;
}

function NHBT_Bool( varName : name, fallback : bool ) : bool
{
	var s : string;

	s = NHBT_Str(varName, "");
	if( s == "" )
		return fallback;

	if( s == "true" || s == "1" )
		return true;

	return false;
}


// ---------------------------------------------------------------------------
// Remembers that we have already sent one stop, so the option can be switched on
// in the middle of a fight without spamming the event on every stamina tick.
// Not 'saved' on purpose: the HUD module is rebuilt on load, and false is the
// correct starting value anyway.
// ---------------------------------------------------------------------------

@addField(CR4HudModuleWolfHead) var NHBT_silenced : bool;


@wrapMethod(CR4HudModuleWolfHead) function UpdateStamina() : void
{
	var mute : bool;

	mute = NHBT_Bool('Mute', true);

	if( mute )
	{
		// One-off: if the loop was already running - because the option was just
		// switched on, or the mod was added mid-game - end it once.
		if( !NHBT_silenced )
		{
			NHBT_silenced = true;

			if( isStaminaSoundPlaying )
			{
				if( !theSound.SoundIsBankLoaded("heartloop.bnk") )
					theSound.SoundLoadBank("heartloop.bnk", false);

				theSound.SoundEvent("stop_heartloop");
			}
		}

		// Claim the loop is already playing, so the original never starts it.
		isStaminaSoundPlaying = true;
	}
	else
	{
		NHBT_silenced = false;
	}

	wrappedMethod();
}
