# -*- coding: utf-8 -*-
"""Пакует пять модов в отдельные архивы для Nexus."""
import os, sys, zipfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from spec import MODS, LOCALES

DIST = os.path.join(ROOT, "dist")
OUT  = r"C:\Users\New\Downloads\w3ee-addons"
VER  = "1.0"

TESTED = "The Witcher 3 Next-Gen (4.0x) on DX12, with W3EE Redux for Next-Gen"

COMMON_TAIL = """
REQUIREMENTS
  W3EE Redux. This is an add-on for it, not a standalone mod - without W3EE the
  game refuses to start and the error names this mod's file. That refusal is
  deliberate: the mod wraps W3EE methods through script extensions instead of
  copying its files, so a W3EE update can never be silently reverted by it.

  Tested on {tested}. NOT tested on Classic 1.32.

  Nothing else is needed beyond what W3EE itself already requires. If W3EE runs
  for you, its prerequisites - Community Patch: Shared Imports, Bootstrap &
  Utilities, Mod Limit Fix - are already in place, and this add-on adds no new
  ones of its own.

INSTALL
{install}
UNINSTALL
{uninstall}
COMPATIBILITY
  No file of W3EE, of the game, or of any other mod is replaced. Everything is
  done with @wrapMethod, and wrappers from different mods chain by design, so
  Script Merger has nothing to merge here. Safe to add or remove mid-playthrough.

  The other add-ons in this set - {others} - are
  independent. Install any combination; none of them needs another.

LANGUAGES
{languages}
CREDITS
  Built on top of W3EE Redux - every combat system this hooks into belongs to its
  authors. This add-on ships none of their files and modifies none of them; it
  only wraps their methods at load time.

  Version {ver}.
"""

INSTALL_WITH_MENU = """  1. Drop the  mods  and  bin  folders from this archive into your game folder -
     the one that already contains bin, content and mods. They merge with what
     is there; nothing is overwritten.

  2. REGISTER THE SETTINGS PAGE. Add the line  {group}.xml;  to BOTH
     dx12filelist.txt  and  dx11filelist.txt  in

         bin\\config\\r4game\\user_config_matrix\\pc\\

     Some mod managers do this automatically, some do not; Menu Filelist Updater
     (Nexus 7171) does it for every installed mod in one run. Without the line the
     mod still works, but its options page never appears and every setting stays
     at its built-in default.

     Editing by hand: those two files are UTF-16 LE. Saving them as UTF-8 breaks
     the menus of EVERY installed mod, not just this one.

  3. Settings: Options -> Mods -> W3EE -> Addons.
"""

INSTALL_PLAIN = """  Drop the  mods  folder from this archive into your game folder - the one that
  already contains bin, content and mods. That is all: this mod has no settings,
  so there is no menu file and nothing to register.
"""

UNINSTALL_WITH_MENU = """  Delete  mods\\{mod}  and remove the  {group}.xml  line from both filelists.
  Nothing of this mod is written into your save.
"""

UNINSTALL_PLAIN = """  Delete  mods\\{mod} . Nothing of this mod is written into your save.
"""

# Метаморфоза действительно пишет в сейв - общий текст тут был бы враньём.
UNINSTALL_OVERRIDE = {
    "modW3EERedux_MetamorphPicker": """  Delete  mods\\{mod}  and remove the  {group}.xml  line from both filelists.

  One game fact named ASH_MetaOff stays behind in the save - that is where your
  choice of mutations lives. It is inert the moment the mod is gone, it adds
  nothing to the save format and it harms nothing; reinstalling later picks your
  choice back up exactly where it was.
""",
}

