// FinisherFix.ws  --  Finisher Fix, a bug fix for W3EE Redux
//
// THE BUG
//   W3EE raises an internal flag, getShouldIgniExplode, when an Igni hit should
//   make the corpse burst. It never lowers it again. The Purgation glyphword sets
//   Igni alight on every hit, so a single Purgation-runed sword leaves the flag
//   raised for good - and from then on EVERY finisher in the game is skipped,
//   because the finisher branch believes an Igni explosion is pending. The only
//   cure in stock W3EE is restarting the game.
//
// THE FIX
//   Lower the flag on any hit that is not an Igni hit. W3EE raises it again by
//   itself whenever it actually needs it, so nothing is lost.
//
// No settings, nothing to configure: a bug fix is either installed or it is not.


@wrapMethod(W3EECombatHandler) function DealPoiseDamage( actorVictim : CActor, action : W3DamageAction )
{
	var isIgni : bool;

	wrappedMethod( actorVictim, action );

	// Recognise Igni by the projectile that caused the damage, NOT by
	// GetSignType(): that one is blind to the heavy (alternate) cast.
	// The cast goes through a local first - '!' in front of a cast does not parse.
	isIgni = false;
	if( (W3IgniProjectile)action.causer )
		isIgni = true;

	if( !isIgni )
		getShouldIgniExplode = false;
}