BODIES = {

"modW3EERedux_SignShatter": """W3EE Redux - Sign Shatter {ver}
===============================

Aard and Igni tear enemies apart instead of merely knocking them down.

WHAT IT DOES

  The follow-up hit
    The NEXT sign hit on an already poise-broken human may tear it apart. Note
    the word NEXT: the hit that breaks the poise still knocks down as usual, so
    you have to commit a second cast to finish the job.

    The chance scales with MISSING health - 70% health left means a 30% chance,
    30% left means 70%. A curve slider bends that relation, and a ceiling slider
    can forbid the shatter entirely above a chosen health percentage.

    On a failed roll W3EE's normal knockdown happens instead, so nothing is lost.

  The killing blow
    Anything a sign actually kills is torn apart - guaranteed, no roll involved.
    Humans can be excluded separately if you only want it on monsters.

  Burning to death
    The fire Igni leaves behind counts too: anyone who burns to death comes
    apart the same way, not just targets hit by the sign itself. This has its
    own toggle, and it only fires when YOU set the target alight - a bandit who
    stumbles into a campfire dies the way he always did.

  What is never torn apart
    Huge enemies (griffins, trolls, golems, leshens), bosses, monster-hunt
    targets and quest-protected NPCs. Creatures that ship no gore models fall
    back to a plain cut instead of dying intact.

  Slow motion
    Optional, with its own chance, strength and duration. It reuses the engine's
    own instant-kill timescale, so it can never leave time stuck at half speed.

WHY THE ARMOUR RULE IS INCLUDED HERE
  W3EE refuses dismemberment for several reasons that all sit above the sign
  branch - heavy armour, a battle mace in hand, a wooden weapon, arrows. From
  outside there is no way to tell which check fired, so this mod overrides any
  refusal that concerns a sign. Swords are left entirely alone; if you want the
  same for swords, that is the separate Dismember Anyone add-on.
""",

"modW3EERedux_DismemberAnyone": """W3EE Redux - Dismember Anyone {ver}
===================================

Armour stops stopping your sword.

THE PROBLEM
  W3EE refuses dismemberment for a whole list of reasons: heavy armour, a battle
  mace in hand, a wooden weapon, arrows. In practice this means the enemies you
  most want to cut in half - Nilfgaardian soldiers, armoured bandits, knights -
  simply never come apart, no matter how the killing blow lands.

WHAT IT DOES
  When W3EE refuses and the victim is an ordinary human, this says yes anyway.
  It does not try to work out WHICH check fired, because from outside a mod that
  cannot be told apart - it overrides the refusal itself.

  A wrapper can only turn a "no" into a "yes", so the result is never worse than
  stock behaviour: anything W3EE already dismembered still dismembers exactly as
  before.

  A chance slider is provided if you would rather it stay a treat than become
  the default outcome.

WHAT IS STILL PROTECTED
  Huge enemies, bosses, monster-hunt targets, quest-protected NPCs and anyone
  about to fall unconscious rather than die. Monsters keep W3EE's own rules
  untouched - this only ever speaks for humans.
""",

"modW3EERedux_FinisherVariety": """W3EE Redux - Finisher Variety {ver}
===================================

Your finishers stop being the same animation over and over.

THE PROBLEM
  Vanilla picks a finisher at random from a pool. W3EE replaced that with a
  direction-based choice, so the animation follows whichever movement key you
  are holding. Standing still - which is exactly what you are usually doing when
  a finisher triggers - that pool collapses to ONE animation. The same stab in
  the chest, every single time.

WHAT IT DOES
  Restores the vanilla pool and adds every finisher shipped with the DLCs, then
  lets the game pick at random again.

  Mode 0  leave W3EE's direction-based behaviour exactly as it is
  Mode 1  vanilla behaviour - the pool matching your current stance
  Mode 2  maximum - every finisher of both stances in one pool

  Headtaker is left alone: that buff deliberately wants its own single animation,
  and overriding it would look wrong.
""",

"modW3EERedux_FinisherFix": """W3EE Redux - Finisher Fix {ver}
===============================

Your finishers stopped happening. Here is why.

THE BUG
  W3EE raises an internal flag when an Igni hit should make the corpse burst.
  It never lowers that flag again.

  The Purgation glyphword sets Igni alight on every hit, so a single
  Purgation-runed sword leaves the flag raised for good. From that moment on
  EVERY finisher in the game is skipped, because the finisher branch believes an
  Igni explosion is still pending. The only cure in stock W3EE is restarting the
  game - and the next Purgation hit brings it straight back.

THE FIX
  Lower the flag on any hit that is not an Igni hit. W3EE raises it again by
  itself whenever it genuinely needs it, so nothing is lost and no behaviour
  changes except the bug going away.

  Twenty lines, one wrapper, no settings. A bug fix is either installed or it
  is not.
""",

"modW3EERedux_NoHeartbeat": """W3EE Redux - No Heartbeat {ver}
===============================

Silences the heartbeat that plays whenever your stamina runs low.

THE SOUND
  W3EE starts a looping heartbeat the moment stamina drops below half, and speeds
  it up the more exhausted you get. In a build that spends most of a fight under
  half stamina - which is to say, most W3EE builds - it never stops.

  This is a W3EE addition, not a vanilla one: the heartloop sound bank is
  referenced nowhere in the base game's scripts.

WHAT IT DOES
  Stops the loop from ever starting. It does not start the sound and cut it off
  afterwards, which would click on every stamina tick - it prevents the request
  itself, so nothing is ever queued.

  A single toggle, on by default. Turn it off and W3EE's heartbeat comes back
  immediately; no reload needed either way.

  Everything else about the stamina HUD is untouched: the low-stamina thud, the
  recharged chime and the wolf head indicator all behave exactly as before.
""",

"modW3EERedux_HonestNumbers": """W3EE Redux - Honest Numbers {ver}
==================================

The character sheet stops overstating what your gear does.

THE PROBLEM
  An audit of 100 rows on the W3EE character sheet found 49 honest and 51 that
  print a figure the game does not deliver. Most of those live inside the display
  file, in global functions a mod cannot wrap - only replace wholesale, which
  would fork W3EE UI logic and freeze it at one version.

  This mod fixes ONLY what is reachable through a getter, so not a single line of
  W3EE is copied or replaced. Two getters, both verified display-only by listing
  every caller.

WHAT IT CORRECTS

  The five per-sign intensity rows
    The sheet asks for each Sign OWN gear bonus and prints it as if it were the
    total. With 180 percent global Sign Intensity and no sign-specific gear, all
    five rows read 100 percent while every Sign actually fires at 144. Worse for
    shopping: a piece of Aard gear worth +0.15 reads as fifteen points when its
    real worth after the diminishing curve is about four, so sign gear looks
    roughly three times more valuable than it is.

  Sword damage, corrected for blade wear
    The damage and DPS figures ignore durability, which combat applies on every
    swing. At 50 percent durability the multiplier is 0.75; at zero it is 0.50,
    so the sheet can show exactly double what lands - on the number you use to
    choose between two swords, drifting silently between grindstones.
    Critical chance is a probability and is left alone.

WHAT IT DELIBERATELY DOES NOT TOUCH
  The attack-speed rows hide the battle mace and battleaxe bonus behind a flag,
  exactly like the sign-power bug - but W3EE calls that same getter with the same
  flag inside a live combat calculation, so correcting it would quietly change
  the fight. Left alone on purpose.

  Everything else on the audit list needs the display file edited rather than
  wrapped, and is out of scope for a mod that refuses to copy other peoples files.

NO COMBAT CHANGE
  Both wrapped getters are read only by the character sheet, the inventory screen
  and the stats popup in this build - W3EE dropped vanillas combat call to the
  offense-stats getter. Nothing in a fight reads either of them.
""",

"modW3EERedux_Mutations": """W3EE Redux - Mutation Fixes {ver}
=================================

The Insectoid mutation returns what its own tooltip promises.

THE BUG
  Insectoid stops toxicity draining on its own and instead burns it when you
  spend Stamina or gain Adrenaline. Its description states the exchange rate,
  twice:

      Per point of Stamina spent:     0.25 seconds worth of drain
      Per point of Adrenaline gained: 0.25 seconds worth of drain

  Both numbers are hardcoded literals in the description builder. The code does
  something else: one point buys 0.1 seconds worth, not 0.25. The tooltip
  overstates the mutation by two and a half times, at every skill level - the
  drain multiplier cancels out of the comparison, so the error is constant.

  That leaves a mutation which occupies a slot, grants no combat stat whatsoever
  (the vanilla damage-reduction half is commented out in W3EE), and pays out
  less than it says. It is the weakest thing you can put in the slot.

WHAT THIS DOES
  Makes the exchange rate a slider, defaulting to 0.25 seconds per point - the
  figure the game already claims. That alone is a 2.5x buff and makes the tooltip
  true. Push it further if you want; stock is 0.10 for reference.

  The description is rewritten to state the rate actually in force, so the
  tooltip and the slider can never disagree.

  Nothing else about the mutation changes.


SPECTER, AND WHY ITS SLIDER DEFAULTS TO ZERO
  Mutation 1 promises "+50% Sign Intensity". It adds +0.5 upstream of W3EE's
  intensity compression, so a built sign character receives roughly +7% while the
  character sheet prints the full 50 (the display path skips the curve). The
  melee penalty it charges for that is an uncompressed -50%.

  The compression is NOT a bug. The author documents it: stacking sign intensity
  is deliberately less effective, and every source is compressed, not just this
  one. So the default here changes nothing about the mechanic - it only stops the
  tooltip lying, by computing the number the mutation actually delivers.

  The bypass slider is offered because compression exists to stop bonuses being
  STACKED, and a mutation cannot be stacked - there is one slot. At 100% the
  promised +50% becomes 50% of the intensity you actually have. It is off by
  default: turning it up is rebalancing somebody else's mod, and that is the
  player's call, not this mod's.

WHAT IS NOT FIXED
  Out of combat, toxicity still never drains - only meditation clears it. That
  is the mutation's defining drawback and it lives inside a loop no wrapper can
  reach without copying a W3EE file, which this mod does not do.
""",

"modW3EERedux_TierBonuses": """W3EE Redux - Tier-Scaled Set Bonuses {ver}
==========================================

The grandmaster half of every armour set, available from the first tier - just
weaker.

THE PROBLEM
  In W3EE the SECOND bonus of a set only switches on with a full grandmaster
  set. Until then half of what the set advertises does nothing at all, so every
  lower tier feels like filler you are only wearing on the way to the real one.

WHAT IT DOES
  Unlocks the second bonus on EVERY tier and scales it down by the average tier
  of the pieces you are wearing:

    tier 1  40%      tier 3  70%      grandmaster  100%
    tier 2  55%      tier 4  85%

  All four percentages are sliders. Grandmaster is deliberately NOT a slider: a
  complete set always behaves exactly like unmodded W3EE, so nothing you already
  built is changed.

  The ADDED part of a bonus is scaled, never the total. The Wolf adrenaline cap
  is 100 + 50 x strength, so it reads 120 at tier 1 and 150 at grandmaster - not
  60.

  Switch the mod off and the second bonus goes back to grandmaster-only, which
  is stock behaviour.

HONEST TOOLTIPS
  W3EE builds set bonus descriptions in code and pushes fixed numbers into them.
  Those numbers know nothing about any scaling, so a tooltip can promise 150
  while the game gives you 120. This rewrites the affected descriptions with the
  real numbers, optionally showing the grandmaster value in brackets - "120
  (150)" - so you can see what finishing the set would buy you.

  Only the numbers this mod actually scales are rewritten. The rest are left
  exactly as W3EE wrote them.

WHAT IS NOT SCALED
  Three parts of the second bonuses are not touched, on any tier: the Viper
  transfusion bonus, the Wolf bleed-resistance shred, and the Gryphon Yrden
  vigor regeneration and free sign. They arrive through data rather than code, so
  they come at full strength as soon as the bonus unlocks.
""",

"modW3EERedux_MetamorphPicker": """W3EE Redux - Metamorphosis Picker {ver}
=======================================

Choose which mutations Metamorphosis actually runs.

THE PROBLEM
  Metamorphosis switches ON every mutation you have researched, all at once, with
  no way to leave any of them out. Some of those you may genuinely not want -
  and there is no interface for saying so, because in W3EE that behaviour is a
  single line of code with no option attached.

WHAT IT DOES
  While Metamorphosis is equipped, pressing "Activate" on another mutation tile
  no longer equips it. Instead it TOGGLES whether that mutation takes part.

  Marks appear right in the mutation screen:
    [+]  taking part
    [-]  switched off
  Metamorphosis itself shows a counter, for example  [+] 7 / 9.

  Clicking the Master Mutation node switches everything back on. In vanilla that
  click does nothing at all, so no existing behaviour is taken away.

HOW YOUR CHOICE IS STORED
  In a game fact - the same mechanism the map filter uses. Facts live inside the
  save and add NOTHING to its schema, so removing this mod later cannot damage a
  save. What is stored is the list of mutations switched OFF, so an empty list
  means stock W3EE behaviour: old saves, new games and players who never touch
  this all behave exactly as before. No migration, no first-run prompt.

  The tile's own equipped-flag is deliberately left alone. Claiming it would make
  the interface offer "Deactivate", and that button sends a signal with no
  mutation attached - it would unequip Metamorphosis itself and leave the
  switched-off mutation impossible to bring back. Hence text marks.
""",
}


def main():
    # Чистим ТОЛЬКО свои архивы, а не папку целиком: рядом лежат
    # архивы камней от pack_release.py, и rmtree уносил их с собой.
    os.makedirs(OUT, exist_ok=True)
    for m in MODS:
        stale = os.path.join(OUT, "%s-%s.zip" % (m["mod"], VER))
        if os.path.exists(stale):
            os.remove(stale)

    langs = "  Menu labels ship in all 17 game languages:\n  " + " ".join(LOCALES) + "\n"
    print("=" * 66)
    print("  АРХИВЫ ДЛЯ NEXUS")
    print("=" * 66)

    for m in MODS:
        root = os.path.join(DIST, m["mod"])
        if not os.path.isdir(root):
            print("   [!!] нет сборки %s — сначала build.py" % m["mod"]); continue

        if m["menu_key"]:
            install = INSTALL_WITH_MENU.format(mod=m["mod"], group=m["group"])
            uninstall = UNINSTALL_WITH_MENU
            languages = langs
        else:
            install = INSTALL_PLAIN.format(mod=m["mod"])
            uninstall = UNINSTALL_PLAIN
            languages = "  None needed - this mod adds no text to the game.\n"

        uninstall = UNINSTALL_OVERRIDE.get(m["mod"], uninstall).format(
            mod=m["mod"], group=m["group"])

        # список соседей БЕЗ самого себя - иначе мод числится среди «остальных»
        others = [x["title"].replace("W3EE Redux - ", "")
                  for x in MODS if x["mod"] != m["mod"]]
        others = ", ".join(others[:-1]) + " and " + others[-1]

        body = BODIES.get(m["mod"])
        if body is None:
            print("   [!!] пропускаю %s — нет текста README в BODIES" % m["mod"])
            continue
        readme = body.format(ver=VER) + COMMON_TAIL.format(
            install=install, uninstall=uninstall, languages=languages,
            others=others, tested=TESTED, ver=VER)

        zpath = os.path.join(OUT, "%s %s.zip" % (m["title"], VER))
        n = 0
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for base, _d, files in os.walk(root):
                for fn in files:
                    p = os.path.join(base, fn)
                    z.write(p, os.path.relpath(p, root))
                    n += 1
            z.writestr("README.txt", readme.replace("\n", "\r\n"))
        print("   %-24s %7d Б  файлов %d" % (os.path.basename(zpath),
                                             os.path.getsize(zpath), n + 1))

    print()
    print("   папка:", OUT)


main()
